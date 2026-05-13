# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.users import UserCreate, UserRead, TokenResponse, MessageResponse
from app.models.users import Users
from app.core.security import verify_password, hash_password
from app.core.jwt import create_access_token, create_refresh_token, verify_refresh_token, revoke_tokens
from app.core.rate_limit import limiter
from app.models.base import get_db
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from sqlalchemy.orm import selectinload
from app.dependencies import get_current_user_from_cookie
from app.services.auth_service import (
    service_register_user, service_login_user,
    service_refresh_token, service_logout_user
)



router = APIRouter()
oauth2_scheme = HTTPBearer()

# 只允許 Manager = 2, Customer = 3
allowed_roles = [2, 3]

#  取得目前登入使用者資訊
@router.get("/me", response_model=UserRead)
async def read_users_me(
    request: Request,
    current_user: Users = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_db)
):
    return current_user

# 註冊使用者
@router.post("/register", response_model=MessageResponse)
@limiter.limit("3/hour") # 限制一小時只能註冊 3 次，防止機器人大量註冊
async def register(request: Request,
                   background_tasks: BackgroundTasks,
                   user_data: UserCreate,
                   db: AsyncSession = Depends(get_db)):
    """
    註冊新使用者。
    - 檢查電子郵件是否已被註冊。
    - 僅允許 Manager 與 Customer
    - Admin 必須手動於資料庫新增
    - 對密碼進行雜湊處理。
    - 將新使用者寫入資料庫。
    """
    return await service_register_user(db, request, background_tasks, user_data)


# 使用者登入，回傳 access_token 和 refresh_token
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute") # 限制一分鐘只能登入 5 次，防止暴力破解
async def login(request: Request,
                background_tasks: BackgroundTasks,
                response: Response,
                form_data: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_db)):

    """
    使用者登入，使用 OAuth2PasswordRequestForm 處理表單資料。
    - 驗證使用者帳號和密碼。
    - 產生並回傳 access token 和 refresh token。
    """
    result = await service_login_user(db, request, background_tasks, form_data.username, form_data.password)
    response.set_cookie(key="access_token", value=result["access_token"], httponly=True, secure=True, samesite="none")
    response.set_cookie(key="refresh_token", value=result["refresh_token"], httponly=True, secure=True, samesite="none")
    return result

# 使用 refresh_token 換取新的 access_token
@router.post("/refresh-token", response_model=TokenResponse)
@limiter.limit("10/minute") # 限制刷新頻率
async def refresh_token_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db)):  # 從 Cookie 取得,
    """
    使用 refresh token 換取新的 access token。
    - 驗證 refresh token 的有效性。
    - 產生新的 access token。
    """
    if not refresh_token:
        raise HTTPException(status_code=401, detail="請重新登入")

    result = await service_refresh_token(db, request, background_tasks, refresh_token)

    # 把新的 access_token 寫入 HttpOnly Cookie
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return result
    


# 登出：將 access_token 和 refresh_token 加入黑名單
@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    access_token: str | None = Cookie(default=None),
    current_user: Users = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_db)
):
    if not access_token:
        raise HTTPException(status_code=401, detail="尚未登入")

    result = await service_logout_user(db, request, background_tasks, current_user, access_token)

    # 刪除 cookie
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "登出成功"}