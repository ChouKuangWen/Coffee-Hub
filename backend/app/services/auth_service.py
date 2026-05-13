# backend/app/services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import Request, BackgroundTasks, HTTPException
from jose import jwt, JWTError
from app.models.users import Users
from app.schemas.users import UserCreate
from app.core.security import verify_password, hash_password
from app.core.jwt import create_access_token, create_refresh_token, verify_refresh_token, revoke_tokens
from app.core.config import settings
from app.services.audit_log_service import log_action

allowed_roles = [2, 3]  # Manager=2, Customer=3

# 註冊
async def service_register_user(db: AsyncSession, request: Request, background_tasks: BackgroundTasks, user_data: UserCreate):
    result = await db.execute(select(Users).where(Users.email == user_data.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(status_code=400, detail="Email 已被註冊")

    if user_data.role_id not in allowed_roles:
        raise HTTPException(status_code=400, detail="只能選擇賣家或買家")

    hashed_password = hash_password(user_data.password)
    new_user = Users(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        phone=user_data.phone,
        address=user_data.address,
        role_id=user_data.role_id
    )
    db.add(new_user)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="註冊失敗")

    try:
        await log_action(
            db=db, background_tasks=background_tasks, request=request,
            user_id=new_user.user_id, category="AUTH", action="REGISTER",
            target_id=str(new_user.user_id),
            after_data={"username": new_user.username, "email": new_user.email},
            request_id=getattr(request.state, "request_id", None)
        )
    except Exception as e:
        print(f"[WARN] log_action failed: {e}")

    return {"message": "註冊成功"}

# 登入
async def service_login_user(db: AsyncSession, request: Request, background_tasks: BackgroundTasks, username: str, password: str):
    result = await db.execute(select(Users).options(selectinload(Users.role)).where(Users.email == username))
    user = result.scalars().first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")

    access_token, jti_value = create_access_token({
        "sub": str(user.user_id),
        "username": user.email,
        "role_id": user.role_id,
        "user_id": user.user_id
    })
    refresh_token = await create_refresh_token(str(user.user_id), db)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="登入失敗")

    try:
        await log_action(
            db=db, background_tasks=background_tasks, request=request,
            user_id=user.user_id, category="AUTH", action="LOGIN",
            target_id=str(user.user_id),
            after_data={"role": user.role.name, "email": user.email},
            request_id=getattr(request.state, "request_id", None)
        )
    except Exception as e:
        print(f"[WARN] log_action failed: {e}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role.name,
        "role_id": user.role_id,
        "user_id": user.user_id,
        "jti": jti_value
    }

# refresh token
async def service_refresh_token(db: AsyncSession, request: Request, background_tasks: BackgroundTasks, refresh_token: str):
    payload = await verify_refresh_token(refresh_token, db)
    user_id = payload["sub"]

    result = await db.execute(select(Users).options(selectinload(Users.role)).where(Users.user_id == int(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    access_token, jti_value = create_access_token({
        "user_id": user.user_id,
        "username": user.email,
        "role_id": user.role_id
    })

    try:
        await log_action(
            db=db, background_tasks=background_tasks, request=request,
            user_id=user.user_id, category="AUTH", action="REFRESH_TOKEN",
            target_id=str(user.user_id),
            after_data={"role": user.role.name, "email": user.email},
            request_id=getattr(request.state, "request_id", None)
        )
    except Exception as e:
        print(f"[WARN] log_action failed: {e}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.name,
        "role_id": user.role_id,
        "user_id": user.user_id,
        "jti": jti_value
    }

# 登出
async def service_logout_user(db: AsyncSession, request: Request, background_tasks: BackgroundTasks, user: Users, access_token: str):
    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 無效")

    access_jti = payload.get("jti")
    if not access_jti:
        raise HTTPException(status_code=400, detail="Token 無效")

    try:
        await revoke_tokens(db, access_jti, None)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="登出失敗")

    try:
        await log_action(
            db=db, background_tasks=background_tasks, request=request,
            user_id=user.user_id, category="AUTH", action="LOGOUT",
            target_id=str(user.user_id),
            before_data={"email": user.email},
            request_id=getattr(request.state, "request_id", None)
        )
    except Exception as e:
        print(f"[WARN] log_action failed: {e}")

    return {"message": "登出成功"}
