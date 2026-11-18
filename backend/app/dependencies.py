# app/dependencies.py
from typing import Optional
from fastapi import Depends, HTTPException, Cookie, Request, status
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

async def _get_authenticated_user(request: Request, token: str, db: AsyncSession) -> Users:
    """以目前資料庫角色授權，絕不將 JWT 的角色寫回 ORM。"""
    payload = await verify_access_token(token, db, request=request)
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Token 無效或過期")

    result = await db.execute(select(Users).where(Users.user_id == user_id))
    user = result.scalars().first()
    if not user or not user.is_active or user.role_id not in (1, 2, 3):
        raise HTTPException(status_code=401, detail="使用者不存在或角色無效")
    if payload.get("role_id") != user.role_id or payload.get("version") != user.token_version:
        raise HTTPException(status_code=401, detail="角色已異動，請重新登入")
    request.state.user_id = user.user_id
    request.state.auth_version = user.token_version
    return user


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Users:
    return await _get_authenticated_user(request, token, db)


async def get_current_user_from_cookie(
    request: Request,
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db)
) -> Users:
    if not access_token:
        raise HTTPException(status_code=401, detail="尚未登入")
    return await _get_authenticated_user(request, access_token, db)


async def get_current_user_from_cookie_optional(
    request: Request,
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db)
) -> Optional[Users]:
    if not access_token:
        return None
    try:
        return await _get_authenticated_user(request, access_token, db)
    except HTTPException as exc:
        if exc.status_code == 401:
            return None
        raise


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

    def role_checker(current_user: Users = Depends(get_current_user_from_cookie)): #  修正：改用 Cookie 驗證
        if current_user.role_id not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"只有 '{allowed_roles}' 才能執行此操作"
            )
        return current_user
    return role_checker
