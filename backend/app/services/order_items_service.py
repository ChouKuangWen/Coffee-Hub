from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, BackgroundTasks, HTTPException
from app.models.users import Users
from app.schemas.order_items import OrderItemCreate
from app.crud.order_items import (
    get_order_item,
    get_order_items_by_order_id,
    create_order_item,
    update_order_item_info,
    delete_order_item,
    get_all_order_items
)
from app.services.audit_log_service import log_action

# CREATE
async def create_order_item_service(db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
                                    current_user: Users, order_item_data: OrderItemCreate):
    # 權限檢查：只有管理員或訂單的買家能新增
    if current_user.role_id != 1 and order_item_data.order_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權新增他人訂單項目")

    db_item = await create_order_item(db, order_item_data)
    await db.commit()

    after_data = {
        "order_item_id": db_item.order_item_id,
        "order_id": db_item.order_id,
        "product_id": db_item.product_id,
        "quantity": db_item.quantity,
        "price": str(db_item.price),
        "subtotal": str(db_item.subtotal)
    }

    await log_action(db=db, background_tasks=background_tasks, request=request,
                     user_id=current_user.user_id, category="ORDER_ITEM", action="CREATE",
                     target_id=str(db_item.order_item_id),
                     after_data=after_data,
                     request_id=request.state.request_id)
    return db_item


# UPDATE
async def update_order_item_service(db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
                                    current_user: Users, order_item_id: int, order_item_data: OrderItemCreate):
    existing_item = await get_order_item(db, order_item_id)
    if not existing_item:
        raise HTTPException(status_code=404, detail="訂單項目不存在")

    # 權限檢查：只有管理員、訂單買家或商品賣家能修改
    if current_user.role_id != 1 \
       and existing_item.order.user_id != current_user.user_id \
       and existing_item.product.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權修改此訂單項目")

    before_data = {
        "quantity": existing_item.quantity,
        "price": str(existing_item.price),
        "subtotal": str(existing_item.subtotal)
    }

    updated_item = await update_order_item_info(db, existing_item, order_item_data)
    await db.commit()

    after_data = {
        "quantity": updated_item.quantity,
        "price": str(updated_item.price),
        "subtotal": str(updated_item.subtotal)
    }

    await log_action(db=db, background_tasks=background_tasks, request=request,
                     user_id=current_user.user_id, category="ORDER_ITEM", action="UPDATE",
                     target_id=str(order_item_id),
                     before_data=before_data,
                     after_data=after_data,
                     request_id=request.state.request_id)
    return updated_item


# DELETE
async def delete_order_item_service(db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
                                    current_user: Users, order_item_id: int):
    existing_item = await get_order_item(db, order_item_id)
    if not existing_item:
        raise HTTPException(status_code=404, detail="訂單項目不存在")

    # 權限檢查：只有管理員、訂單買家或商品賣家能刪除
    if current_user.role_id != 1 \
       and existing_item.order.user_id != current_user.user_id \
       and existing_item.product.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權刪除此訂單項目")

    before_data = {
        "order_item_id": existing_item.order_item_id,
        "order_id": existing_item.order_id,
        "product_id": existing_item.product_id,
        "quantity": existing_item.quantity,
        "price": str(existing_item.price),
        "subtotal": str(existing_item.subtotal)
    }

    await delete_order_item(db, existing_item)
    await db.commit()

    await log_action(db=db, background_tasks=background_tasks, request=request,
                     user_id=current_user.user_id, category="ORDER_ITEM", action="DELETE",
                     target_id=str(order_item_id),
                     before_data=before_data,
                     request_id=request.state.request_id)
    return existing_item


# READ ALL (Admin only)
async def get_all_order_items_service(db: AsyncSession, current_user: Users):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="只有管理員可查看所有訂單項目")
    return await get_all_order_items(db)


# READ BY ORDER
async def get_order_items_by_order_service(db: AsyncSession, current_user: Users, order_id: int):
    all_items = await get_order_items_by_order_id(db, order_id)
    if not all_items:
        return []

    is_admin = current_user.role_id == 1
    is_buyer = all_items[0].order.user_id == current_user.user_id if all_items[0].order else False

    if is_admin or is_buyer:
        filtered_items = all_items
    else:
        filtered_items = [item for item in all_items if item.product and item.product.owner_id == current_user.user_id]

    if not filtered_items:
        raise HTTPException(status_code=403, detail="無權查看此訂單明細")

    return filtered_items
