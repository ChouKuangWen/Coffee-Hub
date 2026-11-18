"""模擬建單交易與訂單資料授權；不呼叫會自行提交的 CRUD。"""
import hashlib
import json
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import lazyload
from app.core.config import settings
from app.models.users import Users
from app.models.products import Products
from app.models.cart_item import CartItem
from app.models.orders import Orders
from app.models.order_items import OrderItems
from app.crud.orders import get_all_orders, get_orders_by_user, get_order_with_items
from app.services.audit_log_service import record_required_action


async def get_admin_orders_service(db, current_user):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="僅限管理員")
    return await get_all_orders(db)


async def get_customer_orders_service(db, target_user_id, current_user):
    if current_user.role_id != 1 and current_user.user_id != target_user_id:
        raise HTTPException(status_code=403, detail="無權查看他人訂單")
    return await get_orders_by_user(db, target_user_id)


def seller_order_view(order, seller_id):
    items = [item for item in order.order_items if item.seller_id == seller_id]
    if not items:
        raise HTTPException(status_code=403, detail="無權查看此訂單")
    return dict(order_id=order.order_id, status=order.status, status_label=order.status,
                created_at=order.created_at,
                seller_total=sum((item.subtotal for item in items), Decimal("0.00")))


async def get_seller_orders_service(db, current_user):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="僅限 Seller")
    from sqlalchemy.orm import selectinload
    result = await db.execute(select(Orders).where(Orders.order_id.in_(
        select(OrderItems.order_id).where(OrderItems.seller_id == current_user.user_id)))
        .options(selectinload(Orders.order_items)))
    return [seller_order_view(order, current_user.user_id) for order in result.scalars().all()]


async def get_authorized_order(db, order_id, current_user, sales=False):
    order = await get_order_with_items(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    if sales:
        if current_user.role_id != 2:
            raise HTTPException(status_code=403, detail="僅限 Seller 銷售查詢")
        return seller_order_view(order, current_user.user_id)
    if current_user.role_id == 1 or order.user_id == current_user.user_id:
        return order
    if current_user.role_id == 2:
        return seller_order_view(order, current_user.user_id)
    raise HTTPException(status_code=403, detail="無權查看此訂單")


async def create_order_service(db, request, background_tasks, current_user, order):
    if not (getattr(settings, "ENABLE_SIMULATED_CHECKOUT", False)
            and getattr(settings, "APP_ENV", "") == "test"):
        raise HTTPException(status_code=403, detail="僅隔離測試環境可啟用模擬建單")
    if current_user.role_id not in (2, 3):
        raise HTTPException(status_code=403, detail="Admin 不參與買家流程")
    selected = {item.cart_item_id: item.quantity for item in order.items}
    fingerprint = hashlib.sha256(json.dumps(sorted(selected.items())).encode()).hexdigest()
    key = str(order.checkout_key)
    try:
        # 先讀取不可由購物車更新更換的商品／賣家識別，以統一使用者→商品鎖順序。
        owner_ids = (await db.execute(select(Products.owner_id).join(CartItem,
            CartItem.product_id == Products.product_id).where(
                CartItem.cart_item_id.in_(selected), CartItem.user_id == current_user.user_id))).scalars().all()
        result = await db.execute(select(Users).where(Users.user_id.in_(
            set(owner_ids) | {current_user.user_id})).order_by(Users.user_id)
            .with_for_update().execution_options(populate_existing=True))
        users = {user.user_id: user for user in result.scalars().all()}
        actor = users.get(current_user.user_id)
        if (not actor or not actor.is_active or actor.role_id not in (2, 3)
                or actor.token_version != request.state.auth_version):
            raise HTTPException(status_code=403, detail="帳號已停用或權限已變更")
        # 同一買家鎖序列化所有轉單；重送先查已提交結果，不依賴已清除的購物車。
        existing = (await db.execute(select(Orders).where(
            Orders.user_id == actor.user_id, Orders.checkout_key == key).with_for_update())).scalar_one_or_none()
        if existing:
            if existing.checkout_fingerprint != fingerprint:
                raise HTTPException(status_code=409, detail="同一請求識別碼不可用於不同品項")
            await db.commit()
            return existing
        result = await db.execute(select(CartItem).options(lazyload(CartItem.product))
            .where(CartItem.user_id == actor.user_id, CartItem.cart_item_id.in_(selected))
            .order_by(CartItem.cart_item_id).with_for_update().execution_options(populate_existing=True))
        cart = result.scalars().all()
        if len(cart) != len(selected) or any(item.quantity != selected[item.cart_item_id] for item in cart):
            raise HTTPException(status_code=409, detail="購物車已變更，請重新載入")
        result = await db.execute(select(Products).options(lazyload(Products.owner))
            .where(Products.product_id.in_([item.product_id for item in cart]))
            .order_by(Products.product_id).with_for_update().execution_options(populate_existing=True))
        products = {product.product_id: product for product in result.scalars().all()}
        total = Decimal("0.00")
        for item in cart:
            product = products.get(item.product_id)
            owner = users.get(product.owner_id) if product else None
            if not product or not product.is_active or not owner or not owner.is_active:
                raise HTTPException(status_code=409, detail="商品已下架或賣家已停用")
            if item.quantity <= 0 or product.stock < item.quantity:
                raise HTTPException(status_code=409, detail="商品庫存不足")
            if product.price <= 0:
                raise HTTPException(status_code=409, detail="商品價格無效")
            total += product.price * item.quantity
        if total > Decimal("99999999.99"):
            raise HTTPException(status_code=409, detail="商品金額超出可儲存範圍")
        created = Orders(user_id=actor.user_id, status="待出貨", total=total,
                         checkout_key=key, checkout_fingerprint=fingerprint)
        db.add(created)
        await db.flush()
        for item in cart:
            product = products[item.product_id]
            db.add(OrderItems(order_id=created.order_id, product_id=product.product_id,
                              product_name=product.name, seller_id=product.owner_id,
                              price=product.price, quantity=item.quantity))
            product.stock -= item.quantity
            await db.delete(item)
        await record_required_action(db, request, user_id=actor.user_id, category="ORDER",
            target_type="ORDER", action="SIMULATED_CREATE", target_id=created.order_id,
            after_data={"total": str(total), "currency": "TWD", "items": len(cart)})
        # MySQL 不提供 INSERT RETURNING；提交前載入 DB 產生的時間欄位。
        await db.refresh(created)
        await db.commit()
        return created
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="模擬建單失敗，所有異動已回滾")


async def update_order_status_service(db, request, background_tasks, current_user, order_id, status_update):
    # 完整取消／退庫存與多賣家狀態矩陣不屬本批，禁止舊入口繞過一致性規則。
    raise HTTPException(status_code=409, detail="狀態異動須經核准流程，目前不開放直接修改")


async def delete_order_service(db, request, background_tasks, current_user, order_id):
    raise HTTPException(status_code=409, detail="訂單歷史不可刪除")
