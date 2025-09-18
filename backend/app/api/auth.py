# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.users import UserCreate, TokenResponse
from app.models.users import Users
from app.core.security import verify_password, hash_password
from app.core.jwt import create_access_token, create_refresh_token, verify_refresh_token, revoke_tokens
from app.models.base import get_db
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
from jose import jwt, JWTError
from app.core.config import settings
from sqlalchemy.orm import selectinload

router = APIRouter()
oauth2_scheme = HTTPBearer()

# 只允許 Manager = 2, Customer = 3
allowed_roles = [2, 3]

# 註冊使用者
@router.post("/register", response_model=dict)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
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
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
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
    print(f"User {user.email} role: {user.role.name}")

    # 產生 access token 和 refresh token
    # JWT payload 加入 role 名稱
    access_token, access_jti = create_access_token({
        "sub": str(user.user_id),
        "role": user.role.name  # 把角色名稱放進 token payload
    })
    refresh_token = await create_refresh_token(str(user.user_id), db)
    await db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role.name,   # 把角色直接回傳  Admin / Manager / Customer
        "role_id": user.role_id,
        "user_id": user.user_id
    }


# 使用 refresh_token 換取新的 access_token
@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token_endpoint(token: str, db: AsyncSession = Depends(get_db)):
    """
    使用 refresh token 換取新的 access token。
    - 驗證 refresh token 的有效性。
    - 產生新的 access token。
    """
    # 驗證 refresh token 並取得 payload
    payload = await verify_refresh_token(token, db)
    user_id = payload["username"]

    # 查出使用者角色
    result = await db.execute(select(Users).options(selectinload(Users.role)).where(Users.user_id == user_id))
    user = result.scalars().first()

    # 產生新的 access token
    access_token, access_jti = create_access_token({
        "sub": user_id,
        "role": user.role.name
    })

    return {
        "access_token": access_token,
        "refresh_token": token,  # refresh_token 保持不變
        "token_type": "bearer",
        "role": user.role.name,   # 加上角色
        "role_id": user.role_id,
        "user_id": user.user_id
    }


# 登出：將 access_token 和 refresh_token 加入黑名單
@router.post("/logout", response_model=dict)
async def logout(
    access_token_cred: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    登出使用者。
    - 從 Authorization Header 中獲取 access token。
    - 將 access token 加入黑名單。
    - 此處僅將 access token 加入黑名單，
      若要將 refresh token 也加入黑名單，需要額外傳入。
    """
    access_token = access_token_cred.credentials

    try:
        # 解碼 access token
        access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 無效", headers={"WWW-Authenticate": "Bearer"})

    access_jti = access_payload.get("jti")

    if not access_jti:
        raise HTTPException(status_code=400, detail="Token 無效")

     # 這裡要呼叫撤銷函式，把 token jti 加入黑名單
    await revoke_tokens(db, access_jti, None)

    return {"message": "登出成功"}
