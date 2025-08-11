from sqlalchemy import Column, Integer, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base  # 從 base.py 匯入 Base，作為 ORM 基底類別
from orders import Orders
from products import Products
class Order_items(Base):
    __tablename__ = "order_items"  #對應資料表名稱
    order_item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False, comment="訂單 ID")
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, comment="商品 ID")
    quantity = Column(Integer, nullable=False, comment="數量")
    price = Column(DECIMAL(10,2), nullable=False, comment="單價")
    order = relationship("Orders", backref="order_item")
    product = relationship("Products", backref="order_item")


