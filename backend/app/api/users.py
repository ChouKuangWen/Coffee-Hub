from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.users import UserRead, UserCreate, UserUpdate, MessageResponse
from app.core.security import hash_password
from app.core.rate_limit import limiter
from app.models.base import get_db   # 取得非同步資料庫 Session
from app.models.users import Users
from app.dependencies import get_current_user_from_cookie
from app.services.user_service import (
    service_get_all_users, service_get_user,
    service_create_user, service_update_user, service_delete_user
)

router = APIRouter()

# 取得所有使用者資料(僅 Admin 可用)
@router.get("/", response_model=List[UserRead])
@limiter.limit("30/minute")
async def read_all_users(request: Request, db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_cookie)):

    return await service_get_all_users(db, request, current_user)

# 根據 user_id 取得使用者資料 (Admin 或自己)
@router.get("/{user_id}", response_model=UserRead)
@limiter.limit("60/minute")
async def read_user(request: Request, user_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_cookie)):

    return await service_get_user(db, request, current_user, user_id)

# 新增使用者
@router.post("/", response_model=UserRead)
@limiter.limit("10/minute")
async def create_user(request: Request,
                      background_tasks: BackgroundTasks,
                      user: UserCreate,
                      db: AsyncSession = Depends(get_db),
                      current_user= Depends(get_current_user_from_cookie),):

    return await service_create_user(db, request, background_tasks, current_user, user)

# 更新使用者資料(Admin 或自己)
@router.put("/{user_id}", response_model=UserRead)
@limiter.limit("10/minute")
async def update_user(request: Request,
                      background_tasks: BackgroundTasks,
                      user_id: int,
                      user_update: UserUpdate,
                      db: AsyncSession = Depends(get_db),
                      current_user=Depends(get_current_user_from_cookie)):

    return await service_update_user(db, request, background_tasks, current_user, user_id, user_update)

# 刪除使用者 (Admin 可刪)
@router.delete("/{user_id}", response_model=MessageResponse)
@limiter.limit("5/minute")
async def delete_user(request: Request,
                      background_tasks: BackgroundTasks,
                      user_id: int,
                      user_update: UserUpdate,
                      db: AsyncSession = Depends(get_db),
                      current_user=Depends(get_current_user_from_cookie)):

    success = await service_delete_user(db, request, background_tasks, current_user, user_id)
    if not success:
        # 找不到使用者，回傳 404 錯誤
        raise HTTPException(status_code=404, detail="User not found")
    return MessageResponse(message="User deleted successfully") # 使用模型回傳
