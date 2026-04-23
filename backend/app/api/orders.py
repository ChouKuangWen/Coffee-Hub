# app/api/orders.py
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.dependencies import get_current_user_from_cookie
from app.models.users import Users

from app.schemas.orders import (
    OrderCreate,
    OrderUpdateStatus,
    OrderRead,
    OrderListResponse,
    OrderMessageResponse
)

from app.services.order_service import (
    get_admin_orders_service,
    get_seller_orders_service,
    get_customer_orders_service,
    create_order_service,
    update_order_status_service,
    delete_order_service
)

from app.crud.orders import get_order
from app.core.rate_limit import limiter

router = APIRouter()

# 序列化工具：把 ORM 轉成 Pydantic
def serialize_order(order):
    return OrderRead.model_validate(order)

# CREATE ORDER
@router.post("/", response_model=OrderRead)
@limiter.limit("5/minute")
async def create_new_order(
    request: Request,
    background_tasks: BackgroundTasks,
    order: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    db_order = await create_order_service(
        db, request, background_tasks, current_user, order
    )
    return serialize_order(db_order)

# 買家獲取訂單 (指定 User ID)
@router.get("/user/{user_id}", response_model=OrderListResponse)
@limiter.limit("30/minute")
async def read_user_orders(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    orders = await get_customer_orders_service(db, user_id, current_user)
    return {
        "items": [serialize_order(order) for order in orders],
        "total": len(orders)
    }

# 賣家獲取訂單
@router.get("/seller", response_model=OrderListResponse)
@limiter.limit("30/minute")
async def read_seller_orders(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    orders = await get_seller_orders_service(db, current_user)
    return {
        "items": [serialize_order(order) for order in orders],
        "total": len(orders)
    }

# 管理員獲取全部訂單
@router.get("/all", response_model=OrderListResponse)
@limiter.limit("30/minute")
async def read_all_orders(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    orders = await get_admin_orders_service(db, current_user)
    return {
        "items": [serialize_order(order) for order in orders],
        "total": len(orders)
    }

# 獲取單個訂單
@router.get("/{order_id}", response_model=OrderRead)
@limiter.limit("30/minute")
async def read_order(
    request: Request,
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    order = await get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    return serialize_order(order)

# 更新
@router.patch("/{order_id}/status", response_model=OrderRead)
@limiter.limit("20/minute")
async def update_status(
    request: Request,
    background_tasks: BackgroundTasks,
    order_id: int,
    status_update: OrderUpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    updated_order = await update_order_status_service(
        db, request, background_tasks, current_user, order_id, status_update
    )
    return serialize_order(updated_order)

# 刪除
@router.delete("/{order_id}", response_model=OrderMessageResponse)
@limiter.limit("10/minute")
async def delete_order(
    request: Request,
    background_tasks: BackgroundTasks,
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    return await delete_order_service(
        db, request, background_tasks, current_user, order_id
    )
