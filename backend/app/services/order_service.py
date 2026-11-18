"""模擬建單交易與訂單資料授權；不呼叫會自行提交的 CRUD。"""
import hashlib
import json
from datetime import datetime, timezone
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
from app.models.order_cancellation import OrderCancellation
from app.schemas.orders import OrderRead, CancellationRead
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


def _can_ship(order, seller_id, items):
    return (order.status == "待出貨" and order.stock_deducted and order.stock_returned_at is None
            and bool(items) and all(item.seller_id is not None for item in items)
            and any(item.seller_id == seller_id and item.shipped_at is None for item in items))


def seller_order_view(order, seller_id, all_items=None):
    all_items = order.order_items if all_items is None else all_items
    items = [item for item in all_items if item.seller_id == seller_id]
    if not items:
        raise HTTPException(status_code=403, detail="無權查看此訂單")
    return dict(order_id=order.order_id, status=order.status, status_label=order.status,
                created_at=order.created_at, can_ship=_can_ship(order, seller_id, all_items),
                seller_shipment_status="已出貨" if all(item.shipped_at is not None for item in items) else "未出貨",
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


def _require_simulation():
    if not (getattr(settings, "ENABLE_SIMULATED_CHECKOUT", False)
            and getattr(settings, "APP_ENV", "") == "test"):
        raise HTTPException(status_code=403, detail="僅隔離測試環境可啟用模擬訂單異動")


async def create_order_service(db, request, background_tasks, current_user, order):
    _require_simulation()
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
                         checkout_key=key, checkout_fingerprint=fingerprint, stock_deducted=True)
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


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _lock_lifecycle(db, request, current_user, order_id, roles):
    # 與前三批一致：先鎖操作者，再鎖訂單；商品依 ID 固定順序鎖定。
    actor = (await db.execute(select(Users).where(Users.user_id == current_user.user_id)
        .with_for_update().execution_options(populate_existing=True))).scalar_one_or_none()
    if (not actor or not actor.is_active or actor.role_id not in roles
            or actor.token_version != request.state.auth_version):
        raise HTTPException(status_code=403, detail="目前帳號無權執行此操作")
    order = (await db.execute(select(Orders).where(Orders.order_id == order_id)
        .with_for_update().execution_options(populate_existing=True))).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    return actor, order


async def _lock_order_items(db, order_id):
    return (await db.execute(select(OrderItems).options(lazyload("*"))
        .where(OrderItems.order_id == order_id).order_by(OrderItems.order_item_id)
        .with_for_update().execution_options(populate_existing=True))).scalars().all()


async def _audit_order(db, request, actor, order, action, before, after):
    await record_required_action(db, request, user_id=actor.user_id, category="ORDER",
        target_type="ORDER", action=action, target_id=order.order_id,
        before_data=before, after_data=after)


async def request_cancellation(db, request, current_user, order_id, data):
    _require_simulation()
    try:
        actor, order = await _lock_lifecycle(db, request, current_user, order_id, (2, 3))
        if order.user_id != actor.user_id:
            raise HTTPException(status_code=403, detail="只能申請取消本人訂單")
        if order.status not in ("待付款", "已付款", "待出貨"):
            raise HTTPException(status_code=409, detail="目前狀態不允許一般取消申請")
        items = await _lock_order_items(db, order_id)
        if any(item.shipped_at is not None for item in items):
            raise HTTPException(status_code=409, detail="已有品項出貨，不允許一般整單取消")
        pending = (await db.execute(select(OrderCancellation).where(
            OrderCancellation.order_id == order_id, OrderCancellation.status == "pending")
            .with_for_update())).scalar_one_or_none()
        if pending:
            if pending.reason != data.reason:
                raise HTTPException(status_code=409, detail="已有待審取消申請")
            result = CancellationRead.model_validate(pending)
            await db.commit()
            return result
        cancellation = OrderCancellation(order_id=order_id, requested_by=actor.user_id, reason=data.reason)
        db.add(cancellation)
        await db.flush()
        await _audit_order(db, request, actor, order, "CANCELLATION_REQUEST",
            {"status": order.status}, {"status": order.status, "cancellation_id": cancellation.cancellation_id})
        await db.refresh(cancellation)
        result = CancellationRead.model_validate(cancellation)
        await db.commit()
        return result
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="取消申請或必要審計失敗，未完成操作")


async def get_cancellations(db, current_user, order_id):
    order = (await db.execute(select(Orders).where(Orders.order_id == order_id))).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    if current_user.role_id != 1 and order.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="無權查看取消申請")
    return (await db.execute(select(OrderCancellation).where(OrderCancellation.order_id == order_id)
        .order_by(OrderCancellation.cancellation_id.desc()))).scalars().all()


async def review_cancellation(db, request, current_user, cancellation_id, data):
    _require_simulation()
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="僅 Admin 可以審核取消申請")
    try:
        order_id = (await db.execute(select(OrderCancellation.order_id).where(
            OrderCancellation.cancellation_id == cancellation_id))).scalar_one_or_none()
        if order_id is None:
            raise HTTPException(status_code=404, detail="取消申請不存在")
        actor, order = await _lock_lifecycle(db, request, current_user, order_id, (1,))
        cancellation = (await db.execute(select(OrderCancellation).where(
            OrderCancellation.cancellation_id == cancellation_id).with_for_update()
            .execution_options(populate_existing=True))).scalar_one()
        if cancellation.status != "pending":
            if cancellation.status != data.decision or cancellation.review_note != data.review_note:
                raise HTTPException(status_code=409, detail="已完成審核，不可變更決定")
            result = CancellationRead.model_validate(cancellation)
            await db.commit()
            return result
        before = {"status": order.status, "stock_returned": order.stock_returned_at is not None,
                  "cancellation_status": cancellation.status}
        returned = []
        if data.decision == "approved":
            if order.status not in ("待付款", "已付款", "待出貨"):
                raise HTTPException(status_code=409, detail="已出貨或目前狀態不允許取消")
            if not order.stock_deducted or order.stock_returned_at is not None:
                raise HTTPException(status_code=409, detail="缺少可信扣庫存證據，或已退還庫存")
            items = await _lock_order_items(db, order_id)
            if any(item.shipped_at is not None for item in items):
                raise HTTPException(status_code=409, detail="已有品項出貨，不允許核准整單取消")
            if not items or any(item.product_id is None or item.quantity <= 0 for item in items):
                raise HTTPException(status_code=409, detail="歷史商品資料不足，無法安全退庫存")
            quantities = {}
            for item in items:
                quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
            products = (await db.execute(select(Products).options(lazyload(Products.owner))
                .where(Products.product_id.in_(quantities)).order_by(Products.product_id)
                .with_for_update().execution_options(populate_existing=True))).scalars().all()
            if len(products) != len(quantities) or any(
                    p.stock < 0 or p.stock + quantities[p.product_id] > 2147483647 for p in products):
                raise HTTPException(status_code=409, detail="商品不存在或退庫存超出可儲存範圍")
            for product in products:
                product.stock += quantities[product.product_id]
                returned.append({"product_id": product.product_id, "quantity": quantities[product.product_id]})
            order.status = "已取消"
            order.status_updated_at = _now()
            order.stock_returned_at = _now()
        cancellation.status = data.decision
        cancellation.reviewed_by = actor.user_id
        cancellation.reviewed_at = _now()
        cancellation.review_note = data.review_note
        await _audit_order(db, request, actor, order, "CANCELLATION_REVIEW", before,
            {"status": order.status, "cancellation_id": cancellation_id,
             "decision": data.decision, "returned": returned})
        result = CancellationRead.model_validate(cancellation)
        await db.commit()
        return result
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="取消審核、退庫存或必要審計失敗，所有異動已回滾")


async def update_order_status_service(db, request, background_tasks, current_user, order_id, status_update):
    _require_simulation()
    try:
        actor, order = await _lock_lifecycle(db, request, current_user, order_id, (1, 2))
        target = status_update.status.value
        items = await _lock_order_items(db, order_id)
        if not order.stock_deducted or order.stock_returned_at is not None:
            raise HTTPException(status_code=409, detail="非可驗證的有效模擬訂單")
        if actor.role_id == 2:
            owned = [item for item in items if item.seller_id == actor.user_id]
            if not owned:
                raise HTTPException(status_code=403, detail="不能操作其他 Seller 的出貨品項")
            if target != "已出貨":
                raise HTTPException(status_code=403, detail="Seller 僅可標記本人品項已出貨")
            if order.status not in ("待出貨", "已出貨") or any(item.seller_id is None for item in items):
                raise HTTPException(status_code=409, detail="目前狀態或歷史快照不允許出貨")
            changed = [item for item in owned if item.shipped_at is None]
            if changed:
                if order.status != "待出貨":
                    raise HTTPException(status_code=409, detail="訂單與品項出貨狀態不一致")
                before = order.status
                for item in changed:
                    item.shipped_at = _now()
                if all(item.shipped_at is not None for item in items):
                    order.status = "已出貨"
                    order.status_updated_at = _now()
                await _audit_order(db, request, actor, order, "SHIP_ITEMS",
                    {"status": before, "items": [{"order_item_id": item.order_item_id, "shipped_at": None} for item in changed]},
                    {"status": order.status, "items": [{"order_item_id": item.order_item_id, "shipped_at": item.shipped_at.isoformat()} for item in changed]})
        else:
            if target != "已完成":
                raise HTTPException(status_code=409, detail="Admin 僅可將已出貨改為已完成；取消請走審核")
            if order.status != "已完成":
                if order.status != "已出貨" or not items or any(item.shipped_at is None for item in items):
                    raise HTTPException(status_code=409, detail="全部品項已出貨後才能完成")
                before = order.status
                order.status = target
                order.status_updated_at = _now()
                await _audit_order(db, request, actor, order, "STATUS_CHANGE", {"status": before}, {"status": target})
        result = (OrderRead.model_validate(order) if actor.role_id == 1
                  else seller_order_view(order, actor.user_id, items))
        await db.commit()
        return result
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="訂單狀態或必要審計失敗，未完成操作")


async def delete_order_service(db, request, background_tasks, current_user, order_id):
    raise HTTPException(status_code=409, detail="訂單歷史不可刪除")
