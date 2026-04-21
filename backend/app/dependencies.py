# app/dependencies.py
from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie, Request
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

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Users:
    """
    非同步依賴注入函式，用於驗證 JWT 並獲取當前使用者。
    - 驗證 access token 的有效性。
    - 根據 token 中的使用者 ID 從資料庫中非同步查詢使用者。
    """
    payload = await verify_access_token(token, db, request=request)
    # 如果 token 驗證失敗，payload 會是 None
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 無效或過期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print("Payload:", payload)
    
    # 獲取 token 中的使用者 ID
    user_id = payload.get("sub")
    role_id = payload.get("role_id")  # 從 token 拿 role_id
    jti = payload.get("jti")
    role_name = payload.get("role")
    print()
    print("role_id from token:", role_id)
    print()
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
    request.state.user_id = int(user_id)
    user.role_id = role_id  #  把 token 裡的 role_id 覆寫給 user
    return user

async def get_current_user_from_cookie(
    request: Request,
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db)
) -> Users:
    """
    從 HttpOnly Cookie 讀取 access_token 並取得當前使用者
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="尚未登入",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 驗證 token
    payload = await verify_access_token(access_token, db, request=request)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 無效或過期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    role_id = payload.get("role_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 格式錯誤或無效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查詢使用者資料
    result = await db.execute(select(Users).where(Users.user_id == int(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="使用者不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.user_id = user.user_id
    # 將 token 內的 role_id 覆寫給 user
    user.role_id = role_id
    print("顯示" + access_token, payload)
    return user

async def get_current_user_from_cookie_optional(
    request: Request,
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db)
) -> Optional[Users]:
    """
    從 HttpOnly Cookie 讀取 access_token 並取得當前使用者 (不強制登入)
    - 驗證成功：回傳 Users 物件
    - 驗證失敗/未登入：回傳 None
    """
    if not access_token:
        return None

    try:
        # 1. 驗證 token
        payload = await verify_access_token(access_token, db, request=request)
        if not payload:
            return None

        user_id = payload.get("sub")
        role_id = payload.get("role_id")
        if not user_id:
            return None

        # 2. 查詢資料庫
        result = await db.execute(select(Users).where(Users.user_id == int(user_id)))
        user = result.scalars().first()
        if not user:
            return None

        # 3. 覆寫 role_id 並回傳
        user.role_id = role_id
        return user
        
    except Exception:
        # 遇到任何解析錯誤，一律當作未登入處理
        return None


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
        print("Checking permission: current_user.role_id =", current_user.role_id, "allowed_roles =", allowed_roles)
        if current_user.role_id not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"只有 '{allowed_roles}' 才能執行此操作"
            )
        return current_user
    return role_checker