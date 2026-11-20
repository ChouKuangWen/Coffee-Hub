"""Batch 3：僅使用明確指定的 TEMP 隔離 MySQL，不讀 .env、不刪既有資料。"""
import asyncio
import os
import re
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import select, text, func
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from tests.unit.test_account_permissions import isolated_app, csrf_client


@pytest.mark.skipif(not os.getenv("COFFEEHUB_TEST_MYSQL_URL"), reason="未指定獨立 MySQL")
def test_checkout_mysql(isolated_app, monkeypatch):
    asyncio.run(_scenario(isolated_app, monkeypatch))


async def _scenario(env, monkeypatch):
    from app.models.users import Users
    from app.models.roles import Roles
    from app.models.products import Products
    from app.models.orders import Orders
    from app.models.order_items import OrderItems
    from app.models.cart_item import CartItem
    from app.models.audit_log import AuditLog
    from app.core.security import hash_password
    from app.services import order_service, product_service

    url = make_url(os.environ["COFFEEHUB_TEST_MYSQL_URL"])
    expected_dir = Path(os.environ["COFFEEHUB_TEST_MYSQL_DATADIR"])
    assert url.host in ("localhost", "127.0.0.1") and url.port not in (None, 3306, 3307)
    assert expected_dir.name.startswith("coffeehub-batch3-")
    database = "coffeehub_batch3_" + uuid4().hex
    bootstrap = create_async_engine(url.set(database=None))
    try:
        async with bootstrap.begin() as conn:
            assert Path((await conn.execute(text("SELECT @@datadir"))).scalar_one()).resolve() == expected_dir.resolve()
            await conn.execute(text(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4"))
    finally:
        await bootstrap.dispose()
    engine = create_async_engine(url.set(database=database))
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def get_db():
        async with sessions() as session:
            yield session

    env.app.dependency_overrides[env.get_db] = get_db
    env.app.state.limiter.enabled = False
    monkeypatch.setattr(order_service.settings, "APP_ENV", "test", raising=False)
    monkeypatch.setattr(order_service.settings, "ENABLE_SIMULATED_CHECKOUT", True, raising=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Roles.__table__.create)
            await conn.run_sync(Users.__table__.create)
            await conn.run_sync(Products.__table__.create)
            # 用舊版表結構驗證增量升級，不執行 init.sql 的 DROP DATABASE／USE。
            await conn.execute(text("""CREATE TABLE orders (
                order_id INT PRIMARY KEY AUTO_INCREMENT, user_id INT NULL,
                status VARCHAR(50) NOT NULL DEFAULT '待付款', total DECIMAL(10,2) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)) ENGINE=InnoDB"""))
            await conn.execute(text("""CREATE TABLE order_items (
                order_item_id INT PRIMARY KEY AUTO_INCREMENT, order_id INT NOT NULL,
                product_id INT NULL, quantity INT NOT NULL, price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE SET NULL) ENGINE=InnoDB"""))
            await conn.execute(text("INSERT INTO orders(total) VALUES(12.50)"))
            await conn.execute(text("INSERT INTO order_items(order_id,quantity,price) VALUES(1,1,12.50)"))
            await conn.run_sync(AuditLog.__table__.create)
            for migration in ("001_account_lifecycle.sql", "002_simulated_checkout.sql", "002_simulated_checkout.sql", "003_order_lifecycle.sql"):
                script = Path("../database/migrations", migration).read_text(encoding="utf-8")
                sql = "\n".join(line for line in script.splitlines() if not line.lstrip().startswith("--"))
                for statement in sql.split(";"):
                    if statement.strip():
                        await conn.execute(text(statement))
            assert tuple((await conn.execute(text("SELECT quantity,price,product_name,seller_id FROM order_items WHERE order_item_id=1"))).one()) == (1, Decimal("12.50"), None, None)
            assert (await conn.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version IN ('001_account_lifecycle','002_simulated_checkout')"))).scalar_one() == 2
            await conn.run_sync(Users.metadata.create_all)
        # 新建與升級後交易欄位、冪等索引及快照外鍵一致。
        fresh = create_async_engine(url.set(database=database + "_fresh"))
        try:
            async with engine.begin() as conn:
                await conn.execute(text(f"CREATE DATABASE `{database}_fresh` CHARACTER SET utf8mb4"))
            async with fresh.begin() as conn:
                script = Path("../database/init.sql").read_text(encoding="utf-8")
                sql = "\n".join(line for line in script.splitlines() if not line.lstrip().startswith("--"))
                for statement in sql.split(";"):
                    match = re.match(r"\s*CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?(\w+)", statement, re.I)
                    if match and match[1] in {"roles", "users", "products", "orders", "order_items"}:
                        await conn.execute(text(statement))
            query = text("""SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT
                FROM information_schema.columns WHERE TABLE_SCHEMA=DATABASE() AND
                ((TABLE_NAME='orders' AND COLUMN_NAME IN ('checkout_key','checkout_fingerprint')) OR
                 (TABLE_NAME='order_items' AND COLUMN_NAME IN ('product_name','seller_id')))
                ORDER BY TABLE_NAME,COLUMN_NAME""")
            async with engine.connect() as old, fresh.connect() as new:
                assert (await old.execute(query)).all() == (await new.execute(query)).all()
                for conn in (old, new):
                    assert (await conn.execute(text("SELECT COUNT(*) FROM information_schema.statistics WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='orders' AND INDEX_NAME='uq_orders_checkout' AND NON_UNIQUE=0"))).scalar_one() == 2
                    assert (await conn.execute(text("SELECT COUNT(*) FROM information_schema.key_column_usage WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='order_items' AND COLUMN_NAME='seller_id' AND REFERENCED_TABLE_NAME='users'"))).scalar_one() == 1
        finally:
            await fresh.dispose()
        print("PASS migrations 001/002, rerun, legacy preservation, fresh/upgrade schema")

        async with sessions() as db:
            db.add_all([Roles(role_id=i, name=name) for i, name in [(1, "Admin"), (2, "Seller"), (3, "Customer")]])
            await db.flush()
            for name, role in [("admin", 1), ("seller1", 2), ("seller2", 2), ("buyer1", 3), ("buyer2", 3)]:
                db.add(Users(username=name, email=f"{name}@example.com", password_hash=hash_password("test-only-value"), phone="0", address="test", role_id=role))
            await db.commit()

        def client():
            return csrf_client(env.app)

        def check(response, status=200):
            assert response.status_code == status, (response.status_code, response.text)
            return response.json() if response.content else None

        async def snapshot():
            async with sessions() as db:
                return (
                    (await db.execute(select(Orders.order_id, Orders.total).order_by(Orders.order_id))).all(),
                    (await db.execute(select(OrderItems.order_item_id, OrderItems.quantity, OrderItems.price).order_by(OrderItems.order_item_id))).all(),
                    (await db.execute(select(Products.product_id, Products.stock).order_by(Products.product_id))).all(),
                    (await db.execute(select(CartItem.cart_item_id, CartItem.quantity).order_by(CartItem.cart_item_id))).all(),
                )

        async with client() as admin, client() as s1, client() as s2, client() as a, client() as b:
            identities = {}
            for c, name in [(admin, "admin"), (s1, "seller1"), (s2, "seller2"), (a, "buyer1"), (b, "buyer2")]:
                identities[name] = check(await c.post("/auth/login", data={"username": f"{name}@example.com", "password": "test-only-value"}))
            async def product(c, name, stock=10, price="12.50"):
                return check(await c.post("/products/", json={"name": name, "price": price, "stock": stock}), 201)

            p1 = await product(s1, "bean one")
            p2 = await product(s2, "bean two", price="3.25")
            check(await s2.patch(f"/products/{p1['product_id']}", json={"price": "1"}), 403)
            check(await s2.delete(f"/products/{p1['product_id']}"), 403)
            check(await a.post("/products/", json={"name": "x", "price": "1"}), 403)
            check(await a.get("/products/dashboard"), 403)
            check(await admin.get('/cart'), 403)
            for invalid in ({"stock": -1}, {"stock": 1.5}, {"price": "0"}, {"price": "NaN"}, {"price": "1.001"}, {"stock": None}, {"price": None}):
                check(await s1.patch(f"/products/{p1['product_id']}", json=invalid), 422)
            check(await admin.patch(f"/products/{p1['product_id']}", json={"stock": 10}), 200)
            # 必要商品審計失敗也不能保存異動。
            with monkeypatch.context() as patch:
                patch.setattr(product_service, "record_required_action", AsyncMock(side_effect=RuntimeError("audit unavailable")))
                check(await s1.patch(f"/products/{p1['product_id']}", json={"stock": 2}), 500)
            assert check(await s1.get(f"/products/{p1['product_id']}"))["stock"] == 10

            async def add(c, p, qty):
                return check(await c.post("/cart", json={"product_id": p["product_id"], "quantity": qty}), 201)

            c1, c2 = await add(a, p1, 2), await add(a, p2, 3)
            untouched = await add(a, await product(s1, "unselected"), 1)
            check(await b.patch(f"/cart/{c1['cart_item_id']}", json={"quantity": 1}), 404)
            check(await b.delete(f"/cart/{c1['cart_item_id']}"), 404)
            check(await a.patch(f"/cart/{c1['cart_item_id']}", json={"quantity": 3}))
            check(await a.patch(f"/cart/{c1['cart_item_id']}", json={"quantity": 2}))
            assert check(await s1.get(f"/products/{p1['product_id']}"))["stock"] == 10
            remove = await add(b, p2, 1)
            check(await b.delete(f"/cart/{remove['cart_item_id']}"), 204)

            def payload(*items):
                return {"checkout_key": str(uuid4()), "items": [{"cart_item_id": item["cart_item_id"], "quantity": item["quantity"]} for item in items]}

            body = payload(c1, c2)
            for extra in ({"total": "1"}, {"user_id": identities['buyer2']['user_id']}, {"price": "1"}):
                check(await a.post('/orders/', json={**body, **extra}), 422)
            monkeypatch.setattr(order_service.settings, "APP_ENV", "production")
            check(await a.post('/orders/', json=body), 403)
            monkeypatch.setattr(order_service.settings, "APP_ENV", "test")
            monkeypatch.setattr(order_service.settings, "ENABLE_SIMULATED_CHECKOUT", False)
            check(await a.post('/orders/', json=body), 403)
            monkeypatch.setattr(order_service.settings, "ENABLE_SIMULATED_CHECKOUT", True)
            check(await admin.post('/orders/', json=body), 403)
            # 已 flush 表頭／明細／庫存／清車後的審計故障必須全部回滾。
            before = await snapshot()
            async def fail_after_flush(db, *args, **kwargs):
                await db.flush()
                # 以真實 MySQL FK 錯誤驗證已寫入 SQL 仍完整回滾。
                await db.execute(text("INSERT INTO order_items(order_id,quantity,price) VALUES(-1,1,1)"))
            with monkeypatch.context() as patch:
                patch.setattr(order_service, "record_required_action", fail_after_flush)
                check(await a.post('/orders/', json=body), 500)
            assert await snapshot() == before
            # 同一識別碼並行重送只有一張訂單、一次扣庫存。
            responses = await asyncio.gather(a.post('/orders/', json=body), a.post('/orders/', json=body))
            created = [check(response) for response in responses]
            assert created[0]['order_id'] == created[1]['order_id']
            order_id = created[0]['order_id']
            assert Decimal(created[0]['total']) == Decimal("34.75")
            async with sessions() as db:
                assert (await db.get(Products, p1['product_id'])).stock == 8
                assert (await db.get(Products, p2['product_id'])).stock == 7
                assert await db.get(CartItem, untouched['cart_item_id']) is not None
                assert (await db.execute(select(func.count()).select_from(Orders).where(Orders.checkout_key == body['checkout_key']))).scalar_one() == 1
            conflict = {**body, 'items': [body['items'][0]]}
            check(await a.post('/orders/', json=conflict), 409)
            changed_quantity = {**body, 'items': [dict(i, quantity=i['quantity'] + 1) for i in body['items']]}
            check(await a.post('/orders/', json=changed_quantity), 409)
            # 鍵只在同一使用者內有效，不能以別人的鍵或購物車取得其訂單。
            check(await b.post('/orders/', json=body), 409)
            other_cart = await add(b, p2, 1)
            other_body = {**payload(other_cart), 'checkout_key': body['checkout_key']}
            other_order = check(await b.post('/orders/', json=other_body))
            assert other_order['order_id'] != order_id and other_order['user_id'] == identities['buyer2']['user_id']
            check(await a.post('/orders/', json=payload(c1)), 409)
            check(await b.get(f'/orders/{order_id}'), 403)
            details = check(await a.get(f'/order_items/by_order/{order_id}'))['items']
            assert len(details) == 2 and sum(Decimal(i['subtotal']) for i in details) == Decimal('34.75')
            for seller, name, own_p in [(s1, 'seller1', p1), (s2, 'seller2', p2)]:
                sales = check(await seller.get('/orders/seller'))['items']
                sales_order = next(order for order in sales if order['order_id'] == order_id)
                assert all('total' not in order and 'user_id' not in order for order in sales)
                assert check(await seller.get(f'/orders/{order_id}')) == sales_order
                own = check(await seller.get(f'/order_items/by_order/{order_id}'))['items']
                assert len(own) == 1 and own[0]['seller_id'] == identities[name]['user_id']
                assert 'order' not in own[0] and 'product' not in own[0]
                other_item = next(i for i in details if i['product_id'] != own_p['product_id'])
                check(await seller.get(f"/order_items/{other_item['order_item_id']}"), 403)
            check(await a.patch(f"/order_items/{details[0]['order_item_id']}", json={"order_id": order_id, "product_id": p2['product_id'], "quantity": 1, "price": "1"}), 409)
            check(await admin.delete(f'/orders/{order_id}'), 409)
            check(await a.patch(f'/orders/{order_id}/status', json={'status': '已取消'}), 403)
            check(await s1.patch(f"/products/{p1['product_id']}", json={'name': 'renamed', 'price': '99.00'}))
            check(await s1.delete(f"/products/{p1['product_id']}"), 204)
            assert check(await a.get(f'/order_items/by_order/{order_id}'))['items'] == details
            async with client() as visitor:
                check(await visitor.get(f"/products/{p1['product_id']}"), 403)
                assert p1['product_id'] not in [p['product_id'] for p in check(await visitor.get('/products'))['items']]
            check(await s1.patch(f"/products/{p1['product_id']}", json={'is_active': True}))
            print('PASS products/ownership/audit, cart CRUD/no reservation, atomic checkout/rollback, snapshots, mixed-Seller read isolation, replay')

            # 下架、購物車數量競爭及不足庫存均整單拒絕，保留所有品項。
            stale = await add(b, p1, 1)
            check(await s1.delete(f"/products/{p1['product_id']}"), 204)
            before = await snapshot()
            check(await b.patch(f"/cart/{stale['cart_item_id']}", json={'quantity': 1}), 404)
            check(await b.post('/orders/', json=payload(stale)), 409)
            assert await snapshot() == before
            check(await s1.patch(f"/products/{p1['product_id']}", json={'is_active': True}))
            stale_body = payload(stale)
            check(await b.patch(f"/cart/{stale['cart_item_id']}", json={'quantity': 2}))
            before = await snapshot()
            check(await b.post('/orders/', json=stale_body), 409)
            assert await snapshot() == before
            check(await b.delete(f"/cart/{stale['cart_item_id']}"), 204)
            scarce = await product(s2, 'scarce', stock=5)
            ca, cb = await add(a, scarce, 3), await add(b, scarce, 3)
            requests = await asyncio.gather(a.post('/orders/', json=payload(ca)), b.post('/orders/', json=payload(cb)))
            assert sorted(r.status_code for r in requests) == [200, 409]
            async with sessions() as db:
                assert (await db.get(Products, scarce['product_id'])).stock == 2
                assert (await db.execute(select(func.count()).select_from(CartItem).where(CartItem.product_id == scarce['product_id']))).scalar_one() == 1
            # 一張單包含足量及不足商品，不得只處理足量者。
            loser, failed_cart = (b, cb) if requests[1].status_code == 409 else (a, ca)
            good = await add(loser, p2, 1)
            before = await snapshot()
            check(await loser.post('/orders/', json=payload(good, failed_cart)), 409)
            assert await snapshot() == before
            # Seller 作為買家仍能讀本人完整混合訂單。
            sc1, sc2 = await add(s1, p1, 1), await add(s1, p2, 1)
            seller_purchase = check(await s1.post('/orders/', json=payload(sc1, sc2)))
            assert 'total' in check(await s1.get(f"/orders/{seller_purchase['order_id']}"))
            assert len(check(await s1.get(f"/order_items/by_order/{seller_purchase['order_id']}"))['items']) == 2
            sale_view = check(await s1.get(f"/orders/{seller_purchase['order_id']}?sales=true"))
            assert 'total' not in sale_view and 'user_id' not in sale_view
            sale_details = check(await s1.get(f"/order_items/by_order/{seller_purchase['order_id']}?sales=true"))['items']
            assert len(sale_details) == 1 and sale_details[0]['product_id'] == p1['product_id']
            print('PASS inactive/stale cart, insufficient entire-order rollback, parallel stock 5 / two requests 3, Seller buyer view')

            # 購物車回應尚未讀取完成時，轉單須等待同一買家的鎖。
            from app.api import cart as cart_api
            race_item = await add(b, await product(s2, 'cart response race'), 1)
            entered, release = asyncio.Event(), asyncio.Event()
            original_read = cart_api._read_item

            async def paused_read(db, item_id):
                entered.set()
                await release.wait()
                return await original_read(db, item_id)

            with monkeypatch.context() as patch:
                patch.setattr(cart_api, '_read_item', paused_read)
                update_task = asyncio.create_task(b.patch(f"/cart/{race_item['cart_item_id']}", json={'quantity': 1}))
                checkout_task = None
                try:
                    await asyncio.wait_for(entered.wait(), 5)
                    checkout_task = asyncio.create_task(b.post('/orders/', json=payload(race_item)))
                    done, _ = await asyncio.wait([checkout_task], timeout=0.25)
                    assert not done, '轉單不應在購物車回應準備完成前移除品項'
                finally:
                    release.set()
                    results = await asyncio.gather(update_task, *([checkout_task] if checkout_task else []), return_exceptions=True)
                assert len(results) == 2
                for response in results:
                    assert not isinstance(response, Exception), repr(response)
                    check(response)
            async with sessions() as db:
                assert await db.get(CartItem, untouched['cart_item_id']) is not None
            # 舊資料 NULL 不授予 Seller 權限，且不開放任意改寫。
            check(await s1.get('/orders/1'), 403)
            check(await s1.get('/order_items/1'), 403)
            check(await s1.get('/order_items/by_order/1'), 403)
            assert check(await admin.get('/order_items/1'))['seller_id'] is None
            check(await admin.patch('/order_items/1', json={'order_id': 1, 'quantity': 1, 'price': '1'}), 409)
            check(await admin.patch(f"/users/{identities['seller1']['user_id']}/activation", json={'is_active': False}))
            assert check(await a.get(f'/order_items/by_order/{order_id}'))['items'] == details
            check(await admin.patch(f"/users/{identities['seller1']['user_id']}/activation", json={'is_active': True}))
            assert check(await a.get(f'/order_items/by_order/{order_id}'))['items'] == details
            print('PASS cross-user keys / changed payload rejection / cart response race / legacy NULL isolation / Seller activation snapshot retention')
    finally:
        env.app.dependency_overrides.clear()
        env.app.state.limiter.enabled = True
        await engine.dispose()
