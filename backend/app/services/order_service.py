# app/services/order_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, BackgroundTasks, HTTPException

from app.models.users import Users
from app.schemas.orders import OrderCreate, OrderUpdateStatus

from app.crud.orders import (
    create_order as crud_create_order,
    get_order,
    update_order_status as crud_update_status,
    delete_order as crud_delete_order
)

from app.crud.order_items import get_order_items_by_order_id
from app.services.audit_log_service import log_action


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
    await db.commit()

    await log_action(
        db=db,
        background_tasks=background_tasks,
        request=request,
        user_id=current_user.user_id,
        category="ORDER",
        action="CREATE",
        target_id=str(db_order.order_id),
        after_data={"total": str(db_order.total)},
    )

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
    order = await get_order(db, order_id)

    if not order:
        raise HTTPException(status_code=404)

    if current_user.role_id != 1:

        is_buyer = order.user_id == current_user.user_id

        items = await get_order_items_by_order_id(db, order_id)
        is_seller = any(
            item.product.owner_id == current_user.user_id
            for item in items
        ) if items else False

        if not (is_buyer or is_seller):
            raise HTTPException(status_code=403)

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
    )

    return updated



# DELETE (含 seller)
async def delete_order_service(
    db: AsyncSession,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Users,
    order_id: int
):
    order = await get_order(db, order_id)

    if not order:
        raise HTTPException(status_code=404)

    if current_user.role_id != 1:

        is_buyer = order.user_id == current_user.user_id

        items = await get_order_items_by_order_id(db, order_id)
        is_seller = any(
            item.product.owner_id == current_user.user_id
            for item in items
        ) if items else False

        if not (is_buyer or is_seller):
            raise HTTPException(status_code=403)

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
    )

    return {"message": "訂單已刪除"}