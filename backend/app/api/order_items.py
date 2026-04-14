# backend/app/api/order_items.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.models.base import get_db
from app.models.users import Users
from app.models.order_items import OrderItems
from app.schemas.order_items import OrderItemCreate, OrderItemRead, OrderItemReadWithDetail, OrderItemListResponse
from app.crud.order_items import (
    get_order_item,
    get_all_order_items,
    create_order_item,
    update_order_item_info,
    delete_order_item,
    get_order_items_by_order_id
)
from app.dependencies import get_current_user_from_cookie
from app.core.rate_limit import limiter

router = APIRouter()

# --- 序列化輔助函式 ---
def serialize_item_detail(item):
    """使用 model_validate 確保 nested relations (product, order) 被正確轉換"""
    return OrderItemReadWithDetail.model_validate(item)

def serialize_item_basic(item):
    """用於只需基本資訊的回傳"""
    return OrderItemRead.model_validate(item)

# 取得所有訂單項目 (管理員可用)
@router.get("/", response_model=List[OrderItemReadWithDetail])
@limiter.limit("20/minute")
async def read_all_order_items(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="只有管理員可查看所有訂單項目")
    items = await get_all_order_items(db)
    return [serialize_item_detail(i) for i in items]


# 取得單一訂單項目
@router.get("/{order_item_id}", response_model=OrderItemReadWithDetail)
@limiter.limit("60/minute")
async def read_order_item(
    request: Request,
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

    return serialize_item_detail(item)


# 新增訂單項目
@router.post("/", response_model=OrderItemRead)
@limiter.limit("10/minute")
async def create_order_item_api(
    request: Request,
    order_item: OrderItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    # 買家只能新增自己訂單的項目
    if current_user.role_id != 1 and order_item.order.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權為他人訂單新增項目")

    db_item = await create_order_item(db, order_item)
    return serialize_item_basic(db_item)


# 更新訂單項目
@router.patch("/{order_item_id}", response_model=OrderItemRead)
@limiter.limit("20/minute")
async def update_order_item_api(
    request: Request,
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
    return serialize_item_basic(updated_item)


# 刪除訂單項目
@router.delete("/{order_item_id}", response_model=OrderItemRead)
@limiter.limit("10/minute")
async def delete_order_item_api(
    request: Request,
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
    return serialize_item_basic(deleted_item)

# 獲取單一訂單的所有訂單項目列表 (前端展開明細專用)
@router.get("/by_order/{order_id}", response_model=OrderItemListResponse)
@limiter.limit("40/minute")
async def read_order_items_by_order(
    request: Request,
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user_from_cookie)
):
    # 1. 取得所有明細
    all_items = await get_order_items_by_order_id(db, order_id)
    if not all_items:
        return OrderItemListResponse(items=[], total=0)
    
    # 2. 判斷權限與過濾資料
    is_admin = current_user.role_id == 1
    # 判斷是否為買家 (下單的人可以看到全部明細)
    is_buyer = all_items[0].order.user_id == current_user.user_id if all_items[0].order else False

    # 3. 執行過濾邏輯
    if is_admin or is_buyer:
        # 管理員與買家，看這張訂單的「全部」內容
        filtered_items = all_items
    else:
        # 賣家身份：只過濾出「屬於自己」的商品明細
        # 判斷標準：item.product.owner_id 等於 current_user.user_id
        filtered_items = [
            item for item in all_items 
            if item.product and item.product.owner_id == current_user.user_id
        ]

        # 如果過濾後是空的，代表這賣家根本沒商品在這張單，噴 403
        if not filtered_items:
            raise HTTPException(status_code=403, detail="無權查看此訂單明細")

        return OrderItemListResponse(
            items=[serialize_item_detail(item) for item in filtered_items],
            total=len(filtered_items)
            )