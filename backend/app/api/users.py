from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.users import UserRead, UserCreate, UserUpdate
from app.crud.users  import get_all_users, get_user_by_id, create_user_db, update_user_crud, delete_user_crud
from app.core.security import hash_password
from app.core.rate_limit import limiter
from app.models.base import get_db   # 取得非同步資料庫 Session
from app.dependencies import has_permission, get_current_user, get_current_user_from_cookie

router = APIRouter()

# 取得所有使用者資料(僅 Admin 可用)
@router.get("/", response_model=List[UserRead])
@limiter.limit("30/minute")
async def read_all_users(request: Request, db: AsyncSession = Depends(get_db),
    current_user=Depends(has_permission(1))):  # 1 = Admin
    users = await get_all_users(db)
    return users

# 根據 user_id 取得使用者資料 (Admin 或自己)
@router.get("/{user_id}", response_model=UserRead)
@limiter.limit("60/minute")
async def read_user(request: Request, user_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_cookie)):

    if current_user.role_id != 1 and current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="無權限查看此使用者")

    user = await get_user_by_id(db, user_id)
    if not user:
        # 找不到使用者，回傳 404 錯誤
        raise HTTPException(status_code=404, detail="User not found")
    return user

# 新增使用者，密碼會先被 hash
@router.post("/", response_model=UserRead)
@limiter.limit("10/minute")
async def create_user(request: Request, user: UserCreate, db: AsyncSession = Depends(get_db),
    current_user=Depends(has_permission(1))):
    # 先將明文密碼做雜湊處理
    hashed_pw = hash_password(user.password)
    user.password = hashed_pw
    new_user = await create_user_db(db, user)
    return new_user

# 更新使用者資料(Admin 或自己)
@router.put("/{user_id}", response_model=UserRead)
@limiter.limit("10/minute")
async def update_user(request: Request, user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_cookie)):

    if current_user.role_id != 1 and current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="無權限修改此使用者")

    updated_user = await update_user_crud(db, user_id, user_update)
    if not updated_user:
        # 找不到使用者，回傳 404 錯誤
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

# 刪除使用者 (Admin 可刪)
@router.delete("/{user_id}")
@limiter.limit("5/minute")
async def delete_user(request: Request, user_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(has_permission(1))):

    success = await delete_user_crud(db, user_id)
    if not success:
        # 找不到使用者，回傳 404 錯誤
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
