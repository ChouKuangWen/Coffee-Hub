# api/order_items.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.order_items import OrderItemCreate, OrderItemRead, OrderItemReadWithDetail
from app.crud.order_items import (
    create_order_item, get_order_item, get_order_items_by_order,
    update_order_item, delete_order_item
)
from app.models.users import Users
from app.models.base import get_db
from app.dependencies import has_permission

router = APIRouter()


# 新增訂單明細（會員、管理員都可）
@router.post("/", response_model=OrderItemRead)
async def create_item(order_item: OrderItemCreate, db: AsyncSession = Depends(get_db),
                      current_user: Users = Depends(has_permission([1, 2]))):
    return await create_order_item(db, order_item)


# 取得單一訂單明細
@router.get("/{order_item_id}", response_model=OrderItemReadWithDetail)
async def read_item(order_item_id: int, db: AsyncSession = Depends(get_db),
                    current_user: Users = Depends(has_permission([1, 2]))):
    item = await get_order_item(db, order_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="找不到訂單明細")
    return item


# 取得某筆訂單的所有明細
@router.get("/order/{order_id}", response_model=list[OrderItemReadWithDetail])
async def read_items_by_order(order_id: int, db: AsyncSession = Depends(get_db),
                              current_user: Users = Depends(has_permission([1, 2]))):
    return await get_order_items_by_order(db, order_id)


# 更新訂單明細（部分更新）
@router.put("/{order_item_id}", response_model=OrderItemRead)
async def update_item(order_item_id: int, updates: dict, db: AsyncSession = Depends(get_db),
                      current_user: Users = Depends(has_permission([1]))):  # 只有管理員可更新
    item = await update_order_item(db, order_item_id, updates)
    if not item:
        raise HTTPException(status_code=404, detail="找不到訂單明細")
    return item


# 刪除訂單明細
@router.delete("/{order_item_id}", response_model=OrderItemRead)
async def delete_item(order_item_id: int, db: AsyncSession = Depends(get_db),
                      current_user: Users = Depends(has_permission([1]))):  # 只有管理員可刪除
    item = await delete_order_item(db, order_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="找不到訂單明細")
    return item
