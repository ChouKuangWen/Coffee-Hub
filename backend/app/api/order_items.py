# backend/app/api/order_items.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.models.base import get_db
from app.models.users import Users
from app.models.order_items import OrderItems
from app.schemas.order_items import OrderItemCreate, OrderItemRead, OrderItemReadWithDetail
from app.crud.order_items import (
    get_order_item,
    get_all_order_items,
    create_order_item,
    update_order_item_info,
    delete_order_item
)
from app.dependencies import get_current_user

router = APIRouter()


# 取得所有訂單項目 (管理員可用)
@router.get("/", response_model=List[OrderItemReadWithDetail])
async def read_all_order_items(
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="只有管理員可查看所有訂單項目")
    return await get_all_order_items(db)


# 取得單一訂單項目
@router.get("/{order_item_id}", response_model=OrderItemReadWithDetail)
async def read_order_item(
    order_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    item = await get_order_item(db, order_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="訂單項目不存在")

    # 權限檢查
    if current_user.role_id != 1 \
       and item.order.user_id != current_user.user_id \
       and item.product.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權查看此訂單項目")

    return item


# 新增訂單項目
@router.post("/", response_model=OrderItemRead)
async def create_order_item_api(
    order_item: OrderItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    # 買家只能新增自己訂單的項目
    if current_user.role_id != 1 and order_item.order.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權為他人訂單新增項目")

    return await create_order_item(db, order_item)


# 更新訂單項目
@router.patch("/{order_item_id}", response_model=OrderItemRead)
async def update_order_item_api(
    order_item_id: int,
    order_item_data: OrderItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    existing_item = await get_order_item(db, order_item_id)
    if not existing_item:
        raise HTTPException(status_code=404, detail="訂單項目不存在")

    # 權限檢查
    if current_user.role_id != 1 \
       and existing_item.order.user_id != current_user.user_id \
       and existing_item.product.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權修改此訂單項目")

    updated_item = await update_order_item_info(db, existing_item, order_item_data)
    return updated_item


# 刪除訂單項目
@router.delete("/{order_item_id}", response_model=OrderItemRead)
async def delete_order_item_api(
    order_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    existing_item = await get_order_item(db, order_item_id)
    if not existing_item:
        raise HTTPException(status_code=404, detail="訂單項目不存在")

    # 權限檢查
    if current_user.role_id != 1 \
       and existing_item.order.user_id != current_user.user_id \
       and existing_item.product.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權刪除此訂單項目")

    deleted_item = await delete_order_item(db, existing_item)
    return deleted_item
