from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app import schemas, crud
from app.core.security import get_password_hash
from app.models.base import get_db   # 取得非同步資料庫 Session

router = APIRouter()

# 取得所有使用者資料
@router.get("/", response_model=List[schemas.UserResponse])
async def read_all_users(db: AsyncSession = Depends(get_db)):
    users = await crud.user.get_all_users(db)
    return users

# 根據 user_id 取得使用者資料
@router.get("/{user_id}", response_model=schemas.UserResponse)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud.user.get_user_by_id(db, user_id)
    if not user:
        # 找不到使用者，回傳 404 錯誤
        raise HTTPException(status_code=404, detail="User not found")
    return user

# 新增使用者，密碼會先被 hash
@router.post("/", response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # 先將明文密碼做雜湊處理
    hashed_pw = get_password_hash(user.password)
    user.password = hashed_pw
    new_user = await crud.user.create_user(db, user)
    return new_user

# 更新使用者資料
@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(user_id: int, user_update: schemas.UserUpdate, db: AsyncSession = Depends(get_db)):
    updated_user = await crud.user.update_user(db, user_id, user_update)
    if not updated_user:
        # 找不到使用者，回傳 404 錯誤
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

# 刪除使用者
@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    success = await crud.user.delete_user(db, user_id)
    if not success:
        # 找不到使用者，回傳 404 錯誤
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
