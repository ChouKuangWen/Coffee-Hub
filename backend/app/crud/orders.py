# app/crud/orders.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.orders import Orders
from app.schemas.orders import OrderCreate, OrderUpdateStatus
from datetime import datetime

# 新增訂單
async def create_order(db: AsyncSession, odrer: OrderCreate):
    new_order = Orders(**odrer.dict())
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    return new_order

# 查詢單筆訂單
async def get_order(db: AsyncSession, order_id: int):
    result = await db.execute(select(Orders).where(Orders.order_id == order_id))
    return result.scalars().first()

# 查詢單一會員的所有訂單
async def get_orders_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(Orders).where(Orders.user_id == user_id))
    return result.scalars().first()

# 更新訂單狀態
async def update_order_status(db: AsyncSession, order_id: int, status_update: OrderUpdateStatus,):
    existing_order = get_order(db, order_id)
    if not existing_order:
        return None
    existing_order.status = status_update.status
    existing_order.status_updated_at = datetime.now()
    await db.commit()
    await db.refresh(existing_order)
    return existing_order

# 刪除訂單
async def delete_order(db: AsyncSession, order_id: int):
    existing_order = await get_order(db, order_id)
    if not existing_order:
        return None
    await db.delete(existing_order)
    await db.commit()
    return existing_order
    
    