# app/crud/orders.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, select, distinct
from app.models.orders import Orders
from app.models.order_items import OrderItems
from app.models.products import Products
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
    return result.scalars().all()

# 查賣家所有賣出的訂單
async def get_orders_by_seller(db: AsyncSession, seller_id: int):
    stmt = (
        select(Orders).distinct()
        .join(OrderItems, Orders.order_id == OrderItems.order_id)
        .join(Products, OrderItems.product_id == Products.product_id)
        .where(Products.owner_id == seller_id)
    )
    result = await db.execute(stmt)
    return result.scalars().unique().all()
    # 使用 unique() 確保在 Python 層級也只返回不重複的 Orders 物件

# 查全部訂單（管理員用）
async def get_all_orders(db: AsyncSession):
    result = await db.execute(select(Orders))
    return result.scalars().all()

# 更新訂單狀態
async def update_order_status(db: AsyncSession, existing_order, status_update: OrderUpdateStatus,):
    existing_order.status = status_update.status
    existing_order.status_updated_at = datetime.now()
    await db.commit()
    await db.refresh(existing_order)
    return existing_order

# 刪除訂單：先刪明細再刪訂單
async def delete_order(db: AsyncSession, existing_order: Orders):
    # 先刪除訂單明細
    await db.execute(
        delete(OrderItems).where(OrderItems.order_id == existing_order.order_id)
    )
    # 再刪除訂單
    await db.delete(existing_order)
    await db.commit()  # 最後 commit
    return existing_order
"""
做法特點：
1.先刪明細再刪訂單 → 避免外鍵限制報錯。
2.保留資料完整性 → 不允許 NULL。
3.加權限檢查 → 管理員 vs 自己的訂單。
"""