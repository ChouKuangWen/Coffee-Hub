from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status
from config import settings  # 用來取得 SECRET_KEY、過期時間等設定
from sqlalchemy.orm import Session
import uuid # 產生唯一識別碼
from models.jwt_blacklist import JWTBlacklist
from models.used_jwt import UsedJWT  # ⬅️ 加入 UsedJWT 模型

# 加解密參數
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# 將 jti 加入黑名單（登出）
def add_jti_to_blacklist(db: Session, jti: str, expires_at: datetime):
    db.add(JWTBlacklist(jti=jti, expires_at=expires_at))
    db.commit()

# 查詢 jti 是否在黑名單中
def is_jti_blacklisted(db: Session, jti: str) -> bool:
    return db.query(JWTBlacklist).filter(JWTBlacklist.jti == jti).first() is not None

# 查詢 jti 是否為已使用（一次性 token）
def is_jti_used(db: Session, jti: str) -> bool:
    return db.query(UsedJWT).filter(UsedJWT.jti == jti).first() is not None

# 標記 jti 為已使用（用於一次性 token）
def mark_jti_as_used(db: Session, jti: str):
    db.add(UsedJWT(jti=jti))
    db.commit()

# 簽發 JWT Token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    jti_value = str(uuid.uuid4()) # 生成一個唯一的 UUID 作為 jti
    to_encode.update({"exp": expire, "jti": jti_value})  # 加入過期時間與 jti
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # jwt.encode() 加密並簽名資料 建立JWT

# 驗證 Token，檢查 jti 是否已撤銷（黑名單或已使用）
def verify_access_token(token: str, db: Session) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # sub是JWT標準欄位， Subject（主體）
        jti: str = payload.get("jti") # 獲取 jti

        if username is None or jti is None: # 檢查 username 和 jti 是否都存在
            raise credentials_exception()

        # 檢查是否在黑名單（如登出）
        if is_jti_blacklisted(db, jti):
            raise credentials_exception()

        # 檢查是否為一次性 token 且已使用
        if is_jti_used(db, jti):
            raise credentials_exception()
        return {"username": username, "jti": jti} # 回傳包含 username 和 jti 的字典

    except JWTError:
        raise credentials_exception()

# 自訂錯誤
def credentials_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無法驗證使用者身份",
        headers={"WWW-Authenticate": "Bearer"},
    )














