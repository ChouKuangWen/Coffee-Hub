from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, lazyload
from app.models.base import get_db
from app.models.cart_item import CartItem
from app.models.products import Products
from app.models.users import Users
from app.schemas.cart import CartItemCreate, CartItemRead, CartItemUpdate, CartResponse
from app.dependencies import get_current_user_from_cookie
from app.core.rate_limit import limiter

router = APIRouter()


def _buyer(user):
    if user.role_id not in (2, 3):
        raise HTTPException(status_code=403, detail="Admin 不參與買家流程")


async def _lock_buyer(db, request, user):
    _buyer(user)
    actor = (await db.execute(select(Users).where(Users.user_id == user.user_id)
        .with_for_update().execution_options(populate_existing=True))).scalar_one()
    if not actor.is_active or actor.role_id not in (2, 3) or actor.token_version != request.state.auth_version:
        raise HTTPException(status_code=403, detail="帳號已停用或權限已變更")


async def _product(db, product_id, quantity):
    product = (await db.execute(select(Products).options(lazyload(Products.owner))
        .where(Products.product_id == product_id).with_for_update()
        .execution_options(populate_existing=True))).scalar_one_or_none()
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="商品已下架或不存在")
    if quantity > product.stock:
        raise HTTPException(status_code=409, detail="要求數量超過實際庫存")
    return product


async def _read_item(db, item_id):
    return (await db.execute(select(CartItem).options(selectinload(CartItem.product))
        .where(CartItem.cart_item_id == item_id))).scalar_one()


@router.get("", response_model=CartResponse)
@limiter.limit("30/minute")
async def read_cart(request: Request, db: AsyncSession = Depends(get_db),
                    current_user=Depends(get_current_user_from_cookie)):
    _buyer(current_user)
    result = await db.execute(select(CartItem).options(selectinload(CartItem.product))
                             .where(CartItem.user_id == current_user.user_id))
    items = result.scalars().all()
    # 保留下架品項供本人移除，但不輸出下架圖片網址。
    output = []
    for item in items:
        data = CartItemRead.model_validate(item)
        if not data.product.is_active:
            data.product.main_image = None
        output.append(data)
    return CartResponse(items=output, total=len(output))


@router.post("", response_model=CartItemRead, status_code=201)
@limiter.limit("20/minute")
async def add_to_cart(request: Request, item_in: CartItemCreate,
                      db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user_from_cookie)):
    try:
        await _lock_buyer(db, request, current_user)
        item = (await db.execute(select(CartItem).options(lazyload(CartItem.product)).where(
            CartItem.user_id == current_user.user_id, CartItem.product_id == item_in.product_id)
            .with_for_update().execution_options(populate_existing=True))).scalar_one_or_none()
        quantity = item_in.quantity + (item.quantity if item else 0)
        await _product(db, item_in.product_id, quantity)
        if item:
            item.quantity = quantity
        else:
            item = CartItem(user_id=current_user.user_id, product_id=item_in.product_id, quantity=quantity)
            db.add(item)
        await db.flush()
        item_id = item.cart_item_id
        response = CartItemRead.model_validate(await _read_item(db, item_id))
        await db.commit()
        return response
    except Exception:
        await db.rollback()
        raise


@router.patch("/{cart_item_id}", response_model=CartItemRead)
@limiter.limit("30/minute")
async def update_cart_item(request: Request, cart_item_id: int, item_update: CartItemUpdate,
                           db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user_from_cookie)):
    try:
        await _lock_buyer(db, request, current_user)
        item = (await db.execute(select(CartItem).options(lazyload(CartItem.product)).where(
            CartItem.cart_item_id == cart_item_id, CartItem.user_id == current_user.user_id)
            .with_for_update().execution_options(populate_existing=True))).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="購物車項目不存在")
        await _product(db, item.product_id, item_update.quantity)
        item.quantity = item_update.quantity
        await db.flush()
        # 仍持有買家鎖時讀取並序列化，避免轉單清車後重讀不到已成功更新的品項。
        response = CartItemRead.model_validate(await _read_item(db, cart_item_id))
        await db.commit()
        return response
    except Exception:
        await db.rollback()
        raise


@router.delete("/{cart_item_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_cart_item(request: Request, cart_item_id: int, db: AsyncSession = Depends(get_db),
                           current_user=Depends(get_current_user_from_cookie)):
    try:
        await _lock_buyer(db, request, current_user)
        item = (await db.execute(select(CartItem).options(lazyload(CartItem.product)).where(
            CartItem.cart_item_id == cart_item_id, CartItem.user_id == current_user.user_id)
            .with_for_update())).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="購物車項目不存在")
        await db.delete(item)
        await db.commit()
    except Exception:
        await db.rollback()
        raise
