# backend/app/api/products.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.products import ProductCreate, ProductRead, ProductUpdate
from app.crud.products import get_all_products, get_product, create_new_product, update_product_information, delete_one_product
from app.models.base import get_db   # 取得非同步資料庫 Session
from app.dependencies import get_current_user_from_cookie, get_current_user, has_permission
from app.core.rate_limit import limiter

router = APIRouter()

# 取得所有商品 (所有角色皆有該權限)
@router.get("", response_model=List[ProductRead])
@limiter.limit("60/minute")
async def read_all_products(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    前台公開 API：
    - 任何人（包括未登入訪客）皆可讀取。
    - 回傳所有已上架商品。
    - 受 IP 限流保護，防止惡意爬蟲。
    """
    # owner_id=None 在 CRUD 邏輯中應代表不篩選特定擁有者，即「全部公開商品」
    return await get_all_products(db, owner_id=None)

# 後台商品管理：賣家/管理者專用 (必須登入) ---
@router.get("/dashboard", response_model=List[ProductRead])
@limiter.limit("30/minute")
async def read_dashboard_products(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """
    後台管理 API：
    - 必須登入才可存取。
    - 管理員 (role_id=1): 看到系統「所有」商品。
    - 賣家 (role_id=2): 只看到「自己」的商品。
    """
    # 根據角色決定篩選邏輯
    filter_id = None if current_user.role_id == 1 else current_user.user_id
    return await get_all_products(db, owner_id=filter_id)

# 取得單一商品（所有角色皆有該權限）
"""所有具有預設值的參數（例如 db: AsyncSession = Depends(get_db)）都必須放在沒有預設值的參數之後。"""
@router.get("/{product_id}", response_model=ProductRead)
@limiter.limit("100/minute")
async def read_product(request: Request, product_id: int, db: AsyncSession = Depends(get_db)):
    product = await get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=400, deta="商品不存在")
    return product

# 新增商品（管理員、賣家有權限）
@router.post("/", response_model=ProductRead, dependencies=[Depends(has_permission([1,2]))])
@limiter.limit("10/minute")
async def create_product(
    request: Request,
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_cookie)):
     # 賣家新增商品時自動設定 owner_id
    if product.owner_id is None:
        product.owner_id = current_user.user_id

    return await create_new_product(db, product)

# 更新商品（管理員、賣家有權限）
@router.patch("/{product_id}", response_model=ProductRead, dependencies=[Depends(has_permission([1,2]))])
@limiter.limit("20/minute")
async def update_product(
    request: Request,
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
@limiter.limit("5/minute")
async def delete_product(
    request: Request,
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