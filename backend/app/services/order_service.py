# app/services/order_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, BackgroundTasks, HTTPException

from app.models.users import Users
from app.schemas.orders import OrderCreate, OrderUpdateStatus

from app.crud.orders import (
    create_order as crud_create_order,
    update_order_status as crud_update_status,
    delete_order as crud_delete_order,
    get_all_orders, 
    get_orders_by_seller, 
    get_orders_by_user, 
    get_order_with_items
)

from app.crud.order_items import get_order_items_by_order_id
from app.services.audit_log_service import log_action
from datetime import datetime

"""
1. 讀取邏輯 (分流與權限)
"""

# 管理員服務：獲取全系統訂單
async def get_admin_orders_service(db: AsyncSession, current_user: Users):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="僅限管理員存取")
    return await get_all_orders(db)

# 賣家服務：獲取該賣家相關訂單
async def get_seller_orders_service(db: AsyncSession, current_user: Users):
    if current_user.role_id not in [1, 2]:
        raise HTTPException(status_code=403, detail="僅限賣家或管理員存取")
    return await get_orders_by_seller(db, current_user.user_id)

# 買家服務：獲取指定用戶訂單 (具備越權檢查)
async def get_customer_orders_service(db: AsyncSession, target_user_id: int, current_user: Users):
    # 只能看自己的，除非是管理員
    if current_user.role_id != 1 and current_user.user_id != target_user_id:
        raise HTTPException(status_code=403, detail="無權查看他人訂單")
    return await get_orders_by_user(db, target_user_id)

"""
2. 寫入與異動邏輯 (含日誌)
"""
# CREATE
async def create_order_service(
    db: AsyncSession,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Users,
    order: OrderCreate
):
    order.user_id = current_user.user_id

    db_order = await crud_create_order(db, order)
    try:
        await db.commit()
        after_data = {"order_id": str(db_order.order_id), "total": str(db_order.total)}

        await log_action(
            db=db,
            background_tasks=background_tasks,
            request=request,
            user_id=current_user.user_id,
            category="ORDER",
            action="CREATE",
            target_id=str(db_order.order_id),
            after_data=after_data
        )
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="建立訂單失敗")

    return db_order


# UPDATE STATUS (含 seller)
async def update_order_status_service(
    db: AsyncSession,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Users,
    order_id: int,
    status_update: OrderUpdateStatus
):
    order = await get_order_with_items(db, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")

    if current_user.role_id != 1:

        is_buyer = order.user_id == current_user.user_id

        # 檢查訂單內是否有任何商品屬於該賣家
        is_seller = any(
            item.product.owner_id == current_user.user_id
            for item in order.order_items
        ) if order.order_items else False

        if not (is_buyer or is_seller):
            raise HTTPException(status_code=403, detail="權限不足")   

    before_data = str(order.status)
    after_data = str(status_update.status)

    if before_data == after_data:
        return order
    
    try:
        updated = await crud_update_status(db, order, status_update)
        await db.commit()

        await log_action(
            db=db,
            background_tasks=background_tasks,
            request=request,
            user_id=current_user.user_id,
            category="ORDER",
            action="UPDATE_STATUS",
            target_id=str(order_id),
            before_data={"status": before_data},
            after_data={"status": after_data}
        )
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新訂單狀態失敗")

    return updated



# DELETE (含 seller)
async def delete_order_service(
    db: AsyncSession,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Users,
    order_id: int
):
    order = await get_order_with_items(db, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")

    if current_user.role_id != 1:

        is_buyer = order.user_id == current_user.user_id

        items = await get_order_items_by_order_id(db, order_id)
        is_seller = any(
            item.product.owner_id == current_user.user_id
            for item in order.order_items
        ) if order.order_items else False

        if not (is_buyer or is_seller):
            raise HTTPException(status_code=403, detail="權限不足")

    before_data = {"order_id": str(order.order_id), "total": str(order.total), "status": str(order.status)}
    try:
        await crud_delete_order(db, order)
        await db.commit()
        await log_action(
            db=db,
            background_tasks=background_tasks,
            request=request,
            user_id=current_user.user_id,
            category="ORDER",
            action="DELETE",
            target_id=str(order_id),
            before_data=before_data
        )
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="刪除訂單失敗")

    return {"message": "訂單已刪除"}