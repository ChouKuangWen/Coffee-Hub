#app/schemas/cart.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

# --- 基礎商品資訊 (用於回傳時嵌套在購物車內) ---
class ProductSimpleRead(BaseModel):
    product_id: int
    name: str
    main_image: Optional[str] = None
    price: Decimal
    stock: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

# --- 1. 加入購物車時的輸入規範 ---
class CartItemCreate(BaseModel):
    product_id: int = Field(..., description="要加入的商品 ID")
    quantity: int = Field(1, ge=1, description="加入數量，必須大於等於 1")

# --- 2. 更新購物車數量時的輸入規範 ---
class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, description="更新後的數量，必須大於等於 1")

# --- 3. 讀取購物車時的輸出規範 ---
class CartItemRead(BaseModel):
    cart_item_id: int
    user_id: int
    product_id: int
    quantity: int
    created_at: datetime
    updated_at: datetime

    # 這裡最關鍵！嵌套商品資訊，前端就不用再自己去查 product 資料表
    product: ProductSimpleRead

    model_config = ConfigDict(from_attributes=True) # 允許從 SQLAlchemy物件轉換為 Pydantic

# 為了讓 API 回傳結構一致
class CartResponse(BaseModel):
    items: List[CartItemRead]
    total: int
    model_config = ConfigDict(from_attributes=True)