from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from base import Base  # 依你的專案路徑調整

class UsedJWT(Base):
    __tablename__ = "used_jwts"
    
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(255), unique=True, nullable=False, comment="JWT 的唯一識別碼")
    created_at = Column(DateTime, default=datetime.utcnow, comment="加入黑名單的時間")