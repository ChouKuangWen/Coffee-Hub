# backend/app/api/products.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.products import ProductCreate, ProductRead, ProductUpdate
from app.crud.products import get_all_products, get_product, create_new_product, update_product_information, delete_one_product
from app.models.base import get_db   # 取得非同步資料庫 Session
from app.dependencies import get_db, has_permission

#router = APIRouter(prefix="/products", tags=["Products"])

router = APIRouter()

# 取得所有商品 (所有角色皆有該權限)
@router.get("/", response_model=List[ProductRead])
async def read_all_products(db: AsyncSession = Depends(get_db)):
    return await get_all_products(db)

# 取得單一商品（所有角色皆有該權限）
"""所有具有預設值的參數（例如 db: AsyncSession = Depends(get_db)）都必須放在沒有預設值的參數之後。"""
@router.get("/{product_id}", response_model=ProductRead)
async def read_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await get_product(db, product_id)
    if not product:
        raise HTTPException(ststus_code=400, deta="商品不存在")
    return product

# 新增商品（管理員、賣家有權限）
@router.post("/", response_model=ProductRead, dependencies=[Depends(has_permission([1,2]))])
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    return await create_new_product(db, product)

# 更新商品（管理員、賣家有權限）
@router.patch("/{product_id}", response_model=ProductRead, dependencies=[Depends(has_permission([1,2]))])
async def update_product(product_id: int, product: ProductUpdate, db: AsyncSession = Depends(get_db)):
    updated = await update_product_information(db, product_id, product)
    if not updated:
        raise HTTPException(status_code=404, detail="商品不存在")
    return await updated

# 刪除商品（Admin / Seller）
@router.delete("/{product_id}", response_model=ProductRead, dependencies=[Depends(has_permission([1,2]))])
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_one_product(db, product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="商品不存在")
    return deleted