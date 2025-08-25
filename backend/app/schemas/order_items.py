from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from app.schemas.products import ProductRead
from app.schemas.orders import OrderRead


# 共用基礎欄位
class OrderItemBase(BaseModel):
    order_id: int
    product_id: int
    quantity: int
    price: Decimal

# 建立時用
class OrderItemCreate(OrderItemBase):
    pass

# 讀取資料時使用
class OrderItemRead(OrderItemBase):
    order_item_id: int
    subtotal: Decimal  # 自動計算的小計

    class Config:
        orm_mode = True

# 產品詳細資訊
class OrderItemReadWithDetail(OrderItemRead):
    product: Optional[ProductRead]
    order: Optional[OrderRead]