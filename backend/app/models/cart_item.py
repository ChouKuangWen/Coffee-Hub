#app/models/cart_item.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func  # 建議使用資料庫層級的 func.now()
from app.models.base import Base

class CartItem(Base):
    __tablename__ = "cart_items"
    cart_item_id = Column(Integer, primary_key=True, autoincrement=True, comment='購物車項目 ID')
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, comment='使用者 ID')
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, comment='商品 ID')
    quantity = Column(Integer, default=1, nullable=False, comment='購買數量')
    
    # 使用 server_default 以對應你 SQL 中的 DEFAULT CURRENT_TIMESTAMP
    created_at = Column(DateTime, server_default=func.now(), comment='建立時間')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新時間')

    # --- 關聯設定 ---
    
    # 關聯到使用者 (對應 Users 類別)
    user = relationship("Users", back_populates="cart_items")
    
    # 關聯到商品 (對應 Products 類別)
    product = relationship("Products")

    # --- 約束與索引 ---
    __table_args__ = (
        # 確保同個用戶不會對同個商品產生兩筆紀錄，這是處理「重複加入」邏輯的基礎
        UniqueConstraint('user_id', 'product_id', name='unique_user_product'),
    )