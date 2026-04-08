from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing import Optional, List
from decimal import Decimal
from app.schemas.products import ProductRead
from app.schemas.orders import OrderRead


# 共用基礎欄位
class OrderItemBase(BaseModel):
    order_id: int
    product_id: Optional[int] = None
    quantity: int = Field(..., gt=0, description="購買數量")
    price: Decimal = Field(..., ge=0, description="下單時單價")

# 建立時用
class OrderItemCreate(OrderItemBase):
    pass

# 讀取資料時使用
class OrderItemRead(OrderItemBase):
    order_item_id: int

    # 使用 V2 的計算欄位，自動算出小計
    @computed_field
    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity

    model_config = ConfigDict(from_attributes=True)

# 產品詳細資訊
class OrderItemReadWithDetail(OrderItemRead):
    product: Optional[ProductRead] = None
    order: Optional[OrderRead] = None

# 列表回應模型 (讓 Swagger 顯示 {items, total})
class OrderItemListResponse(BaseModel):
    items: List[OrderItemReadWithDetail]
    total: int
    
    model_config = ConfigDict(from_attributes=True)