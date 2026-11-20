# backend/app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import Request, BackgroundTasks, HTTPException
from app.crud.users import (
    get_all_users, get_user_by_id,
    create_user_db, update_user_crud
)
from app.schemas.users import UserCreate, UserUpdate
from app.core.security import hash_password
from app.services.audit_log_service import log_action, record_sensitive_read
from app.core.sanitizer import sanitize_user_input
from app.models.users import Users

# 取得所有使用者
async def service_get_all_users(db: AsyncSession, request: Request, current_user: Users):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="只有 Admin 可以查看所有使用者")
    users = await get_all_users(db)
    await record_sensitive_read(db, request, current_user, "USER", metadata={"result_count":len(users)})
    return users

# 取得單一使用者
async def service_get_user(db: AsyncSession, request: Request, current_user: Users, user_id: int):
    if current_user.role_id != 1 and current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="無權限查看此使用者")
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    if current_user.role_id == 1 and current_user.user_id != user_id:
        await record_sensitive_read(db, request, current_user, "USER", user_id)
    return user

# 建立使用者
async def service_create_user(
    db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
    current_user: Users, user: UserCreate
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="只有 Admin 可以建立使用者")
    if user.role_id != 3:
        raise HTTPException(status_code=403, detail="一般新增僅能建立 Customer；Seller 須經核准流程")
    # [安全] 在 Service 層做淨化與密碼雜湊
    user.username = sanitize_user_input(user.username)
    user.address = sanitize_user_input(user.address)
    user.password = hash_password(user.password)

    # 呼叫 CRUD 建立使用者
    # [交易控制] 主交易 commit
    try:
        new_user = await create_user_db(db, user)
        await log_action(
            db=db, background_tasks=background_tasks, request=request,
            user_id=current_user.user_id, category="USER", action="CREATE",
            target_id=str(new_user.user_id),
            after_data={"role_id": 3},
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email 或帳號名稱已被使用")
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="建立使用者失敗")


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
        raise HTTPException(status_code=404, detail="使用者不存在")

    changed_fields = set(user_update.model_fields_set)
    if not changed_fields <= {"username", "email", "phone", "address"}:
        raise HTTPException(status_code=403, detail="角色及帳號狀態不可透過個資更新變更")

    # [安全] 在 Service 層做淨化
    if "username" in changed_fields:
        user_update.username = sanitize_user_input(user_update.username)
        if not user_update.username.strip():
            raise HTTPException(status_code=422, detail="帳號名稱不可為空白")
    if "address" in changed_fields:
        user_update.address = sanitize_user_input(user_update.address)

    # [交易控制] 主交易 commit
    try:
        updated_user = await update_user_crud(db, user_id, user_update)
        await log_action(
            db=db, background_tasks=background_tasks, request=request,
            user_id=current_user.user_id, category="ACCOUNT" if current_user.role_id == 1 else "USER", action="UPDATE",
            target_id=str(user_id),
            after_data={"changed_fields": sorted(changed_fields)},
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email 或帳號名稱已被使用")
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新使用者失敗")


    return await get_user_by_id(db, user_id)

# 舊 DELETE 入口保留相容性，但業務效果為停用，絕不硬刪。
async def service_delete_user(db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
                              current_user: Users, user_id: int):
    from app.services.account_service import set_user_activation
    return await set_user_activation(db, request, current_user, user_id, False)
