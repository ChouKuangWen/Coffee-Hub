# app/crud/audit_log.py
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate

def create_audit_log(db: Session, obj_in: AuditLogCreate):
    """內部使用的寫入工具"""
    db_obj = AuditLog(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    return db_obj