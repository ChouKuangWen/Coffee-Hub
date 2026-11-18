"""Batch 4 必要整合：專用 loopback MySQL、獨立新 schema，不讀正式設定。"""
import asyncio
import os
import re
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from tests.unit.test_account_permissions import isolated_app


@pytest.mark.skipif(not os.getenv("COFFEEHUB_TEST_MYSQL_URL"), reason="未指定獨立測試 MySQL")
def test_order_lifecycle_mysql(isolated_app, monkeypatch):
    asyncio.run(_scenario(isolated_app, monkeypatch))


async def _scenario(env, monkeypatch):
    from app.models.users import Users
    from app.models.roles import Roles
    from app.models.products import Products
    from app.models.orders import Orders
    from app.models.order_items import OrderItems
    from app.models.order_cancellation import OrderCancellation
    from app.models.audit_log import AuditLog
    from app.core.security import hash_password
    from app.services import order_service

    url = make_url(os.environ['COFFEEHUB_TEST_MYSQL_URL'])
    expected = Path(os.environ['COFFEEHUB_TEST_MYSQL_DATADIR'])
    assert url.host in ('localhost', '127.0.0.1') and url.port not in (None, 3306, 3307)
    assert expected.name.startswith(('coffeehub-batch3-', 'coffeehub-batch4-'))
    name = 'coffeehub_batch4_' + uuid4().hex
    bootstrap = create_async_engine(url.set(database=None))
    try:
        async with bootstrap.begin() as conn:
            assert Path((await conn.execute(text('SELECT @@datadir'))).scalar_one()).resolve() == expected.resolve()
            await conn.execute(text(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4'))
            await conn.execute(text(f'CREATE DATABASE `{name}_fresh` CHARACTER SET utf8mb4'))
    finally:
        await bootstrap.dispose()
    engine = create_async_engine(url.set(database=name))
    fresh = create_async_engine(url.set(database=name + '_fresh'))
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def get_db():
        async with sessions() as db:
            yield db

    env.app.dependency_overrides[env.get_db] = get_db
    env.app.state.limiter.enabled = False
    monkeypatch.setattr(order_service.settings, 'APP_ENV', 'test', raising=False)
    monkeypatch.setattr(order_service.settings, 'ENABLE_SIMULATED_CHECKOUT', True, raising=False)
    try:
        async with engine.begin() as conn:
            for table in (Roles.__table__, Users.__table__, Products.__table__, AuditLog.__table__):
                await conn.run_sync(table.create)
            init = Path('../database/init.sql').read_text(encoding='utf-8')
            sql = '\n'.join(line for line in init.splitlines() if not line.lstrip().startswith('--'))
            # 重建的是本次全新空 schema 的舊版表結構，不執行 DROP DATABASE／USE。
            for statement in sql.split(';'):
                match = re.match(r'\s*CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?(\w+)', statement, re.I)
                if match and match[1] in {'orders', 'order_items'}:
                    old = re.sub(r'^\s*(?:stock_deducted|stock_returned_at|shipped_at)\s+[^\n]+\n', '\n', statement, flags=re.M)
                    await conn.execute(text(old))
        async with sessions() as db:
            db.add_all([Roles(role_id=i, name=n) for i, n in [(1, 'Admin'), (2, 'Seller'), (3, 'Customer')]])
            await db.flush()
            for i, n, role in [(1,'admin',1),(2,'s1',2),(3,'s2',2),(4,'a',3),(5,'b',3),(6,'admin2',1)]:
                db.add(Users(user_id=i, username=n, email=f'{n}@example.com', phone='0', address='test',
                             role_id=role, password_hash=hash_password('test-only-value')))
            await db.flush()
            db.add(Products(product_id=1, name='migration bean', price=10, stock=10, owner_id=2))
            await db.commit()
        async with engine.begin() as conn:
            await conn.execute(text("INSERT INTO orders(order_id,user_id,total,checkout_key,checkout_fingerprint) VALUES(1,4,10,NULL,NULL),(2,4,10,:k,:f),(3,4,10,:k2,:f)"),
                               {'k': str(uuid4()), 'k2': str(uuid4()), 'f': 'f' * 64})
            await conn.execute(text("INSERT INTO order_items(order_id,product_id,quantity,price,product_name,seller_id) VALUES(1,1,1,10,NULL,NULL),(2,1,1,10,'migration bean',2),(3,1,1,10,'migration bean',2)"))
            await conn.execute(text("INSERT INTO audit_logs(user_id,category,action,target_type,target_id,status) VALUES(4,'ORDER','SIMULATED_CREATE','ORDER','2','SUCCESS')"))
            for filename in ('001_account_lifecycle.sql', '002_simulated_checkout.sql', '003_order_lifecycle.sql'):
                script = Path('../database/migrations', filename).read_text(encoding='utf-8')
                script = '\n'.join(line for line in script.splitlines() if not line.lstrip().startswith('--'))
                for statement in script.split(';'):
                    if statement.strip():
                        await conn.execute(text(statement))
            assert (await conn.execute(text('SELECT stock_deducted FROM orders ORDER BY order_id'))).scalars().all() == [0, 1, 0]
            await conn.execute(text("UPDATE orders SET status='已取消',stock_returned_at='2026-01-01 00:00:00' WHERE order_id=2"))
            script = Path('../database/migrations/003_order_lifecycle.sql').read_text(encoding='utf-8')
            script = '\n'.join(line for line in script.splitlines() if not line.lstrip().startswith('--'))
            for statement in script.split(';'):
                if statement.strip():
                    await conn.execute(text(statement))
            assert str((await conn.execute(text('SELECT stock_returned_at FROM orders WHERE order_id=2'))).scalar_one()) == '2026-01-01 00:00:00'
            assert tuple((await conn.execute(text('SELECT product_name,seller_id,shipped_at FROM order_items WHERE order_id=1'))).one()) == (None, None, None)
            assert (await conn.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='003_order_lifecycle'"))).scalar_one() == 1
            await conn.run_sync(Users.metadata.create_all)
        async with fresh.begin() as conn:
            for statement in sql.split(';'):
                match = re.match(r'\s*CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?(\w+)', statement, re.I)
                if match and match[1] in {'roles','users','products','orders','order_items','order_cancellations'}:
                    await conn.execute(text(statement))
        query = text("""SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT,EXTRA
            FROM information_schema.columns WHERE TABLE_SCHEMA=DATABASE() AND
            (TABLE_NAME='order_cancellations' OR (TABLE_NAME='orders' AND COLUMN_NAME IN ('stock_deducted','stock_returned_at'))
             OR (TABLE_NAME='order_items' AND COLUMN_NAME='shipped_at')) ORDER BY TABLE_NAME,COLUMN_NAME""")
        async with engine.connect() as old, fresh.connect() as new:
            assert (await old.execute(query)).all() == (await new.execute(query)).all()
        print('PASS migration 003 / trusted Batch 3 evidence / unknown history preserved / rerun / fresh-upgrade schema')

        def client():
            return httpx.AsyncClient(transport=httpx.ASGITransport(env.app), base_url='https://testserver')

        def check(response, status=200):
            assert response.status_code == status, (response.status_code, response.text)
            return response.json() if response.content else None

        async def state(oid):
            async with sessions() as db:
                order = await db.get(Orders, oid)
                items = (await db.execute(select(OrderItems.order_item_id, OrderItems.quantity, OrderItems.price, OrderItems.shipped_at)
                                         .where(OrderItems.order_id == oid).order_by(OrderItems.order_item_id))).all()
                stock = (await db.execute(select(Products.product_id, Products.stock).order_by(Products.product_id))).all()
                requests = (await db.execute(select(OrderCancellation.cancellation_id, OrderCancellation.status)
                                            .where(OrderCancellation.order_id == oid).order_by(OrderCancellation.cancellation_id))).all()
                return order.status, order.stock_returned_at, items, stock, requests

        async with client() as admin, client() as admin2, client() as s1, client() as s2, client() as a, client() as b:
            for c, n in [(admin,'admin'),(admin2,'admin2'),(s1,'s1'),(s2,'s2'),(a,'a'),(b,'b')]:
                check(await c.post('/auth/login', data={'username': f'{n}@example.com', 'password':'test-only-value'}))
            p1 = check(await s1.post('/products/', json={'name':'one','price':'10.50','stock':30}), 201)
            p2 = check(await s2.post('/products/', json={'name':'two','price':'5','stock':30}), 201)

            async def order(c=a, mixed=True):
                entries = []
                for p, quantity in [(p1,2), (p2,3)] if mixed else [(p1,2)]:
                    item = check(await c.post('/cart', json={'product_id':p['product_id'],'quantity':quantity}), 201)
                    entries.append({'cart_item_id':item['cart_item_id'],'quantity':item['quantity']})
                created = check(await c.post('/orders/', json={'checkout_key':str(uuid4()),'items':entries}))
                assert created['status'] == '待出貨'
                return created['order_id']

            async def request(oid, c=a):
                return check(await c.post(f'/orders/{oid}/cancellation-requests', json={'reason':'test reason'}))

            async def review(entry, decision='approved', c=admin):
                return await c.patch(f"/orders/cancellation-requests/{entry['cancellation_id']}", json={'decision':decision})

            async def ship(oid, c):
                return await c.patch(f'/orders/{oid}/status', json={'status':'已出貨'})

            oid = await order()
            baseline = await state(oid)
            check(await b.post(f'/orders/{oid}/cancellation-requests', json={'reason':'x'}), 403)
            check(await s1.post(f'/orders/{oid}/cancellation-requests', json={'reason':'x'}), 403)
            submissions = await asyncio.gather(request(oid), request(oid))
            assert submissions[0]['cancellation_id'] == submissions[1]['cancellation_id']
            entry = submissions[0]
            assert (await request(oid))['cancellation_id'] == entry['cancellation_id']
            check(await a.post(f'/orders/{oid}/cancellation-requests', json={'reason':'different reason'}), 409)
            assert (await state(oid))[:4] == baseline[:4]
            check(await review(entry, c=a), 403)
            check(await s1.get(f'/orders/{oid}/cancellation-requests'), 403)
            check(await review(entry, 'rejected'))
            assert (await state(oid))[:4] == baseline[:4]
            entry = await request(oid)

            async def fail_sql_after_flush(db, *args, **kwargs):
                await db.flush()
                await db.execute(text('INSERT INTO order_items(order_id,quantity,price) VALUES(-1,1,1)'))

            for failure in (AsyncMock(side_effect=RuntimeError('audit unavailable')), fail_sql_after_flush):
                before = await state(oid)
                with monkeypatch.context() as patch:
                    patch.setattr(order_service, 'record_required_action', failure)
                    check(await review(entry), 500)
                assert await state(oid) == before
            approvals = await asyncio.gather(review(entry), review(entry, c=admin2))
            for response in approvals:
                check(response)
            after = await state(oid)
            assert after[0] == '已取消' and after[1] is not None and after[2] == baseline[2]
            stock_before = dict(baseline[3])
            assert dict(after[3])[p1['product_id']] == stock_before[p1['product_id']] + 2
            assert dict(after[3])[p2['product_id']] == stock_before[p2['product_id']] + 3
            check(await review(entry))
            assert await state(oid) == after
            check(await review(entry, 'rejected'), 409)
            check(await a.post(f'/orders/{oid}/cancellation-requests', json={'reason':'again'}), 409)
            check(await ship(oid,s1), 409)
            check(await admin.delete(f'/orders/{oid}'), 409)
            async with sessions() as db:
                audits = (await db.execute(select(AuditLog).where(AuditLog.target_id == str(oid), AuditLog.action == 'CANCELLATION_REVIEW'))).scalars().all()
                assert sum(event.after_data['decision'] == 'approved' for event in audits) == 1
            print('PASS buyer ownership / Admin-only review / request no stock change / reject-reapply / parallel approve exactly once / audit and SQL rollback')

            mixed = await order()
            waiting = await request(mixed)
            before = await state(mixed)
            with monkeypatch.context() as patch:
                patch.setattr(order_service, 'record_required_action', AsyncMock(side_effect=RuntimeError('audit unavailable')))
                check(await ship(mixed,s1), 500)
            assert await state(mixed) == before
            first = check(await ship(mixed,s1))
            assert first['status'] == '待出貨' and first['seller_shipment_status'] == '已出貨'
            assert 'total' not in first and 'user_id' not in first
            seller1_items = check(await s1.get(f'/order_items/by_order/{mixed}?sales=true'))['items']
            seller2_items = check(await s2.get(f'/order_items/by_order/{mixed}?sales=true'))['items']
            assert all(i['shipped_at'] is not None for i in seller1_items)
            assert all(i['shipped_at'] is None for i in seller2_items)
            check(await ship(mixed,s1))
            check(await a.post(f'/orders/{mixed}/cancellation-requests', json={'reason':'partial shipment'}), 409)
            check(await review(waiting), 409)
            check(await admin.patch(f'/orders/{mixed}/status', json={'status':'已完成'}), 409)
            check(await review(waiting,'rejected'))
            assert check(await ship(mixed,s2))['status'] == '已出貨'
            check(await a.post(f'/orders/{mixed}/cancellation-requests', json={'reason':'shipped'}), 409)
            check(await s1.patch(f'/orders/{mixed}/status', json={'status':'已完成'}), 403)
            before = await state(mixed)
            with monkeypatch.context() as patch:
                patch.setattr(order_service, 'record_required_action', fail_sql_after_flush)
                check(await admin.patch(f'/orders/{mixed}/status', json={'status':'已完成'}), 500)
            assert await state(mixed) == before
            assert check(await admin.patch(f'/orders/{mixed}/status', json={'status':'已完成'}))['status'] == '已完成'
            print('PASS mixed-Seller own shipment only / whole-order aggregation / partial shipment prevents cancellation / Admin-only completion / rollback')

            single = await order(mixed=False)
            check(await ship(single,s2), 403)
            check(await ship(single,s1))
            assert check(await admin.patch(f'/orders/{single}/status', json={'status':'已完成'}))['status'] == '已完成'
            seller_buy = await order(c=s1)
            seller_request = await request(seller_buy,c=s1)
            check(await review(seller_request))
            legacy = await request(1)
            check(await review(legacy), 409)
            assert (await state(1))[0] == '待付款'
            # 核准取消與第一個品項出貨競爭，不能既出貨又退庫存。
            racing = await order()
            racing_entry = await request(racing)
            before = await state(racing)
            approval, shipping = await asyncio.gather(review(racing_entry), ship(racing,s1))
            assert sorted([approval.status_code,shipping.status_code]) == [200,409]
            after = await state(racing)
            if approval.status_code == 200:
                assert after[0] == '已取消' and after[1] is not None
                assert all(item[3] is None for item in after[2])
            else:
                assert after[0] == '待出貨' and after[1] is None and after[3] == before[3]
                assert any(item[3] is not None for item in after[2])
            monkeypatch.setattr(order_service.settings,'APP_ENV','production')
            check(await a.post(f'/orders/1/cancellation-requests', json={'reason':'x'}),403)
            check(await review(legacy,'rejected'),403)
            check(await ship(single,s1),403)
            print('PASS single-Seller ownership / Seller buyer cancellation / unknown deduction blocked / shipping-approval race / environment gate')
    finally:
        env.app.dependency_overrides.clear()
        env.app.state.limiter.enabled = True
        await fresh.dispose()
        await engine.dispose()
