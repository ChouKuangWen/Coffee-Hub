#app/api/cart.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from typing import List
from sqlalchemy.orm import selectinload
from app.models.base import get_db
from app.models.cart_item import CartItem
from app.models.products import Products
from app.schemas.cart import CartItemCreate, CartItemRead, CartItemUpdate
from app.dependencies import get_current_user_from_cookie
from app.core.rate_limit import limiter

router = APIRouter()

# 1. 取得購物車清單
@router.get("", response_model=List[CartItemRead])
@limiter.limit("30/minute")
async def read_cart(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """
    取得目前登入使用者的購物車：
    - 自動過濾掉已下架的商品。
    - 使用 joinedload 確保 product 資訊一併回傳（由 Model 關聯或在此實作）。
    """
    # 這裡使用 join 確保只抓到已上架商品
    query = (
        select(CartItem)
        .options(selectinload(CartItem.product))
        .join(Products)
        .where(
            CartItem.user_id == current_user.user_id,
            Products.is_active == True
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

# 2. 加入購物車 (包含 Upsert 邏輯)
@router.post("", response_model=CartItemRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def add_to_cart(
    request: Request,
    item_in: CartItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    # A. 檢查商品狀態與庫存
    product_query = select(Products).where(Products.product_id == item_in.product_id)
    product_result = await db.execute(product_query)
    product = product_result.scalar_one_or_none()

    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="商品已下架或不存在")
    
    if item_in.quantity > product.stock:
        raise HTTPException(status_code=400, detail=f"庫存不足，僅剩 {product.stock} 件")

    # B. 檢查是否已存在於購物車
    existing_query = select(CartItem).where(
        CartItem.user_id == current_user.user_id,
        CartItem.product_id == item_in.product_id
    )
    existing_result = await db.execute(existing_query)
    existing_item = existing_result.scalar_one_or_none()

    target_id = None

    if existing_item:
        # 累加數量並校驗
        new_qty = existing_item.quantity + item_in.quantity
        if new_qty > product.stock:
            raise HTTPException(status_code=400, detail="加上購物車現有數量後超過庫存上限")
        
        existing_item.quantity = new_qty
        await db.commit()
    else:
        # C. 新增項目
        new_cart_item = CartItem(
            user_id=current_user.user_id,
            product_id=item_in.product_id,
            quantity=item_in.quantity
        )
        db.add(new_cart_item)
        await db.commit()
        await db.refresh(new_cart_item)
        target_id = new_cart_item.cart_item_id

    # 核心修正：重新查詢包含關聯資料的 CartItem 以符合 CartItemRead Schema
    final_query = (
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.cart_item_id == target_id)
    )
    final_result = await db.execute(final_query)
    return final_result.scalar_one()


# 3. 更新購物車數量
@router.patch("/{cart_item_id}", response_model=CartItemRead)
@limiter.limit("30/minute")
async def update_cart_item(
    request: Request,
    cart_item_id: int,
    item_update: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    # 查找該使用者的特定購物車項
    query = select(CartItem).where(
        CartItem.cart_item_id == cart_item_id,
        CartItem.user_id == current_user.user_id
    )
    result = await db.execute(query)
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=404, detail="購物車項目不存在")

    # 檢查商品庫存 (透過關聯 lazy="joined" 或額外查詢)
    # 這裡示範直接透過 cart_item.product 存取 (前提是 Model 設定正確)
    product_query = select(Products).where(Products.product_id == cart_item.product_id)
    p_result = await db.execute(product_query)
    product = p_result.scalar_one()

    if item_update.quantity > product.stock:
        raise HTTPException(status_code=400, detail="修改數量超過庫存")

    cart_item.quantity = item_update.quantity
    await db.commit()
    final_query = (
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.cart_item_id == cart_item_id)
    )
    final_result = await db.execute(final_query)
    return final_result.scalar_one()

# 4. 刪除購物車品項
@router.delete("/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_cart_item(
    request: Request,
    cart_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    query = delete(CartItem).where(
        CartItem.cart_item_id == cart_item_id,
        CartItem.user_id == current_user.user_id
    )
    result = await db.execute(query)
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="項目不存在")
    
    await db.commit()
    return None