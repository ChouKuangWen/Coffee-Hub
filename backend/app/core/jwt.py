from datetime import datetime, timedelta, timezone
import uuid
from jose import JWTError, jwt
from fastapi import HTTPException, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.jwt_blacklist import JWTBlacklist
from app.models.refresh_token import RefreshToken

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def credentials_exception():
    return HTTPException(status_code=401, detail="憑證無效、過期或已撤銷，請重新登入",
                         headers={"WWW-Authenticate": "Bearer"})


def decode_token(token: str, token_type: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],
                             options={"require_exp": True, "require_sub": True, "require_jti": True})
        if (payload.get("token_type") != token_type or int(payload["sub"]) <= 0
                or not isinstance(payload.get("version"), int) or isinstance(payload["version"], bool)
                or payload["version"] < 0 or not isinstance(payload.get("sid"), str) or not payload["sid"]):
            raise credentials_exception()
        return payload
    except (JWTError, ValueError, TypeError, KeyError):
        raise credentials_exception()


async def is_jti_blacklisted(db: AsyncSession, jti: str) -> bool:
    result = await db.execute(select(JWTBlacklist.id).where(JWTBlacklist.jti == jti))
    return result.first() is not None


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    jti = str(uuid.uuid4())
    payload = dict(data)
    payload.update(sub=str(data.get("user_id")), jti=jti, token_type="access",
                   sid=data.get("session_id"), version=data.get("token_version", 0),
                   exp=datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)))
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM), jti


async def verify_session(db: AsyncSession, payload: dict):
    result = await db.execute(select(RefreshToken).where(
        RefreshToken.jti == payload["sid"], RefreshToken.user_id == int(payload["sub"]),
        RefreshToken.is_revoked.is_(False)))
    session = result.scalars().first()
    if not session or session.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise credentials_exception()
    return session


async def verify_access_token(token: str, db: AsyncSession, request: Request = None) -> dict:
    payload = decode_token(token, "access")
    if payload.get("role_id") not in (1, 2, 3) or await is_jti_blacklisted(db, payload["jti"]):
        raise credentials_exception()
    await verify_session(db, payload)
    return payload


async def create_refresh_token(user_id: str, db: AsyncSession, token_version: int = 0,
                               session_id: str | None = None):
    sid = session_id or str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token = jwt.encode({"sub": str(user_id), "exp": expires, "jti": sid, "sid": sid,
                        "version": token_version, "token_type": "refresh"}, SECRET_KEY, algorithm=ALGORITHM)
    db.add(RefreshToken(user_id=int(user_id), token=token, jti=sid, expires_at=expires))
    return token


async def verify_refresh_token(token: str, db: AsyncSession) -> dict:
    payload = decode_token(token, "refresh")
    if payload["jti"] != payload["sid"]:
        raise credentials_exception()
    session = await verify_session(db, payload)
    if session.token != token:
        raise credentials_exception()
    return payload


async def revoke_all_sessions(db: AsyncSession, user):
    # 與角色／狀態異動同一交易。版本遞增防止重新啟用後舊 JWT 復活。
    user.token_version += 1
    await db.execute(update(RefreshToken).where(RefreshToken.user_id == user.user_id)
                     .values(is_revoked=True))


async def revoke_tokens(db: AsyncSession, access_jti: str, refresh_jti: str):
    # sid 撤銷會讓該會話所有新舊 access（包括刷新前）一併失效，不影響其他裝置。
    await db.execute(update(RefreshToken).where(RefreshToken.jti == refresh_jti).values(is_revoked=True))
