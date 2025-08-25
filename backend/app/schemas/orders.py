from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import datetime

# 共同欄位基礎類別
class OrderBase(BaseModel):
    user_id: int
    status: Optional[str] = "待付款"
    total: Decimal

# 建立訂單用
class OrderCreate(OrderBase):
    pass  # 和 OrderBase 相同，不需另外欄位

# 更新訂單狀態用（可自訂）
class OrderUpdateStatus(BaseModel):
    status: str

# 回傳訂單資料用
class OrderRead(OrderBase):
    order_id: int
    created_at: datetime
    status_updated_at: datetime

    model_config = ConfigDict(from_attributes=True)  # 允許從 SQLAlchemy 物件轉換