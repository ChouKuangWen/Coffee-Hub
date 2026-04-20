# app/crud/audit_log.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate

async def create_audit_log(db: AsyncSession, obj_in: AuditLogCreate) -> AuditLog:
    """
    建立 Audit Log（非同步版本）
    """
    # 1. 建立 ORM 物件
    db_obj = AuditLog(**obj_in.model_dump())
    # 2. 加入 session
    db.add(db_obj)
    # 3. commit（非同步）
    await db.commit()
    # 4. refresh（拿 DB 實際資料，例如 id）
    await db.refresh(db_obj)
    return db_obj