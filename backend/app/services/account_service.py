from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, update
from app.models.users import Users
from app.models.products import Products
from app.models.seller_application import SellerApplication
from app.core.jwt import revoke_all_sessions
from app.services.audit_log_service import record_required_action


async def _lock_users(db, request, actor_id, target_id, required_role):
    # 固定順序鎖定，避免兩名管理員互相停用時鎖定順序相反。
    result = await db.execute(select(Users).where(Users.user_id.in_([actor_id, target_id]))
                              .order_by(Users.user_id).with_for_update()
                              .execution_options(populate_existing=True))
    users = {u.user_id: u for u in result.scalars().all()}
    actor = users.get(actor_id)
    if (not actor or not actor.is_active or actor.role_id != required_role
            or actor.token_version != request.state.auth_version):
        raise HTTPException(status_code=403, detail="目前帳號無權執行此操作")
    target = users.get(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="使用者不存在")
    return target


async def submit_seller_application(db, request, current_user):
    try:
        user = await _lock_users(db, request, current_user.user_id, current_user.user_id, 3)
        pending = await db.execute(select(SellerApplication).where(
            SellerApplication.user_id == user.user_id, SellerApplication.status == "pending").with_for_update())
        if pending.scalars().first():
            raise HTTPException(status_code=409, detail="已有待審申請，請勿重複送出")
        application = SellerApplication(user_id=user.user_id, status="pending")
        db.add(application)
        await db.flush()
        await db.refresh(application)
        await record_required_action(db, request, user_id=user.user_id, action="SELLER_APPLY",
                                     target_id=user.user_id,
                                     after_data={"application_id": application.application_id, "status": "pending"})
        await db.commit()
        return application
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="無法可靠保存申請及審計，未完成操作")


async def get_seller_applications(db, current_user):
    query = select(SellerApplication).order_by(SellerApplication.application_id.desc())
    if current_user.role_id != 1:
        query = query.where(SellerApplication.user_id == current_user.user_id)
    result = await db.execute(query)
    return result.scalars().all()


async def review_seller_application(db, request, current_user, application_id, decision):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="僅 Admin 可以審核 Seller 申請")
    try:
        result = await db.execute(select(SellerApplication).where(
            SellerApplication.application_id == application_id))
        application = result.scalars().first()
        if not application:
            raise HTTPException(status_code=404, detail="申請不存在")
        user = await _lock_users(db, request, current_user.user_id, application.user_id, 1)
        result = await db.execute(select(SellerApplication).where(
            SellerApplication.application_id == application_id).with_for_update()
            .execution_options(populate_existing=True))
        application = result.scalars().first()
        if application.status != "pending":
            raise HTTPException(status_code=409, detail="此申請已審核，不能重複處理")
        if not user.is_active or user.role_id != 3:
            raise HTTPException(status_code=409, detail="僅能審核啟用中的 Customer")
        application.status = decision
        application.reviewed_by = current_user.user_id
        application.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if decision == "approved":
            user.role_id = 2
            await revoke_all_sessions(db, user)
        await record_required_action(db, request, user_id=current_user.user_id, action="SELLER_REVIEW",
            target_id=user.user_id, before_data={"role_id": 3, "status": "pending"},
            after_data={"application_id": application_id, "role_id": user.role_id, "status": decision})
        await db.commit()
        return application
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="審核、撤銷或必要審計保存失敗，未完成操作")


async def set_user_activation(db, request, current_user, user_id, is_active):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="僅 Admin 可以停用或重新啟用會員")
    try:
        user = await _lock_users(db, request, current_user.user_id, user_id, 1)
        before = user.is_active
        if before == is_active:
            await db.rollback()
            return {"message": "帳號狀態未變更"}
        user.is_active = is_active
        await revoke_all_sessions(db, user)
        if not is_active:
            # 不硬刪商品、不刪圖片；重新啟用不執行任何商品上架操作。
            await db.execute(update(Products).where(Products.owner_id == user_id).values(is_active=False))
        await record_required_action(db, request, user_id=current_user.user_id,
            action="USER_ENABLE" if is_active else "USER_DISABLE", target_id=user_id,
            before_data={"is_active": before}, after_data={"is_active": is_active})
        await db.commit()
        return {"message": "會員已重新啟用，請重新登入" if is_active else "會員已停用，所有會話已撤銷"}
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="帳號、商品、撤銷或必要審計保存失敗，未完成操作")
