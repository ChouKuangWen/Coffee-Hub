"""Batch 2 精簡整合驗證；顯式指定本機獨立 MySQL 才執行，不載入 .env。

COFFEEHUB_TEST_MYSQL_URL: 只接受 loopback 且非 3306/3307 的專用實例。
COFFEEHUB_TEST_MYSQL_DATADIR: 必須與伺服器 @@datadir 一致。
每次建立獨立 coffeehub_batch2_* 資料庫；不刪資料、不碰既有 schema。
"""
import asyncio
import os
import re
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import select, text, func
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from tests.unit.test_account_permissions import isolated_app, csrf_client


@pytest.mark.skipif(not os.getenv("COFFEEHUB_TEST_MYSQL_URL"), reason="未指定獨立測試 MySQL")
def test_account_lifecycle_mysql(isolated_app, monkeypatch):
    asyncio.run(_scenario(isolated_app, monkeypatch))


async def _scenario(env, monkeypatch):
    from app.models.users import Users
    from app.models.roles import Roles
    from app.models.products import Products
    from app.models.orders import Orders
    from app.models.seller_application import SellerApplication
    from app.models.refresh_token import RefreshToken
    from app.models.audit_log import AuditLog
    from app.services import account_service
    from app.core.security import hash_password

    url = make_url(os.environ["COFFEEHUB_TEST_MYSQL_URL"])
    assert url.host in ("127.0.0.1", "localhost") and url.port not in (None, 3306, 3307)
    expected_dir = os.environ["COFFEEHUB_TEST_MYSQL_DATADIR"]
    assert Path(expected_dir).name.startswith(("coffeehub-batch2-", "coffeehub-batch3-"))
    db_name = "coffeehub_batch2_" + uuid4().hex
    bootstrap = create_async_engine(url.set(database=None))
    try:
        async with bootstrap.begin() as conn:
            datadir = (await conn.execute(text("SELECT @@datadir"))).scalar_one()
            assert Path(datadir).resolve() == Path(expected_dir).resolve()
            await conn.execute(text(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4"))
    finally:
        await bootstrap.dispose()
    engine = create_async_engine(url.set(database=db_name))
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def get_db():
        async with sessions() as session:
            yield session

    env.app.dependency_overrides[env.get_db] = get_db
    env.app.state.limiter.enabled = False
    try:
        # 真正驗證舊 users 的增量遷移，先保留一筆舊資料再執行版本化 SQL。
        async with engine.begin() as conn:
            await conn.run_sync(Roles.__table__.create)
            await conn.execute(text("INSERT INTO roles VALUES (1,'Admin'),(2,'Seller'),(3,'Customer')"))
            await conn.execute(text("""CREATE TABLE users (
                user_id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL, email VARCHAR(100) NOT NULL UNIQUE,
                phone VARCHAR(20) NOT NULL, address VARCHAR(255) NOT NULL,
                role_id INT NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(role_id) REFERENCES roles(role_id)) ENGINE=InnoDB"""))
            await conn.execute(text("""INSERT INTO users(username,password_hash,email,phone,address,role_id)
                VALUES('preserved','not-a-login-hash','preserved@example.com','0','test',3)"""))
            migration = Path("../database/migrations/001_account_lifecycle.sql").read_text(encoding="utf-8")
            sql = "\n".join(line for line in migration.splitlines() if not line.lstrip().startswith("--"))
            for statement in sql.split(";"):
                if statement.strip():
                    await conn.execute(text(statement))
            # 同一遷移重跑不應丟錯，亦不能重設帳號狀態或憑證版本。
            await conn.execute(text("UPDATE users SET is_active=FALSE,token_version=7 WHERE username='preserved'"))
            for statement in sql.split(";"):
                if statement.strip():
                    await conn.execute(text(statement))
            assert tuple((await conn.execute(text("SELECT is_active,token_version FROM users WHERE username='preserved'"))).one()) == (0, 7)
            assert (await conn.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='001_account_lifecycle'"))).scalar_one() == 1
            await conn.execute(text("UPDATE users SET is_active=TRUE,token_version=0 WHERE username='preserved'"))
            await conn.run_sync(Users.metadata.create_all)
            preserved = (await conn.execute(text("SELECT is_active,token_version FROM users WHERE username='preserved'"))).one()
            assert tuple(preserved) == (1, 0)
        print("PASS migration 001 preserves existing user")
        # 不執行 init.sql 中的 DROP／USE；只在另一空 DB 核對本批必要 DDL。
        fresh_name = db_name + '_fresh'
        async with engine.begin() as conn:
            await conn.execute(text(f'CREATE DATABASE `{fresh_name}` CHARACTER SET utf8mb4'))
        fresh = create_async_engine(url.set(database=fresh_name))
        try:
            async with fresh.begin() as conn:
                init = Path('../database/init.sql').read_text(encoding='utf-8')
                init = '\n'.join(line for line in init.splitlines() if not line.lstrip().startswith('--'))
                for statement in init.split(';'):
                    match = re.match(r'\s*CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?(\w+)', statement, re.I)
                    if match and match[1] in {'roles', 'users', 'seller_applications', 'schema_migrations'}:
                        await conn.execute(text(statement))
            column_query = text("""SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT,EXTRA
                FROM information_schema.columns WHERE TABLE_SCHEMA=DATABASE() AND
                (TABLE_NAME IN ('seller_applications','schema_migrations') OR
                 (TABLE_NAME='users' AND COLUMN_NAME IN ('is_active','token_version')))
                ORDER BY TABLE_NAME,ORDINAL_POSITION""")
            async with engine.connect() as upgraded, fresh.connect() as initial:
                assert (await upgraded.execute(column_query)).all() == (await initial.execute(column_query)).all()
        finally:
            await fresh.dispose()
        print('PASS migration rerun / preserved status-version / fresh and upgraded lifecycle schema match')
        async with sessions() as session:
            session.add(Users(username="admin", email="admin@example.com", password_hash=hash_password("test-only-value"),
                              phone="0", address="test", role_id=1))
            await session.commit()

        def client():
            return csrf_client(env.app)

        def check(response, code):
            assert response.status_code == code, (response.status_code, response.text)
            return response.json()

        async def login(c, email):
            c.cookies.clear()
            return check(await c.post("/auth/login", data={"username": email, "password": "test-only-value"}), 200)

        async def denied(c):
            check(await c.get("/auth/me"), 401)
            check(await c.post("/auth/refresh-token"), 401)

        async with client() as admin, client() as a, client() as b, client() as outsider:
            await login(admin, "admin@example.com")
            payload = dict(username="buyer", email="buyer@example.com", password="test-only-value", phone="0", address="test")
            for role in (1, 2):
                check(await a.post("/auth/register", json={**payload, "role_id": role}), 422)
            check(await a.post("/auth/register", json=payload), 200)
            first = await login(a, payload["email"])
            user_id = first["user_id"]
            await login(b, payload["email"])
            check(await a.put(f"/users/{user_id}", json={"phone": "0911111111"}), 200)
            check(await a.put(f"/users/{user_id}", json={"role_id": 2}), 422)
            check(await a.get("/users/1"), 403)
            check(await a.get("/users/"), 403)
            # 一般登出只撤銷一個會話，包括刷新前的舊 access。
            old_access = first["access_token"]
            check(await a.post("/auth/refresh-token"), 200)
            check(await a.post("/auth/logout"), 200)
            a.cookies.set("access_token", old_access)
            await denied(a)
            check(await b.get("/auth/me"), 200)
            check(await b.post("/auth/refresh-token"), 200)
            await login(a, payload["email"])
            print("PASS Batch 1 regression / single-device logout")

            app = check(await a.post("/users/seller-applications"), 201)
            assert check(await a.get("/auth/me"), 200)["role_id"] == 3
            check(await a.get('/cart'), 200)
            check(await a.post("/users/seller-applications"), 409)
            check(await a.patch(f"/users/seller-applications/{app['application_id']}", json={"decision": "approved"}), 403)
            check(await admin.patch(f"/users/seller-applications/{app['application_id']}", json={"decision": "rejected"}), 200)
            assert check(await a.get("/auth/me"), 200)["role_id"] == 3
            submissions = await asyncio.gather(*[a.post("/users/seller-applications") for _ in range(2)])
            assert sorted(r.status_code for r in submissions) == [201, 409]
            app = next(r.json() for r in submissions if r.status_code == 201)
            check(await outsider.post('/auth/register', json={**payload, 'username': 'other', 'email': 'other@example.com'}), 200)
            other_login = await login(outsider, 'other@example.com')
            assert check(await outsider.get('/users/seller-applications'), 200) == []
            endpoint = f"/users/seller-applications/{app['application_id']}"

            with monkeypatch.context() as patch:
                patch.setattr(account_service, "record_required_action", AsyncMock(side_effect=RuntimeError("audit unavailable")))
                check(await admin.patch(endpoint, json={"decision": "approved"}), 500)
            async with sessions() as session:
                assert (await session.get(Users, user_id)).role_id == 3
                assert (await session.get(SellerApplication, app["application_id"])).status == "pending"
            check(await a.get("/auth/me"), 200)
            check(await b.post("/auth/refresh-token"), 200)
            # 同一申請同時審核只能一次成功。
            reviews = await asyncio.gather(*[admin.patch(endpoint, json={"decision": "approved"}) for _ in range(2)])
            assert sorted(r.status_code for r in reviews) == [200, 409]
            await denied(a)
            await denied(b)
            print("PASS request/reject/reapply / non-Admin denial / audit rollback / concurrent approval / all-device revocation")

            seller_a = await login(a, payload["email"])
            seller_b = await login(b, payload["email"])
            assert seller_a["user_id"] == user_id and seller_a["role_id"] == 2
            check(await a.post("/users/seller-applications"), 403)
            async with sessions() as session:
                product = Products(name="test bean", price=100, stock=5, owner_id=user_id,
                                   main_image="https://example.com/test.png", is_active=True)
                order = Orders(user_id=user_id, total=100)
                session.add_all([product, order])
                await session.commit()
                product_id, order_id = product.product_id, order.order_id
                version = (await session.get(Users, user_id)).token_version
            activation = f"/users/{user_id}/activation"
            check(await a.patch(activation, json={"is_active": False}), 403)
            with monkeypatch.context() as patch:
                patch.setattr(account_service, "record_required_action", AsyncMock(side_effect=RuntimeError("audit unavailable")))
                check(await admin.patch(activation, json={"is_active": False}), 500)
            async with sessions() as session:
                assert (await session.get(Users, user_id)).is_active
                assert (await session.get(Users, user_id)).token_version == version
                assert (await session.get(Products, product_id)).is_active
            check(await a.get("/auth/me"), 200)
            # 舊 DELETE 必須停用；同時嘗試上架不得留下仍上架的停用 Seller 商品。
            product_change, disable = await asyncio.gather(
                a.patch(f'/products/{product_id}', json={'is_active': True}),
                admin.delete(f"/users/{user_id}"))
            assert product_change.status_code in (200, 401, 403)
            check(disable, 200)
            await denied(a)
            await denied(b)
            check(await admin.patch(f'/products/{product_id}', json={'is_active': True}), 409)
            check(await outsider.post("/auth/login", data={"username": payload["email"], "password": "test-only-value"}), 401)
            async with sessions() as session:
                assert not (await session.get(Users, user_id)).is_active
                product = await session.get(Products, product_id)
                assert not product.is_active and product.main_image == "https://example.com/test.png"
                assert await session.get(Orders, order_id) is not None
                assert (await session.execute(select(func.count()).select_from(RefreshToken).where(
                    RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False)))).scalar_one() == 0
            check(await admin.patch(activation, json={"is_active": True}), 200)
            await denied(a)
            await denied(b)
            await login(a, payload["email"])
            check(await a.get("/auth/me"), 200)
            async with sessions() as session:
                assert not (await session.get(Products, product_id)).is_active
                history = (await session.execute(select(AuditLog).where(AuditLog.category == "ACCOUNT"))).scalars().all()
                actions = {event.action for event in history}
                assert {"SELLER_APPLY", "SELLER_REVIEW", "USER_DISABLE", "USER_ENABLE"} <= actions
                assert not any("access_token" in str(event.after_data) or "test-only-value" in str(event.after_data) for event in history)
            print("PASS Seller disable atomicity / login denial / history and image retention / re-enable without resurrection / durable audit")
            other_id = other_login['user_id']
            check(await admin.patch(f'/users/{other_id}/activation', json={'is_active': False}), 200)
            await denied(outsider)
            check(await outsider.post('/auth/login', data={'username': 'other@example.com', 'password': 'test-only-value'}), 401)
            check(await admin.patch(f'/users/{other_id}/activation', json={'is_active': True}), 200)
            await denied(outsider)
            await login(outsider, 'other@example.com')
            check(await outsider.get('/auth/me'), 200)
            print('PASS Customer disable / re-enable / application data isolation / duplicate concurrent application')
    finally:
        env.app.dependency_overrides.clear()
        env.app.state.limiter.enabled = True
        await engine.dispose()
