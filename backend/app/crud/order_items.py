# backend/app/crud/order_items.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
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
    await db.flush()
    await db.refresh(new_item)
    return new_item

async def update_order_item_info(db: AsyncSession, existing_item, order_item_data):
    for field, value in order_item_data.dict(exclude_unset=True).items():
        setattr(existing_item, field, value)
    await db.flush()
    await db.refresh(existing_item)
    return existing_item

async def delete_order_item(db: AsyncSession, existing_item):
    await db.delete(existing_item)
    await db.flush()
    return existing_item

# 根據 order_id 獲取所有訂單明細
async def get_order_items_by_order_id(db: AsyncSession, order_id: int):
    """
    根據訂單 ID 查詢所有相關的訂單項目。
    """
    result = await db.execute(
        select(OrderItems)
        .where(OrderItems.order_id == order_id)
        # 由於前端只需要 OrderItemRead 的基本資訊，可以省略 selectinload，
        # 但為了確保數據完整性，這裡保持載入 product 資訊 (如果 OrderItemReadWithDetail 需要)。
        .options(
            selectinload(OrderItems.order),
            selectinload(OrderItems.product)
        )
    )
    return result.scalars().all()
