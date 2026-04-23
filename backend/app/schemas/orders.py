from pydantic import BaseModel, ConfigDict, computed_field
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
class OrderCreate(OrderBase):
    user_id: Optional[int] = None # 建立時可選，路由會從 current_user 帶入

# 更新訂單狀態用（可自訂）
class OrderUpdateStatus(BaseModel):
    status: OrderStatus # 強制驗證傳入的值

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

class OrderMessageResponse(BaseModel):
    message: str