from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.models.base import Base


class OrderCancellation(Base):
    __tablename__ = "order_cancellations"
    cancellation_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False, index=True)
    requested_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    reason = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False, default="pending", server_default="pending")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    reviewed_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(String(500), nullable=True)
