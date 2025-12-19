# backend/app/api/products.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.products import ProductCreate, ProductRead, ProductUpdate
from app.crud.products import get_all_products, get_product, create_new_product, update_product_information, delete_one_product
from app.models.base import get_db   # 取得非同步資料庫 Session
from app.dependencies import get_current_user_from_cookie, get_current_user, has_permission

router = APIRouter()

# 取得所有商品 (所有角色皆有該權限)
@router.get("", response_model=List[ProductRead])
async def read_all_products(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    # 邏輯判斷：
    # 如果是管理員 (1)，filter_id 為 None (代表不篩選，看全部)
    # 如果是賣家 (2) 或其他，filter_id 為自己的 ID (只看自己的商品)
    filter_id = None if current_user.role_id == 1 else current_user.user_id
    
    # 呼叫 CRUD 並傳入過濾 ID
    return await get_all_products(db, owner_id=filter_id)

# 取得單一商品（所有角色皆有該權限）
"""所有具有預設值的參數（例如 db: AsyncSession = Depends(get_db)）都必須放在沒有預設值的參數之後。"""
@router.get("/{product_id}", response_model=ProductRead)
async def read_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=400, deta="商品不存在")
    return product

# 新增商品（管理員、賣家有權限）
@router.post("/", response_model=ProductRead, dependencies=[Depends(has_permission([1,2]))])
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_cookie)):
     # 賣家新增商品時自動設定 owner_id
    if product.owner_id is None:
        product.owner_id = current_user.user_id

    return await create_new_product(db, product)

# 更新商品（管理員、賣家有權限）
@router.patch("/{product_id}", response_model=ProductRead, dependencies=[Depends(has_permission([1,2]))])
async def update_product(
    product_id: int,
    product: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_cookie)  # 取得目前登入者
    ):
    # 先取得商品
    existing_product = await get_product(db, product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # 檢查權限：賣家只能更新自己商品
    if current_user.role_id == 2 and existing_product.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="沒有權限操作此商品")

    updated = await update_product_information(db, product, existing_product)
    return  updated

# 刪除商品（Admin / Seller）
@router.delete("/{product_id}", response_model=ProductRead, dependencies=[Depends(has_permission([1,2]))])
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_cookie)
    ):
    existing_product = await get_product(db, product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # 檢查權限
    if current_user.role_id == 2 and existing_product.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="沒有權限操作此商品")

    deleted = await delete_one_product(db, existing_product)
    return deleted