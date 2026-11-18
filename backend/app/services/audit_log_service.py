# app/services/audit_log_service.py
from fastapi import BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.audit_log import AuditLogCreate
from app.crud.audit_log import create_audit_log
from app.models.audit_log import AuditLog


async def record_required_action(db: AsyncSession, request: Request, *, user_id: int,
                                 action: str, target_id: int | None, before_data=None, after_data=None,
                                 status="SUCCESS", category="ACCOUNT", target_type="USER"):
    """必要審計與主變更同一交易；不 commit、不吞例外、不排背景任務。"""
    db.add(AuditLog(
        user_id=user_id, category=category, action=action, target_type=target_type,
        target_id=str(target_id) if target_id is not None else None, status=status, before_data=before_data,
        after_data=after_data, request_id=getattr(request.state, "request_id", None),
    ))
    await db.flush()


async def log_action(
    db: AsyncSession,
    background_tasks: BackgroundTasks,
    request: Request,
    *,
    user_id: int,
    category: str,
    action: str,
    target_id: str | None = None,
    before_data: dict | None = None,
    after_data: dict | None = None,
):
    """
    Audit Log Service

    功能：
    - 統一管理「審計紀錄（Audit Log）」的建立邏輯
    - 組裝 log 資料（誰做了什麼事）
    - 使用 BackgroundTasks 非同步寫入 DB（避免拖慢 API）

    使用時機：
    - 建立訂單
    - 修改資料
    - 刪除資料
    - 權限變更
    """

    # 取得 request 資訊（可用於追蹤）
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # 組裝 schema
    log_data = AuditLogCreate(
        user_id=user_id,
        category=category,
        action=action,
        target_type=category,  # 或自己定義（例如 "ORDER"）
        target_id=target_id,
        status="SUCCESS",
        before_data=before_data,
        after_data=after_data,
        request_id=getattr(request.state, "request_id", None),
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # 丟到背景任務（不阻塞 API）
    background_tasks.add_task(create_audit_log, db, log_data)
