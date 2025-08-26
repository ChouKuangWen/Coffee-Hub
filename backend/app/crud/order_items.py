# backend/app/crud/order_items.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.order_items import OrderItems

async def get_order_item(db: AsyncSession, order_item_id: int):
    result = await db.execute(
        select(OrderItems)
        .options(
            selectinload(OrderItems.product),   # 預先載入 product
            selectinload(OrderItems.order)      # 預先載入 order
        )
        .where(OrderItems.order_item_id == order_item_id)
    )
    return result.scalars().first()


async def get_all_order_items(db: AsyncSession):
    result = await db.execute(
        select(OrderItems)
        .options(
            selectinload(OrderItems.product),
            selectinload(OrderItems.order)
        )
    )
    return result.scalars().all()

async def create_order_item(db: AsyncSession, order_item_data):
    new_item = OrderItems(**order_item_data.dict())
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

async def update_order_item_info(db: AsyncSession, existing_item, order_item_data):
    for field, value in order_item_data.dict(exclude_unset=True).items():
        setattr(existing_item, field, value)
    await db.commit()
    await db.refresh(existing_item)
    return existing_item

async def delete_order_item(db: AsyncSession, existing_item):
    await db.delete(existing_item)
    await db.commit()
    return existing_item
