# app/api/orders.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import get_db
from app.schemas.orders import OrderCreate, OrderRead, OrderUpdateStatus, OrderListResponse, OrderMessageResponse, STATUS_LABEL
from app.crud.orders import create_order, get_order, get_orders_by_user, update_order_status, delete_order, get_all_orders, get_orders_by_seller
from app.crud.order_items import get_order_items_by_order_id
from typing import List
from app.dependencies import get_current_user_from_cookie
from app.models.users import Users
from app.core.rate_limit import limiter

def serialize_order(order):
    """
    使用 model_validate 自動處理 SQLAlchemy ORM 物件，
    這會保留所有透過 joinedload 載入的關聯資料。
    """
    return OrderRead.model_validate(order)

router = APIRouter()

# 新增訂單
@router.post("/", response_model=OrderRead)
@limiter.limit("5/minute")
async def create_new_order(
    request: Request,
    order: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
    ):
    # 會員只能新增自己的訂單
    order.user_id = current_user.user_id
    db_order = await create_order(db, order)
    return serialize_order(db_order)

# 查全部訂單 (Admin / Seller)
@router.get("/list", response_model=OrderListResponse)
@limiter.limit("30/minute")
async def read_all_orders(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    if current_user.role_id == 1:
        # 管理員 -> 全部訂單
        orders = await get_all_orders(db)
    elif current_user.role_id == 2:
        # 賣家 -> 自己賣出的訂單
        orders = await get_orders_by_seller(db, current_user.user_id)
    else:
        raise HTTPException(status_code=403, detail="無權查看其他會員訂單")

    # 直接回傳，FastAPI 會根據 response_model 自動處理剩餘的序列化
    return OrderListResponse(
        items=[serialize_order(order) for order in orders],
        total=len(orders)
    )
    
# 查會員的所有訂單 (Customer 只能查自己)
@router.get("/user/{user_id}", response_model=OrderListResponse)
@limiter.limit("30/minute")
async def read_orders_by_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    if current_user.role_id != 1 and user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權查看其他會員訂單")
    orders = await get_orders_by_user(db, user_id)
    return OrderListResponse(
        items=[serialize_order(order) for order in orders],
        total=len(orders)
    )

# 查單筆訂單
@router.get("/{order_id}", response_model=OrderRead)
@limiter.limit("30/minute")
async def read_order(
    request: Request,
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    db_order = await get_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    
    # 權限檢查
    if current_user.role_id != 1 and db_order.user_id != current_user.user_id and db_order.product_owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權查看此訂單")
    
    return serialize_order(db_order)

# 更新訂單狀態（管理員及賣家）
@router.patch("/{order_id}/status", response_model=OrderRead)
@limiter.limit("20/minute")
async def update_status(
    request: Request,
    order_id: int,
    status_update: OrderUpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
    ):

    existing_order = await get_order(db, order_id)
    if not existing_order:
        raise HTTPException(status_code=404, detail="訂單不存在")

    # 權限檢查：管理員或賣家可以更新
    # 假設 product_owner_id 在 order 裡面
    if current_user.role_id != 1 :
        items = await get_order_items_by_order_id(db, order_id)
        # 只要這張單沒東西，或是第一件商品的擁有者不是當前登入者，就擋掉
        if not items or items[0].product.owner_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="無權更新此訂單")

    update_order = await update_order_status(db, existing_order, status_update)
    return serialize_order(update_order)

# 刪除訂單
@router.delete("/{order_id}", response_model=OrderMessageResponse)
@limiter.limit("10/minute")
async def remove_order(
    request: Request,
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)):

    existing_order = await get_order(db, order_id)
    if not existing_order:
        raise HTTPException(status_code=404, detail="訂單不存在")

    # 權限檢查：管理員、下單買家、賣家可以刪除
    if current_user.role_id != 1 and existing_order.user_id != current_user.user_id and existing_order.product_owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權刪除此訂單")

    await delete_order(db, existing_order)
    return {"message": "訂單已成功刪除"}