from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status
from config import settings  # 用來取得 SECRET_KEY、過期時間等設定
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select           # 引入 select
import uuid # 產生唯一識別碼
from app.models.jwt_blacklist import JWTBlacklist
from app.models.used_jwt import UsedJWT  #  加入 UsedJWT 模型
from app.models.refresh_token import RefreshToken

# 加解密參數
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


# 查詢 jti 是否在黑名單中
async def is_jti_blacklisted(db: AsyncSession, jti: str) -> bool:
    result = await db.execute(select(JWTBlacklist).where(JWTBlacklist.jti == jti))
    return result.scalars().first() is not None

# 查詢 jti 是否為已使用（一次性 token）
async def is_jti_used(db: AsyncSession, jti: str) -> bool:
    result = await db.execute(select(UsedJWT).where(UsedJWT.jti == jti))
    return result.scalars().first() is not None

# 簽發 JWT Token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    jti_value = str(uuid.uuid4()) # 生成一個唯一的 UUID 作為 jti
    to_encode.update({"exp": expire, "jti": jti_value})  # 加入過期時間與 jti
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM),  jti_value  # jwt.encode() 加密並簽名資料 建立JWT

# 驗證 Token，檢查 jti 是否已撤銷（黑名單或已使用）
async def verify_access_token(token: str, db: AsyncSession) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # sub是JWT標準欄位， Subject（主體）
        jti: str = payload.get("jti") # 獲取 jti

        if username is None or jti is None: # 檢查 username 和 jti 是否都存在
            raise credentials_exception()

        # 檢查是否在黑名單（如登出）且是否為一次性 token 且已使用
        if await is_jti_blacklisted(db, jti) or await is_jti_used(db, jti):
            raise credentials_exception()
        return {"username": username, "jti": jti} # 回傳包含 username 和 jti 的字典

    except JWTError:
        raise credentials_exception()

# 建立 Refresh Token（並寫入資料庫）
async def create_refresh_token(user_id: str, db: AsyncSession):
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)  # 設定過期時間
    jti = str(uuid.uuid4())  # 產生唯一的 jti（JWT ID）
    to_encode = {"sub": user_id, "exp": expire, "jti": jti} # 建立 payload主體
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # 將 refresh token 存入資料庫
    db.add(RefreshToken(
        user_id=user_id,
        token=token,
        jti=jti,
        issued_at=datetime.now(timezone.utc),
        expires_at=expire
    ))
    await db.commit()

    # 回傳 token 給前端
    return token

# 驗證 Refresh Token（檢查是否存在、未撤銷、未過期）
async def verify_refresh_token(token: str, db: AsyncSession) -> dict:
    try:
        # 解碼 JWT，提取 payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # 主體（使用者 ID）
        jti: str = payload.get("jti")       # JWT ID

        # 基本欄位檢查
        if username is None or jti is None:
            raise credentials_exception()

        # 查詢資料庫中是否存在該筆 token 且尚未撤銷
        # 使用 select 和 where 進行非同步查詢
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.jti == jti,
                RefreshToken.token == token,
                RefreshToken.is_revoked == False
            )
        )
        db_token = result.scalars().first()


        # 若資料不存在或已過期，視為無效
        if not db_token or db_token.expires_at < datetime.now(timezone.utc):
            raise credentials_exception()

        # 回傳解碼後資訊
        return {"username": username, "jti": jti}

    except JWTError:
        # 若解碼失敗或 token 不合法，回傳未授權錯誤
        raise credentials_exception()


# 登出：將 Access Token 加入黑名單、Refresh Token 設為撤銷
async def revoke_tokens(db: AsyncSession, access_jti: str, refresh_jti: str):
    # 計算 access token 的過期時間（將 jti 加入黑名單）
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    db.add(JWTBlacklist(jti=access_jti, expires_at=expires_at))

    # 查詢對應的 refresh token，設為撤銷（is_revoked = True）
    result = await db.execute(select(RefreshToken).where(RefreshToken.jti == refresh_jti))
    db_token = result.scalars().first()
    if db_token:
        db_token.is_revoked = True

    # 提交變更
    await db.commit()

# 自訂錯誤
def credentials_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無法驗證使用者身份",
        headers={"WWW-Authenticate": "Bearer"},
    )














