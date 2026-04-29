# app/crud/orders.py
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.orm import selectinload
from app.models.orders import Orders
from app.models.order_items import OrderItems
from app.models.products import Products
from app.schemas.orders import OrderCreate, OrderUpdateStatus
from datetime import datetime

# CREATE
async def create_order(db: AsyncSession, order: OrderCreate):
    new_order = Orders(**order.model_dump(mode="json"))
    db.add(new_order)
    await db.flush()
    return new_order

# GET SINGLE
async def get_order(db: AsyncSession, order_id: int):
    result = await db.execute(
        select(Orders).where(Orders.order_id == order_id)
    )
    return result.scalars().first()

# GET SINGLE WITH ITEMS (強化款：供 Service 權限檢查與詳情顯示使用)
async def get_order_with_items(db: AsyncSession, order_id: int):
    """
    獲取訂單並預加載明細與產品資訊
    這能解決 Service 層檢查 is_seller 時抓不到 item.product 的問題
    """
    result = await db.execute(
        select(Orders)
        .options(
            selectinload(Orders.order_items)      # 載入訂單明細
            .selectinload(OrderItems.product) # 嵌套載入產品資訊 (內含 owner_id)
        )
        .where(Orders.order_id == order_id)
    )
    return result.scalars().first()

# GET BY USER
async def get_orders_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Orders)
        .options(selectinload(Orders.order_items)) # 預加載明細，防止 Pydantic 422 報錯
        .where(Orders.user_id == user_id)
    )
    return result.scalars().all()

# GET BY SELLER
async def get_orders_by_seller(db: AsyncSession, seller_id: int):
    stmt = (
        select(Orders)
        .join(OrderItems, Orders.order_id == OrderItems.order_id)
        .join(Products, OrderItems.product_id == Products.product_id)
        .where(Products.owner_id == seller_id)
        .options(selectinload(Orders.order_items)) # 預加載明細
        .distinct()
    )
    result = await db.execute(stmt)
    return result.scalars().all()

# GET ALL (ADMIN)
async def get_all_orders(db: AsyncSession):
    result = await db.execute(select(Orders).options(selectinload(Orders.order_items)))
    return result.scalars().all()

# UPDATE STATUS
async def update_order_status(db: AsyncSession, order, new_status: str):
    order.status = new_status
    if hasattr(order, "status_updated_at"):
        order.status_updated_at = datetime.now()

    await db.flush()
    return order

# DELETE
async def delete_order(db: AsyncSession, order: Orders):
    await db.execute(
        delete(OrderItems).where(OrderItems.order_id == order.order_id)
    )
    await db.delete(order)
    await db.flush()
    return order