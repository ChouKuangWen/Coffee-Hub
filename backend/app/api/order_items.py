# backend/app/api/order_items.py
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.models.base import get_db
from app.models.users import Users
from app.schemas.order_items import OrderItemCreate, OrderItemRead, OrderItemReadWithDetail, OrderItemListResponse
from app.services.order_items_service import (
    get_authorized_order_item,
    create_order_item_service,
    update_order_item_service,
    delete_order_item_service,
    get_all_order_items_service,
    get_order_items_by_order_service
)

from app.crud.order_items import get_order_item
from app.dependencies import get_current_user_from_cookie
from app.core.rate_limit import limiter
from app.services.audit_log_service import record_sensitive_read

router = APIRouter()

# --- 序列化輔助函式 ---
def serialize_item_detail(item):
    """使用 model_validate 確保 nested relations (product, order) 被正確轉換"""
    return OrderItemReadWithDetail.model_validate(item)

def serialize_item_basic(item):
    """用於只需基本資訊的回傳"""
    return OrderItemRead.model_validate(item)

# 取得所有訂單項目 (管理員可用)
@router.get("/", response_model=List[OrderItemReadWithDetail])
@limiter.limit("20/minute")
async def read_all_order_items(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    items = await get_all_order_items_service(db, current_user)
    await record_sensitive_read(db, request, current_user, "ORDER_ITEM", metadata={"result_count":len(items)})
    return [serialize_item_detail(i) for i in items]


# 取得單一訂單項目
@router.get("/{order_item_id}", response_model=OrderItemReadWithDetail)
@limiter.limit("60/minute")
async def read_order_item(
    request: Request,
    order_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    item = await get_authorized_order_item(db, order_item_id, current_user)
    if current_user.role_id == 1:
        await record_sensitive_read(db, request, current_user, "ORDER_ITEM", order_item_id)
    return serialize_item_detail(item)

# 新增訂單項目
@router.post("/", response_model=OrderItemRead)
@limiter.limit("10/minute")
async def create_order_item_api(
    request: Request,
    order_item: OrderItemCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    db_item = await create_order_item_service(db, request, background_tasks, current_user, order_item)
    return serialize_item_basic(db_item)


# 更新訂單項目
@router.patch("/{order_item_id}", response_model=OrderItemRead)
@limiter.limit("20/minute")
async def update_order_item_api(
    request: Request,
    order_item_id: int,
    order_item_data: OrderItemCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):

    updated_item = await update_order_item_service(db, request, background_tasks, current_user, order_item_id, order_item_data)
    return serialize_item_basic(updated_item)


# 刪除訂單項目
@router.delete("/{order_item_id}", response_model=OrderItemRead)
@limiter.limit("10/minute")
async def delete_order_item_api(
    request: Request,
    order_item_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):

    deleted_item = await delete_order_item_service(db, request, background_tasks, current_user, order_item_id)
    return serialize_item_basic(deleted_item)

# 獲取單一訂單的所有訂單項目列表 (前端展開明細專用)
@router.get("/by_order/{order_id}", response_model=OrderItemListResponse)
@limiter.limit("40/minute")
async def read_order_items_by_order(
    request: Request,
    order_id: int,
    sales: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    filtered_items = await get_order_items_by_order_service(db, current_user, order_id, sales)
    if current_user.role_id == 1:
        await record_sensitive_read(db, request, current_user, "ORDER", order_id, {"result_count":len(filtered_items)})
    return OrderItemListResponse(
        items=[serialize_item_detail(item) for item in filtered_items],
        total=len(filtered_items)
    )
