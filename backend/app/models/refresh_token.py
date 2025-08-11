from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.models.base import Base  # 匯入Base基底

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    token = Column(String(length=1000), nullable=False)
    jti = Column(String(255), nullable=False, index=True)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)