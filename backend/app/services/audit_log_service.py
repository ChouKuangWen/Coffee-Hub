"""Atomic audit writes, retention and redacted Admin queries."""
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models.audit_log import AuditLog
import re

SAFE_KEYS = {"role_id", "is_active", "status", "application_id", "changed_fields",
    "price", "stock", "total", "currency", "items", "stock_deducted", "stock_returned",
    "stock_returned_at", "shipped_at", "item_ids", "shipped_item_ids", "seller_id",
    "cancellation_id", "cancellation_status", "decision", "returned", "product_id", "quantity", "order_item_id",
    "count", "layout_hash", "image_ids", "cleanup_candidates",
    "image_id", "size_bytes", "attempts", "generation", "method", "route", "status_code",
    "page", "limit", "result_count", "filter_fields", "dry_run", "deleted_count"}


def safe_data(value):
    if not isinstance(value, dict):
        return None
    def clean(key, v):
        if isinstance(v, dict):
            return safe_data(v)
        if isinstance(v, (list, tuple)):
            return [clean(key, x) for x in v[:100] if clean(key, x) is not None]
        if isinstance(v, (int, float, bool)) or v is None:
            return v
        text = str(v)
        if key in {"price", "total"} and re.fullmatch(r"\d{1,12}(\.\d{1,4})?", text):
            return text
        if key == "layout_hash" and re.fullmatch(r"[a-f0-9]{64}", text):
            return text
        if key in {"stock_returned_at", "shipped_at"} and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?", text):
            return text
        if key in {"image_id", "image_ids", "cleanup_candidates"} and re.fullmatch(r"[a-f0-9-]{36}", text):
            return text
        if key == "route" and re.fullmatch(r"/[a-z_/{\}0-9-]*|unmatched", text):
            return text
        allowed = {"SUCCESS", "FAIL", "FAILED", "DENIED", "pending", "approved", "rejected",
                   "待付款", "已付款", "待出貨", "已出貨", "已完成", "已取消", "TWD",
                   "GET", "POST", "PATCH", "PUT", "DELETE", "HEAD", "OPTIONS"}
        if key in {"changed_fields", "filter_fields"}:
            allowed |= {"username", "email", "phone", "address", "category", "action", "user_id",
                        "target_type", "target_id", "status", "request_id", "since", "until"}
        return text if text in allowed else None
    return {k: clean(k, v) for k, v in value.items() if k in SAFE_KEYS}


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def retention(category, action, at):
    # 敏感查閱三年已獲使用者核准。舊資料不猜測分類，NULL 到期日禁止清理。
    if (category in {"ACCOUNT", "ORDER", "SENSITIVE_READ", "AUDIT"} or (category == "USER" and action == "CREATE")) and action not in {"LOGIN", "LOGIN_FAILED", "REFRESH_TOKEN", "LOGOUT", "REGISTER"}:
        years, label = 3, "HIGH_RISK"
    elif category in {"PRODUCT", "IMAGE", "USER"} or action == "REGISTER":
        years, label = 1, "BUSINESS"
    elif category in {"AUTH", "SECURITY"} or action in {"LOGIN", "LOGIN_FAILED", "REFRESH_TOKEN", "LOGOUT"}:
        return "SECURITY", at + timedelta(days=90)
    else:
        return "UNCLASSIFIED", None
    try:
        expiry = at.replace(year=at.year + years)
    except ValueError:
        expiry = at.replace(year=at.year + years, day=28)
    return label, expiry


async def record_required_action(db, request, *, user_id, action, target_id, before_data=None,
                                 after_data=None, status="SUCCESS", category="ACCOUNT", target_type="USER"):
    at = now()
    label, expiry = retention(category, action, at)
    db.add(AuditLog(user_id=user_id, category=category, action=action, target_type=target_type,
        target_id=str(target_id) if target_id is not None else None, status=status,
        before_data=safe_data(before_data), after_data=safe_data(after_data),
        request_id=getattr(request.state, "request_id", None), created_at=at,
        retention_class=label, expires_at=expiry, is_held=False))
    await db.flush()


async def log_action(db, background_tasks, request, *, user_id, category, action, target_id=None,
                     before_data=None, after_data=None):
    # 同交易寫入；錯誤向上傳遞，主異動回滾後可重送，不依賴易遺失的背景任務。
    await record_required_action(db, request, user_id=user_id, category=category, action=action,
        target_type=category, target_id=target_id, before_data=before_data, after_data=after_data)


async def record_sensitive_read(db, request, actor, target_type, target_id=None, metadata=None):
    try:
        await lock_admin(db, request, actor)
        await record_required_action(db, request, user_id=actor.user_id, category="SENSITIVE_READ",
            action="READ", target_type=target_type, target_id=target_id, after_data=metadata)
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=503, detail="查閱審計暫時無法保存，請稍後重試")


async def lock_admin(db, request, actor):
    from app.models.users import Users
    current = (await db.execute(select(Users).where(Users.user_id == actor.user_id)
        .with_for_update().execution_options(populate_existing=True))).scalar_one_or_none()
    if not current or not current.is_active or current.role_id != 1 or current.token_version != request.state.auth_version:
        raise HTTPException(status_code=403, detail="Admin 權限已變更")


def public_audit(row):
    def label(value):
        return value if value and re.fullmatch(r"[A-Z_]{1,100}", value) else None
    target = row.target_id if row.target_id and re.fullmatch(r"\d{1,20}|[a-f0-9-]{36}", row.target_id) else None
    trace = row.request_id if row.request_id and re.fullmatch(r"[a-f0-9-]{36}", row.request_id) else None
    return dict(id=row.id, user_id=row.user_id, category=label(row.category), action=label(row.action),
        target_type=label(row.target_type), target_id=target, status=label(row.status),
        before_data=safe_data(row.before_data), after_data=safe_data(row.after_data),
        request_id=trace, created_at=row.created_at, retention_class=row.retention_class,
        expires_at=row.expires_at, is_held=row.is_held)


async def query_audit(db, request, actor, *, page, limit, category=None, action=None, user_id=None,
                      target_type=None, target_id=None, status=None, request_id=None, since=None, until=None):
    if since and until and since > until:
        raise HTTPException(status_code=422, detail="起始時間不得晚於結束時間")
    filters = []
    provided = []
    for key, value in dict(category=category, action=action, user_id=user_id, target_type=target_type,
                           target_id=target_id, status=status, request_id=request_id).items():
        if value is not None:
            filters.append(getattr(AuditLog, key) == value)
            provided.append(key)
    if since:
        filters.append(AuditLog.created_at >= since)
        provided.append("since")
    if until:
        filters.append(AuditLog.created_at <= until)
        provided.append("until")
    total = (await db.execute(select(func.count()).select_from(AuditLog).where(*filters))).scalar_one()
    rows = (await db.execute(select(AuditLog).where(*filters).order_by(AuditLog.id.desc())
                            .offset((page-1)*limit).limit(limit))).scalars().all()
    result = {"items": [public_audit(row) for row in rows], "total": total, "page": page, "limit": limit}
    await record_sensitive_read(db, request, actor, "AUDIT_LOG", metadata={"page":page,
        "limit":limit, "result_count":len(rows), "filter_fields":provided})
    return result


async def cleanup_audit(db, request, actor, *, dry_run=True, limit=100):
    from app.core.config import settings
    if not dry_run and not getattr(settings, "AUDIT_DELETE_ENABLED", False):
        raise HTTPException(status_code=403, detail="實際審計清理尚未啟用")
    try:
        await lock_admin(db, request, actor)
        rows = (await db.execute(select(AuditLog).where(AuditLog.is_held.is_(False),
            AuditLog.expires_at.is_not(None), AuditLog.expires_at <= now(),
            AuditLog.retention_class.in_(["HIGH_RISK", "BUSINESS", "SECURITY"]))
            .order_by(AuditLog.id).limit(limit).with_for_update()
            .execution_options(populate_existing=True))).scalars().all()
        count = len(rows)
        if not dry_run:
            for row in rows:
                await db.delete(row)
        await record_required_action(db, request, user_id=actor.user_id, category="AUDIT",
            action="RETENTION_CLEANUP", target_type="AUDIT_LOG", target_id=None,
            after_data={"dry_run":dry_run, "count":count, "deleted_count":0 if dry_run else count})
        await db.commit()
        return {"dry_run":dry_run, "candidates":count, "deleted":0 if dry_run else count}
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=503, detail="審計清理失敗，異動已回滾")
