# backend/app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, BackgroundTasks, HTTPException
from app.crud.users import (
    get_all_users, get_user_by_id,
    create_user_db, update_user_crud, delete_user_crud
)
from app.schemas.users import UserCreate, UserUpdate
from app.core.security import hash_password
from app.services.audit_log_service import log_action
from app.core.sanitizer import sanitize_user_input
from app.models.users import Users

# 取得所有使用者
async def service_get_all_users(db: AsyncSession, request: Request, current_user: Users):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="只有 Admin 可以查看所有使用者")
    return await get_all_users(db)

# 取得單一使用者
async def service_get_user(db: AsyncSession, request: Request, current_user: Users, user_id: int):
    if current_user.role_id != 1 and current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="無權限查看此使用者")
    return await get_user_by_id(db, user_id)

# 建立使用者
async def service_create_user(
    db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
    current_user: Users, user: UserCreate
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="只有 Admin 可以建立使用者")
    # [安全] 在 Service 層做淨化與密碼雜湊
    user.username = sanitize_user_input(user.username)
    user.address = sanitize_user_input(user.address)
    user.password = hash_password(user.password)

    # 呼叫 CRUD 建立使用者
    new_user = await create_user_db(db, user)

    # [交易控制] 主交易 commit
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="建立使用者失敗")

    # [審計日誌] log_action 容錯，不影響主交易
    try:
        await log_action(
            db=db, background_tasks=background_tasks, request=request,
            user_id=current_user.user_id, category="USER", action="CREATE",
            target_id=str(new_user.user_id),
            after_data={"username": new_user.username, "email": new_user.email},
            request_id=getattr(request.state, "request_id", None)
        )
    except Exception as e:
        print(f"[WARN] log_action failed: {e}")

    return await get_user_by_id(db, new_user.user_id)

# 更新使用者
async def service_update_user(
    db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
    current_user: Users, user_id: int, user_update: UserUpdate
):
    if current_user.role_id != 1 and current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="無權限修改此使用者")

    # 先取得更新前的資料
    before_data = await get_user_by_id(db, user_id)
    if not before_data:
        return None

    # [安全] 在 Service 層做淨化
    if user_update.username:
        user_update.username = sanitize_user_input(user_update.username)
    if user_update.address:
        user_update.address = sanitize_user_input(user_update.address)

    # 呼叫 CRUD 更新
    updated_user = await update_user_crud(db, user_id, user_update)

    # [交易控制] 主交易 commit
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新使用者失敗")

    # [審計日誌] log_action 容錯
    try:
        await log_action(
            db=db, background_tasks=background_tasks, request=request,
            user_id=current_user.user_id, category="USER", action="UPDATE",
            target_id=str(user_id),
            before_data={"username": before_data.username, "email": before_data.email},
            after_data={"username": updated_user.username, "email": updated_user.email},
            request_id=getattr(request.state, "request_id", None)
        )
    except Exception as e:
        print(f"[WARN] log_action failed: {e}")

    return await get_user_by_id(db, user_id)

# 刪除使用者
async def service_delete_user(
    db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
    current_user: Users, user_id: int
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="只有 Admin 可以刪除使用者")
    # 先取得刪除前的資料
    before_data = await get_user_by_id(db, user_id)
    if not before_data:
        return False

    # 呼叫 CRUD 刪除
    await delete_user_crud(db, user_id)

    # [交易控制] 主交易 commit
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="刪除使用者失敗")

    # [審計日誌] log_action 容錯
    try:
        await log_action(
            db=db, background_tasks=background_tasks, request=request,
            user_id=current_user.user_id, category="USER", action="DELETE",
            target_id=str(user_id),
            before_data={"username": before_data.username, "email": before_data.email},
            request_id=getattr(request.state, "request_id", None)
        )
    except Exception as e:
        print(f"[WARN] log_action failed: {e}")

    return True