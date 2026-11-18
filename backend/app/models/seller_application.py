from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.models.base import Base


class SellerApplication(Base):
    __tablename__ = "seller_applications"
    application_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    reviewed_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
