from sqlalchemy import Column, Integer, String, DateTime
from app.models.base import Base  # 請確保你有初始化 Base
from datetime import datetime, timezone

class JWTBlacklist(Base):
    __tablename__ = "jwt_blacklist"
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(36), unique=True, nullable=False, comment="JWT 的 JTI")
    expires_at = Column(DateTime, nullable=False, comment="JWT 過期時間")
    created_at = Column(DateTime, default=datetime.now(timezone.utc))