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
    delete_order_item,
    get_order_items_by_order_id
)
from app.dependencies import get_current_user_from_cookie

router = APIRouter()


# 取得所有訂單項目 (管理員可用)
@router.get("/", response_model=List[OrderItemReadWithDetail])
async def read_all_order_items(
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="只有管理員可查看所有訂單項目")
    return await get_all_order_items(db)


# 取得單一訂單項目
@router.get("/{order_item_id}", response_model=OrderItemReadWithDetail)
async def read_order_item(
    order_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
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
    current_user: Users = Depends(get_current_user_from_cookie)
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
    current_user: Users = Depends(get_current_user_from_cookie)
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
    current_user: Users = Depends(get_current_user_from_cookie)
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

# 獲取單一訂單的所有訂單項目列表 (前端展開明細專用)
@router.get("/by_order/{order_id}", response_model=List[OrderItemReadWithDetail])
async def read_order_items_by_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    # 1. 取得訂單明細
    items = await get_order_items_by_order_id(db, order_id)
    
    if not items:
        # 即使沒有項目，我們也返回空列表而不是 404
        return []

    # 2. 準備權限檢查變數
    # 管理員 (role_id == 1)
    is_admin = current_user.role_id == 1

    # 買家檢查：訂單的下單者是否為當前使用者 (orders.user_id)
    # 注意：需確保 items[0].order 已被載入
    is_buyer = items[0].order.user_id == current_user.user_id if items[0].order else False

    # 賣家檢查：當前使用者是否為此訂單中「任何一個商品」的擁有者 (products.owner_id)
    # 這是最嚴謹的作法，只要有一件商品是你的，你就有權看明細
    is_seller = any(
        item.product.owner_id == current_user.user_id 
        for item in items if item.product
    )

    # 3. 權限判定邏輯
    # 如果不是管理員、也不是買家、也不是賣家，才拋出 403
    if not (is_admin or is_buyer or is_seller):
        raise HTTPException(
            status_code=403, 
            detail=f"無權查看此訂單的明細。您的使用者 ID 為 {current_user.user_id}"
        )
        
    return items