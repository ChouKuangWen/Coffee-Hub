# app/crud/orders.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.models.orders import Orders
from app.models.order_items import OrderItems
from app.models.products import Products
from app.schemas.orders import OrderCreate, OrderUpdateStatus
from datetime import datetime


async def create_order(db: AsyncSession, order: OrderCreate):
    new_order = Orders(**order.model_dump())
    db.add(new_order)
    await db.flush()
    return new_order


async def get_order(db: AsyncSession, order_id: int):
    result = await db.execute(
        select(Orders).where(Orders.order_id == order_id)
    )
    return result.scalars().first()


async def get_orders_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Orders).where(Orders.user_id == user_id)
    )
    return result.scalars().all()


async def get_orders_by_seller(db: AsyncSession, seller_id: int):
    stmt = (
        select(Orders)
        .join(OrderItems, Orders.order_id == OrderItems.order_id)
        .join(Products, OrderItems.product_id == Products.product_id)
        .where(Products.owner_id == seller_id)
        .distinct()
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_all_orders(db: AsyncSession):
    result = await db.execute(select(Orders))
    return result.scalars().all()


async def update_order_status(db: AsyncSession, order, status_update: OrderUpdateStatus):
    order.status = status_update.status
    order.status_updated_at = datetime.now()
    await db.flush()
    return order


async def delete_order(db: AsyncSession, order: Orders):
    await db.execute(
        delete(OrderItems).where(OrderItems.order_id == order.order_id)
    )
    await db.delete(order)
    await db.flush()
    return order