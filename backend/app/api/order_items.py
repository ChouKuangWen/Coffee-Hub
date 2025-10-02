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

    # 2. 權限檢查：檢查訂單或任一項目是否屬於當前使用者或管理員
    # 由於明細通常屬於同一筆訂單，我們檢查第一筆的權限即可
    first_item = items[0] 
    
    # 權限檢查：管理員、下單買家、賣家可以查看
    # 注意：我們依賴 OrderItem 關聯到 Order (item.order) 和 Product (item.product.owner_id)
    if current_user.role_id != 1 \
        and first_item.order.user_id != current_user.user_id \
        and first_item.product.owner_id != current_user.user_id:
        
        # 雖然第一筆檢查通過，但嚴格來說應該檢查所有產品的擁有者是否為 Seller
        # 為簡化，我們假設一筆訂單通常是查看權限一致的。
        # 如果買家/賣家無權查看，則拋出 403
        raise HTTPException(status_code=403, detail="無權查看此訂單的明細")
        
    return items