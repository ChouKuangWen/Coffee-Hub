# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession  # 非同步
from sqlalchemy.future import select           # 引入 select
from app.core.jwt import verify_access_token
from app.models.base import get_db             # 引入非同步資料庫依賴
from app.models.users import Users

# 處理 Token 的提取
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Users:
    """
    非同步依賴注入函式，用於驗證 JWT 並獲取當前使用者。
    - 驗證 access token 的有效性。
    - 根據 token 中的使用者 ID 從資料庫中非同步查詢使用者。
    """
    payload = await verify_access_token(token, db)

    # 獲取 token 中的使用者 ID
    user_id = payload.get("username")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 格式錯誤或無效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查詢資料庫
    result = await db.execute(select(Users).where(Users.id == int(user_id)))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="使用者不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# 授權相關依賴
def has_permission(required_role: str):
    """
    可重用函式，用於建立一個檢查指定角色的依賴。
    它會返回一個內部函式，該函式會檢查當前使用者是否具備 required_role。
    """
    def role_checker(current_user: Users = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"只有 '{required_role}' 才能執行此操作"
            )
        return current_user
    return role_checker
