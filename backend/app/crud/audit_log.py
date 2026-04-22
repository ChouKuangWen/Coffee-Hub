# app/crud/audit_log.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate
from app.core.logger import audit_logger

async def create_audit_log(db: AsyncSession, obj_in: AuditLogCreate) -> AuditLog | None:
    """
    建立 Audit Log（非同步版本）

    設計重點：
    - 使用 AsyncSession
    - 發生錯誤時 rollback，避免 transaction 卡住
    - 不 raise exception（避免影響主流程）
    - 記錄錯誤到 audit_logger（方便追蹤）

    回傳：
    - 成功：AuditLog
    - 失敗：None
    """

    # 1. 建立 ORM 物件
    db_obj = AuditLog(**obj_in.model_dump())

    try:
        # 2. 加入 session
        db.add(db_obj)

        # 3. commit（非同步）
        await db.commit()

        # 4. refresh（取得 DB 實際資料，例如 id / created_at）
        await db.refresh(db_obj)

        return db_obj

    except SQLAlchemyError as e:
        # 發生 DB 錯誤時 rollback
        await db.rollback()

        # 記錄錯誤（但不影響主流程）
        audit_logger.error({
            "event": "audit_log_failed",
            "error": str(e),
            "data": obj_in.model_dump()
        })

        return None