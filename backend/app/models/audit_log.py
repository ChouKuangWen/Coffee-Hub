# app/models/audit_log.py
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, JSON, Text, func
from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    category = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="SUCCESS")
    error_message = Column(Text, nullable=True)
    before_data = Column(JSON, nullable=True)
    after_data = Column(JSON, nullable=True)
    request_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())