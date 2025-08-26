# app/api/orders.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import get_db
from app.schemas.orders import OrderCreate, OrderRead, OrderUpdateStatus
from app.crud.orders import create_order, get_order, get_orders_by_user, update_order_status, delete_order
from typing import List
from app.dependencies import has_permission, get_current_user
from app.models.users import Users

router = APIRouter()

# 新增訂單
@router.post("/", response_model=OrderRead)
async def create_new_order(
    order: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
    ):
    # 會員只能新增自己的訂單
    order.user_id = current_user.user_id
    return await create_order(db, order)

# 查詢單筆訂單
@router.get("/{order_id}", response_model=OrderRead)
async def read_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
    ):
    db_order = await get_order(db, order_id)
    
    # 如果不是管理員，檢查是不是自己的訂單
    if not db_order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    
    # 權限檢查：管理員、下單買家、賣家可以查看
    if current_user.role_id != 1 and db_order.user_id != current_user.user_id and db_order.product_owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權查看此訂單")
    return db_order

# 查詢會員的所有訂單
@router.get("/user/{user_id}", response_model=List[OrderRead]) # 因為會回傳所有資訊所以要用list
async def read_orders_by_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
    ):
    if current_user.role_id != 1 and user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權查看其他會員訂單")
    return await get_orders_by_user(db, user_id)

# 更新訂單狀態（管理員及賣家）
@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_status(
    order_id: int,
    status_update: OrderUpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
    ):

    existing_order = await get_order(db, order_id)
    if not existing_order:
        raise HTTPException(status_code=404, detail="訂單不存在")

    # 權限檢查：管理員或賣家可以更新
    # 假設 product_owner_id 在 order 裡面
    if current_user.role_id != 1 and existing_order.product_owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權更新此訂單")

    update_order = await update_order_status(db, existing_order, status_update)
    return update_order

# 刪除訂單
@router.delete("/{order_id}", response_model=OrderRead)
async def remove_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)):

    existing_order = await get_order(db, order_id)
    if not existing_order:
        raise HTTPException(status_code=404, detail="訂單不存在")

    # 權限檢查：管理員、下單買家、賣家可以刪除
    if current_user.role_id != 1 and existing_order.user_id != current_user.user_id and existing_order.product_owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權刪除此訂單")

    deleted_order = await delete_order(db, existing_order)
    return deleted_order