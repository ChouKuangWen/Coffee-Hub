from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, BackgroundTasks, HTTPException, status
from typing import Optional, Tuple, List

from app.models.users import Users
from app.schemas.products import ProductCreate, ProductUpdate
from app.crud.products import (
    get_all_products as crud_get_all_products,
    get_product as crud_get_product,
    create_new_product as crud_create_new_product,
    update_product_information as crud_update_product_information,
    delete_one_product as crud_delete_one_product
)
from app.services.audit_log_service import log_action
from app.core.sanitizer import sanitize_user_input

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
async def get_dashboard_products_service(db: AsyncSession, current_user: Users):
    filter_id = None if current_user.role_id == 1 else current_user.user_id
    products, total = await crud_get_all_products(db, owner_id=filter_id, is_active=None)
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


# 新增商品
async def create_product_service(db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
                                 current_user: Users, product_in: ProductCreate):
    # 安全淨化處理
    if product_in.description:
        product_in.description = sanitize_user_input(product_in.description)
    if product_in.flavor_tags:
        product_in.flavor_tags = sanitize_user_input(product_in.flavor_tags)

    db_product = await crud_create_new_product(db, product_in, current_user.user_id)
    await db.commit()
    after_data = {"name": db_product.name, "price": str(db_product.price)}

    await log_action(db=db, background_tasks=background_tasks, request=request,
                     user_id=current_user.user_id, category="PRODUCT", action="CREATE",
                     target_id=str(db_product.product_id),
                     after_data=after_data,
                     request_id=request.state.request_id)
    return db_product


# 更新商品
async def update_product_service(db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
                                 current_user: Users, product_id: int, product_in: ProductUpdate):
    existing = await crud_get_product(db, product_id)
    if not existing:
        raise HTTPException(status_code=404, detail="商品不存在")
    # 賣家權限檢查 (管理員 role_id=1 除外)
    if current_user.role_id != 1 and existing.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="您無權編輯此商品")

    before_data = {"name": existing.name, "price": str(existing.price)}

    # 安全淨化處理
    if product_in.description:
        product_in.description = sanitize_user_input(product_in.description)
    if product_in.flavor_tags:
        product_in.flavor_tags = sanitize_user_input(product_in.flavor_tags)

    updated = await crud_update_product_information(db, product_in, existing)
    await db.commit()
    after_data = {"name": updated.name, "price": str(updated.price)}

    await log_action(db=db, background_tasks=background_tasks, request=request,
                     user_id=current_user.user_id, category="PRODUCT", action="UPDATE",
                     target_id=str(product_id), before_data=before_data, after_data=after_data,
                     request_id=request.state.request_id)
    return updated

    
# 刪除商品
async def delete_product_service(db: AsyncSession, request: Request, background_tasks: BackgroundTasks,
                                 current_user: Users, product_id: int):
    existing = await crud_get_product(db, product_id)
    if not existing:
        raise HTTPException(status_code=404, detail="商品不存在")
    # 檢查權限
    if current_user.role_id != 1 and existing.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="您無權刪除此商品")

    before_data = {"name": existing.name, "price": str(existing.price)}
    await crud_delete_one_product(db, existing)
    await db.commit()

    await log_action(db=db, background_tasks=background_tasks, request=request,
                     user_id=current_user.user_id, category="PRODUCT", action="DELETE",
                     target_id=str(product_id), before_data=before_data,
                     request_id=request.state.request_id)
    return None
