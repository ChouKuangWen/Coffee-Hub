from pydantic import BaseModel, ConfigDict, computed_field, Field, field_validator
from uuid import UUID
from typing import Literal
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from enum import Enum

# 1. 強制規範狀態，Swagger 會顯示下拉選單
class OrderStatus(str, Enum):
    PENDING = "待付款"
    PAID = "已付款"
    PENDING_SHIPMENT = "待出貨"
    SHIPPED = "已出貨"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


# 共同欄位基礎類別
class OrderBase(BaseModel):
    status: OrderStatus = OrderStatus.PENDING
    total: Decimal

# 建立訂單用
class CheckoutItem(BaseModel):
    cart_item_id: int = Field(gt=0, strict=True)
    quantity: int = Field(gt=0, le=2147483647, strict=True)
    model_config = ConfigDict(extra="forbid")


class OrderCreate(BaseModel):
    checkout_key: UUID
    items: List[CheckoutItem] = Field(min_length=1, max_length=100)
    model_config = ConfigDict(extra="forbid")

    @field_validator('items')
    @classmethod
    def unique_items(cls, items):
        if len({item.cart_item_id for item in items}) != len(items):
            raise ValueError('購物車品項不可重複')
        return items

# 更新訂單狀態用（可自訂）
class OrderUpdateStatus(BaseModel):
    status: OrderStatus # 強制驗證傳入的值
    model_config = ConfigDict(extra="forbid")

# 回傳訂單資料用
class OrderRead(OrderBase):
    order_id: int
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    status_updated_at: Optional[datetime] = None

    #  新增這個：讓 Pydantic 自動產生 status_label 欄位給前端
    @computed_field
    @property
    def status_label(self) -> str:
        # STATUS_LABEL 是你上面定義的字典
        return self.status.value if isinstance(self.status, OrderStatus) else self.status
    model_config = ConfigDict(from_attributes=True)

# 2. 列表包裝，讓 Swagger 顯示 {items: [], total: 0}
class OrderListResponse(BaseModel):
    items: List[OrderRead]
    total: int


class SellerOrderRead(BaseModel):
    order_id: int
    status: OrderStatus
    status_label: str
    created_at: Optional[datetime] = None
    seller_total: Decimal
    can_ship: bool = False
    seller_shipment_status: Literal["未出貨", "已出貨"] = "未出貨"


class SellerOrderListResponse(BaseModel):
    items: List[SellerOrderRead]
    total: int

class OrderMessageResponse(BaseModel):
    message: str


class CancellationCreate(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CancellationReview(BaseModel):
    decision: Literal["approved", "rejected"]
    review_note: Optional[str] = Field(None, max_length=500)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CancellationRead(BaseModel):
    cancellation_id: int
    order_id: int
    requested_by: int
    reason: str
    status: Literal["pending", "approved", "rejected"]
    created_at: datetime
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
