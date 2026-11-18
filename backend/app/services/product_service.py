from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, BackgroundTasks, HTTPException, status
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import lazyload
from app.models.products import Products
from app.models.users import Users
from app.schemas.products import ProductCreate, ProductUpdate
from app.crud.products import (
    get_all_products as crud_get_all_products,
    get_product as crud_get_product,
    create_new_product as crud_create_new_product,
    update_product_information as crud_update_product_information,
    delete_one_product as crud_delete_one_product
)
from app.services.audit_log_service import record_required_action
from app.core.sanitizer import sanitize_user_input
from app.services.image_service import image_urls, synchronize_product_images


async def _lock_active_actor(db, request, current_user, owner_id=None, activating=False):
    owner_id = owner_id if owner_id is not None else current_user.user_id
    result = await db.execute(select(Users).where(Users.user_id.in_([current_user.user_id, owner_id]))
                              .order_by(Users.user_id).with_for_update()
                              .execution_options(populate_existing=True))
    users = {user.user_id: user for user in result.scalars().all()}
    actor = users.get(current_user.user_id)
    if (not actor or not actor.is_active or actor.role_id not in (1, 2)
            or actor.token_version != request.state.auth_version):
        raise HTTPException(status_code=403, detail="帳號已停用或權限已變更")
    owner = users.get(owner_id)
    if activating and (not owner or not owner.is_active):
        raise HTTPException(status_code=409, detail="商品擁有者已停用，不可上架")

# 前台公開查詢
async def get_public_products_service(db: AsyncSession, page: int, limit: int,
                                      category: Optional[str], country: Optional[str],
                                      roast_level: Optional[str], sort_by_sales: bool):
    skip = (page - 1) * limit
    products, total = await crud_get_all_products(
        db, owner_id=None, category=category, country=country,
        roast_level=roast_level, is_active=True,
        sort_by_sales=sort_by_sales, skip=skip, limit=limit
    )
    return products, total


# 後台 Dashboard 查詢
async def get_dashboard_products_service(db: AsyncSession, current_user: Users, page=1, limit=20):
    if current_user.role_id not in (1, 2):
        raise HTTPException(status_code=403, detail="僅限 Admin 或 Seller")
    filter_id = None if current_user.role_id == 1 else current_user.user_id
    products, total = await crud_get_all_products(db, owner_id=filter_id, is_active=None,
                                                skip=(page - 1) * limit, limit=limit)
    return products, total


# 取得單一商品（含權限檢查）
async def get_product_service(db: AsyncSession, product_id: int, current_user: Optional[Users] = None):
    product = await crud_get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    # 如果商品是公開的，所有人都能看
    if product.is_active:
        return product
    # 如果商品已下架，只有管理員或擁有者能看
    # 此時 current_user 可能是 None
    if current_user and (current_user.role_id == 1 or product.owner_id == current_user.user_id):
        return product
    # 3. 其他情況一律拒絕
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="該商品目前不對外公開")


def _product_state(product):
    return {"name": product.name, "price": str(product.price),
            "stock": product.stock, "is_active": product.is_active}


async def _locked_product(db, request, current_user, product_id, activating=False):
    existing = await crud_get_product(db, product_id)
    if not existing:
        raise HTTPException(status_code=404, detail="商品不存在")
    await _lock_active_actor(db, request, current_user, existing.owner_id, activating)
    result = await db.execute(select(Products).options(lazyload(Products.owner))
                              .where(Products.product_id == product_id).with_for_update()
                              .execution_options(populate_existing=True))
    existing = result.scalar_one()
    if current_user.role_id != 1 and existing.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="您無權管理此商品")
    return existing


async def create_product_service(db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
                                 current_user: Users, product_in: ProductCreate):
    try:
        await _lock_active_actor(db, request, current_user, activating=product_in.is_active)
        if product_in.description:
            product_in.description = sanitize_user_input(product_in.description)
        if product_in.flavor_tags:
            product_in.flavor_tags = sanitize_user_input(product_in.flavor_tags)
        product = await crud_create_new_product(db, product_in, current_user.user_id)
        await synchronize_product_images(db, request, current_user, product, set(), [None, []])
        await record_required_action(db, request, user_id=current_user.user_id, category="PRODUCT",
                                     target_type="PRODUCT", action="CREATE", target_id=product.product_id,
                                     after_data=_product_state(product))
        await db.commit()
        return await crud_get_product(db, product.product_id)
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="建立商品失敗")


async def update_product_service(db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
                                 current_user: Users, product_id: int, product_in: ProductUpdate):
    try:
        existing = await _locked_product(db, request, current_user, product_id, product_in.is_active is True)
        before = _product_state(existing)
        before_urls = image_urls(existing)
        before_layout = [existing.main_image, list(existing.sub_images or [])]
        if product_in.description:
            product_in.description = sanitize_user_input(product_in.description)
        if product_in.flavor_tags:
            product_in.flavor_tags = sanitize_user_input(product_in.flavor_tags)
        updated = await crud_update_product_information(db, product_in, existing)
        await synchronize_product_images(db, request, current_user, updated, before_urls, before_layout)
        await record_required_action(db, request, user_id=current_user.user_id, category="PRODUCT",
                                     target_type="PRODUCT", action="UPDATE", target_id=product_id,
                                     before_data=before, after_data=_product_state(updated))
        await db.commit()
        return await crud_get_product(db, product_id)
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新商品失敗")


async def delete_product_service(db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
                                 current_user: Users, product_id: int):
    try:
        existing = await _locked_product(db, request, current_user, product_id)
        before = _product_state(existing)
        await crud_delete_one_product(db, existing)
        await record_required_action(db, request, user_id=current_user.user_id, category="PRODUCT",
                                     target_type="PRODUCT", action="DEACTIVATE", target_id=product_id,
                                     before_data=before, after_data=_product_state(existing))
        await db.commit()
        return {"message": "商品已下架"}
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="下架商品失敗")
