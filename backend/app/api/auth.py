# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.users import UserCreate, UserRead, TokenResponse, MessageResponse
from app.models.users import Users
from app.core.security import verify_password, hash_password
from app.core.jwt import create_access_token, create_refresh_token, verify_refresh_token, revoke_tokens
from app.core.rate_limit import limiter
from app.models.base import get_db
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
from jose import jwt, JWTError
from app.core.config import settings
from sqlalchemy.orm import selectinload
from app.dependencies import get_current_user_from_cookie



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
async def register(request: Request, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    註冊新使用者。
    - 檢查電子郵件是否已被註冊。
    - 僅允許 Manager 與 Customer
    - Admin 必須手動於資料庫新增
    - 對密碼進行雜湊處理。
    - 將新使用者寫入資料庫。
    """
    # 查詢 email 是否已存在
    result = await db.execute(select(Users).where(Users.email == user_data.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(status_code=400, detail="Email 已被註冊")

    # 檢查角色是否合法
    if user_data.role_id not in allowed_roles:
        raise HTTPException(status_code=400, detail="只能選擇賣家或買家")
    
    # 密碼加密
    hashed_password = hash_password(user_data.password)

    # 建立新使用者實例
    new_user = Users(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        phone=user_data.phone,
        address=user_data.address,
        role_id=user_data.role_id
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"message": "註冊成功"}


# 使用者登入，回傳 access_token 和 refresh_token
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute") # 限制一分鐘只能登入 5 次，防止暴力破解
async def login(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    print("### Running the login route... ###") # <--- 在這裡加上這行

    """
    使用者登入，使用 OAuth2PasswordRequestForm 處理表單資料。
    - 驗證使用者帳號和密碼。
    - 產生並回傳 access token 和 refresh token。
    """
    # 根據 username (等同於 email) 查詢使用者,連帶載入使用者角色
    result = await db.execute(select(Users).options(selectinload(Users.role)).where(Users.email == form_data.username))
    user = result.scalars().first()

    # 若帳號或密碼錯誤
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 印出使用者角色到終端機
    print(f"User {user.email} role: {user.role.name} role_id: {user.role_id}")

    # 產生 access token 和 refresh token
    # JWT payload 加入 role 名稱
    access_token, access_jti = create_access_token({
        "sub": str(user.user_id),
        "username": user.email,
        "role_id": user.role_id,   # 把role_id放進 token payload
        "user_id": user.user_id
    })
    refresh_token = await create_refresh_token(str(user.user_id), db)
    await db.commit()

    #  修改：增加 HttpOnly cookie
    response.set_cookie(
    key="access_token",               # Cookie 名稱，前端 JS 不可讀
    value=access_token,               # Cookie 的值，也就是你的 JWT
    httponly=True,                    # 讓 JS 無法透過 document.cookie 讀取，減少 XSS 攻擊風險
    secure=True,                      # 只允許 HTTPS 傳輸，保護 token 在網路上不被竊取
    samesite="none",                   # 防止 CSRF 攻擊，僅允許同站請求攜帶 cookie
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Cookie 過期秒數
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return {
        #"access_token": access_token,
        #"refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role.name,   # 把角色直接回傳  Admin / Manager / Customer
        "role_id": user.role_id,
        "user_id": user.user_id
    }

# 使用 refresh_token 換取新的 access_token
@router.post("/refresh-token", response_model=TokenResponse)
@limiter.limit("10/minute") # 限制刷新頻率
async def refresh_token_endpoint(
    request: Request,
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
    
    # 驗證 refresh token 並取得 payload
    payload = await verify_refresh_token(refresh_token, db)
    user_id = payload["sub"]

    # 查出使用者角色
    result = await db.execute(select(Users).options(selectinload(Users.role)).where(Users.user_id == int(user_id)))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    # 產生新的 access token
    access_token,  = create_access_token({
        "user_id": user.user_id,
        "username": user.email,
        "role_id": user.role_id   # 把role_id放進 token payloa
    })

    #  將新的 access_token 放入 HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

 
    return {
        #"access_token": access_token,
        #"refresh_token": refresh_token,  # refresh_token 保持不變
        "token_type": "bearer",
        "role": user.role.name,   # 加上角色
        "role_id": user.role_id,
        "user_id": user.user_id
    }


# 登出：將 access_token 和 refresh_token 加入黑名單
@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db)
):
    if not access_token:
        raise HTTPException(status_code=401, detail="尚未登入")

    try:
        access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 無效")

    access_jti = access_payload.get("jti")
    if not access_jti:
        raise HTTPException(status_code=400, detail="Token 無效")

    # 將 token 加入黑名單
    await revoke_tokens(db, access_jti, None)

    # 刪除 cookie
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "登出成功"}
