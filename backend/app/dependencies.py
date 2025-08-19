# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession  # 非同步
from sqlalchemy.future import select           # 引入 select
from app.core.jwt import verify_access_token
from app.models.base import get_db             # 引入非同步資料庫依賴
from app.models.users import Users

"""
Token 提取設定
OAuth2PasswordBearer 是 FastAPI 提供的一種安全方案
它會自動從 Authorization Header 讀取 Bearer token
tokenUrl 參數是用來生成 swagger UI 的登入表單用 URL
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Users:
    """
    非同步依賴注入函式，用於驗證 JWT 並獲取當前使用者。
    - 驗證 access token 的有效性。
    - 根據 token 中的使用者 ID 從資料庫中非同步查詢使用者。
    """
    payload = await verify_access_token(token, db)
    # 如果 token 驗證失敗，payload 會是 None
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 無效或過期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print("Payload:", payload)
    
    # 獲取 token 中的使用者 ID
    user_id = payload.get("username")
    jti = payload.get("jti")
    role_name = payload.get("role")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 格式錯誤或無效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查詢資料庫
    result = await db.execute(select(Users).where(Users.user_id == int(user_id)))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="使用者不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# 授權相關依賴
def has_permission(required_role):
    """
    可重用函式，用於建立一個檢查指定角色的依賴。
    它會返回一個內部函式，該函式會檢查當前使用者是否具備 required_role。
    """

    # 統一處理單一角色或多角色的情況(預留)
    if isinstance(required_role, int):
        allowed_roles = [required_role]
    else:
        allowed_roles = required_role

    def role_checker(current_user: Users = Depends(get_current_user)):
        if current_user.role_id not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"只有 '{allowed_roles}' 才能執行此操作"
            )
        return current_user
    return role_checker
