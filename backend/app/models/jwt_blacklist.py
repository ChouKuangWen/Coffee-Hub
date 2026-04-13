from sqlalchemy import Column, Integer, String, DateTime
from app.models.base import Base  # 請確保你有初始化 Base
from sqlalchemy.sql import func

class JWTBlacklist(Base):
    __tablename__ = "jwt_blacklist"
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(255), unique=True, nullable=False, index=True, comment="JWT 的 JTI")
    expires_at = Column(DateTime, nullable=False, comment="JWT 過期時間")
    created_at = Column(DateTime, server_default=func.now(), comment="加入黑名單時間")