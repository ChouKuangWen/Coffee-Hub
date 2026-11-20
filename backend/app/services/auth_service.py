# backend/app/services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from fastapi import Request, BackgroundTasks, HTTPException
from app.models.users import Users
from app.schemas.users import UserCreate
from app.core.security import verify_password, hash_password
from app.core.jwt import create_access_token, create_refresh_token, verify_refresh_token, revoke_tokens
from app.services.audit_log_service import log_action, record_required_action

# 註冊
async def service_register_user(db: AsyncSession, request: Request, background_tasks: BackgroundTasks, user_data: UserCreate):
    if user_data.role_id != 3:
        raise HTTPException(status_code=403, detail="註冊僅能建立 Customer 帳號")
    result = await db.execute(select(Users).where(or_(
        Users.email == user_data.email, Users.username == user_data.username
    )))
    user = result.scalars().first()
    if user:
        raise HTTPException(status_code=400, detail="Email 或帳號名稱已被註冊")

    hashed_password = hash_password(user_data.password)
    new_user = Users(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        phone=user_data.phone,
        address=user_data.address,
        role_id=3
    )
    db.add(new_user)

    try:
        await db.flush()
        await log_action(
            db=db, background_tasks=background_tasks, request=request,
            user_id=new_user.user_id, category="AUTH", action="REGISTER",
            target_id=str(new_user.user_id),
            after_data={"role_id": 3},
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email 或帳號名稱已被註冊")
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="註冊失敗")


    return {"message": "註冊成功"}

# 登入與刷新都鎖定會員列，與審核／停用序列化，避免簽發出跨越撤銷時點的會話。
async def service_login_user(db: AsyncSession, request: Request, background_tasks: BackgroundTasks, username: str, password: str):
    from uuid import uuid4
    try:
        result = await db.execute(select(Users).options(selectinload(Users.role))
                                  .where(Users.email == username).with_for_update()
                                  .execution_options(populate_existing=True))
        user = result.scalars().first()
        if not user or not user.is_active or user.role_id not in (1, 2, 3) or not verify_password(password, user.password_hash):
            await record_required_action(db, request, user_id=None, action="LOGIN_FAILED",
                                         target_id=None, status="FAIL")
            await db.commit()
            raise HTTPException(status_code=401, detail="帳號或密碼錯誤，或帳號已停用")
        sid = str(uuid4())
        refresh_token = await create_refresh_token(str(user.user_id), db, user.token_version, sid)
        access_token, jti_value = create_access_token({
            "user_id": user.user_id, "username": user.email, "role_id": user.role_id,
            "token_version": user.token_version, "session_id": sid,
        })
        await record_required_action(db, request, user_id=user.user_id, action="LOGIN", target_id=user.user_id)
        await db.commit()
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="登入失敗")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer",
            "role": user.role.name, "role_id": user.role_id, "user_id": user.user_id, "jti": jti_value}


async def service_refresh_token(db: AsyncSession, request: Request, background_tasks: BackgroundTasks, refresh_token: str):
    try:
        payload = await verify_refresh_token(refresh_token, db)
        result = await db.execute(select(Users).options(selectinload(Users.role))
                                  .where(Users.user_id == int(payload["sub"])).with_for_update()
                                  .execution_options(populate_existing=True))
        user = result.scalars().first()
        if not user or not user.is_active or payload["version"] != user.token_version:
            raise HTTPException(status_code=401, detail="會話已撤銷或帳號已停用")
        # 取得會員鎖後再以 current read 檢查會話，避免登出與更新的競爭。
        from app.models.refresh_token import RefreshToken
        result = await db.execute(select(RefreshToken).where(RefreshToken.jti == payload["sid"])
                                  .with_for_update().execution_options(populate_existing=True))
        session = result.scalars().first()
        if not session or session.is_revoked:
            raise HTTPException(status_code=401, detail="會話已撤銷")
        access_token, jti_value = create_access_token({
            "user_id": user.user_id, "username": user.email, "role_id": user.role_id,
            "token_version": user.token_version, "session_id": payload["sid"],
        })
        await record_required_action(db, request, user_id=user.user_id, action="REFRESH_TOKEN", target_id=user.user_id)
        await db.commit()
        return {"access_token": access_token, "token_type": "bearer", "role": user.role.name,
                "role_id": user.role_id, "user_id": user.user_id, "jti": jti_value}
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新憑證失敗")


async def service_logout_user(db: AsyncSession, request: Request, background_tasks: BackgroundTasks, user: Users, access_token: str):
    from app.core.jwt import decode_token
    payload = decode_token(access_token, "access")
    try:
        # 與登入／刷新／停用採相同的會員→會話鎖定順序。
        await db.execute(select(Users).where(Users.user_id == user.user_id).with_for_update())
        await revoke_tokens(db, payload["jti"], payload["sid"])
        await record_required_action(db, request, user_id=user.user_id, action="LOGOUT", target_id=user.user_id)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="登出失敗")
    return {"message": "登出成功"}
