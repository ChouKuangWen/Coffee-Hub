# app/api/orders.py
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.dependencies import get_current_user_from_cookie
from app.models.users import Users

from app.schemas.orders import (
    OrderCreate,
    CancellationCreate, CancellationReview, CancellationRead,
    SellerOrderRead,
    SellerOrderListResponse,
    OrderUpdateStatus,
    OrderRead,
    OrderListResponse,
    OrderMessageResponse
)

from app.services.order_service import (
    get_authorized_order,
    request_cancellation, get_cancellations, review_cancellation,
    get_admin_orders_service,
    get_seller_orders_service,
    get_customer_orders_service,
    create_order_service,
    update_order_status_service,
    delete_order_service
)

from app.crud.orders import get_order
from app.core.rate_limit import limiter
from app.services.audit_log_service import record_sensitive_read

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
    if current_user.role_id == 1 and user_id != current_user.user_id:
        await record_sensitive_read(db, request, current_user, "USER_ORDERS", user_id, {"result_count":len(orders)})
    return {
        "items": [serialize_order(order) for order in orders],
        "total": len(orders)
    }

# 賣家獲取訂單
@router.get("/seller", response_model=SellerOrderListResponse)
@limiter.limit("30/minute")
async def read_seller_orders(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    orders = await get_seller_orders_service(db, current_user)
    return {"items": orders, "total": len(orders)}

# 管理員獲取全部訂單
@router.get("/all", response_model=OrderListResponse)
@limiter.limit("30/minute")
async def read_all_orders(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    orders = await get_admin_orders_service(db, current_user)
    await record_sensitive_read(db, request, current_user, "ORDER", metadata={"result_count":len(orders)})
    return {
        "items": [serialize_order(order) for order in orders],
        "total": len(orders)
    }

# 獲取單個訂單
@router.get("/{order_id}", response_model=OrderRead | SellerOrderRead)
@limiter.limit("30/minute")
async def read_order(
    request: Request,
    order_id: int,
    sales: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    order = await get_authorized_order(db, order_id, current_user, sales)
    if current_user.role_id == 1:
        await record_sensitive_read(db, request, current_user, "ORDER", order_id)
    return order

# 更新
@router.patch("/{order_id}/status", response_model=OrderRead | SellerOrderRead)
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
    return updated_order

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


@router.post("/{order_id}/cancellation-requests", response_model=CancellationRead)
@limiter.limit("10/minute")
async def create_cancellation(request: Request, order_id: int, data: CancellationCreate,
                              db: AsyncSession = Depends(get_db),
                              current_user: Users = Depends(get_current_user_from_cookie)):
    return await request_cancellation(db, request, current_user, order_id, data)


@router.get("/{order_id}/cancellation-requests", response_model=list[CancellationRead])
@limiter.limit("30/minute")
async def read_cancellations(request: Request, order_id: int, db: AsyncSession = Depends(get_db),
                             current_user: Users = Depends(get_current_user_from_cookie)):
    rows = await get_cancellations(db, current_user, order_id)
    if current_user.role_id == 1:
        await record_sensitive_read(db, request, current_user, "ORDER_CANCELLATION", order_id, {"result_count":len(rows)})
    return rows


@router.patch("/cancellation-requests/{cancellation_id}", response_model=CancellationRead)
@limiter.limit("20/minute")
async def review_cancellation_api(request: Request, cancellation_id: int, data: CancellationReview,
                                  db: AsyncSession = Depends(get_db),
                                  current_user: Users = Depends(get_current_user_from_cookie)):
    return await review_cancellation(db, request, current_user, cancellation_id, data)
