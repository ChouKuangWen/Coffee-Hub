from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

# 共用欄位（給 Create、Read、Update 繼承）
class ProductBase(BaseModel):
    name: str                           # 商品名稱
    price: Decimal                      # 價格，使用 Decimal 保留精度
    stock: int                          # 庫存數量
    description: Optional[str] = None   # 商品描述，可為空

# 建立商品時使用的 schema（要送到後端）
class ProductCreate(ProductBase):
    pass

# 回傳商品資料用（包含 ID）
class ProductRead(ProductBase):
    product_id: int

    class Config:
        orm_mode = True

# 商品更新時使用（允許部分欄位）
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True

