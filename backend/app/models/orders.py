from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base  # 從 base.py 匯入 Base，作為 ORM 基底類別

class Orders(Base):
    __tablename__ = "orders"  #對應資料表名稱
    order_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True, comment="下單會員 ID")
    status = Column(String(50), nullable=False, default="待付款", index=True, comment="訂單狀態")
    total = Column(DECIMAL(10,2), nullable=False, comment="總金額")
    created_at = Column(DateTime, default=func.now(), index=True, comment="建立時間")
    status_updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="狀態變動時間")
    user = relationship("Users", back_populates="order")
