# app/schemas/audit_log.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any, Dict


class AuditLogBase(BaseModel):
    category: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    status: str = "SUCCESS"
    error_message: Optional[str] = None
    before_data: Optional[Dict[str, Any]] = None
    after_data: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogRead(AuditLogBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogCreate(AuditLogBase):
    user_id: Optional[int] = None