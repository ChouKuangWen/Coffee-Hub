"""Batch 6: real isolated MySQL; no .env, GCS or production data."""
import asyncio
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock
import httpx
import pytest
from sqlalchemy import select, text, func
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from tests.unit.test_account_permissions import isolated_app


@pytest.mark.skipif(not os.getenv("COFFEEHUB_TEST_MYSQL_URL"), reason="Isolated MySQL not configured")
def test_audit_security_mysql(isolated_app, monkeypatch):
    asyncio.run(scenario(isolated_app, monkeypatch))


async def scenario(env, monkeypatch):
    from app.models.users import Users
    from app.models.roles import Roles
    from app.models.audit_log import AuditLog
    from app.models.orders import Orders
    from app.services import audit_log_service as audit, user_service
    from app.core.security import hash_password
    from app.core.config import settings

    url = make_url(os.environ["COFFEEHUB_TEST_MYSQL_URL"])
    expected = Path(os.environ["COFFEEHUB_TEST_MYSQL_DATADIR"])
    assert url.host in ("localhost", "127.0.0.1") and url.port not in (None, 3306, 3307)
    assert expected.name.startswith("coffeehub-batch3-")
    name = "coffeehub_batch6_" + uuid4().hex
    bootstrap = create_async_engine(url.set(database=None))
    try:
        async with bootstrap.begin() as conn:
            assert Path((await conn.execute(text("SELECT @@datadir"))).scalar_one()).resolve() == expected.resolve()
            await conn.execute(text(f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4"))
    finally:
        await bootstrap.dispose()
    engine = create_async_engine(url.set(database=name))
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async def get_db():
        async with sessions() as db:
            yield db
    env.app.dependency_overrides[env.get_db] = get_db
    env.app.state.limiter.enabled = False
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda c: Users.metadata.create_all(c,
                tables=[t for key,t in Users.metadata.tables.items() if key != "audit_logs"]))
            # Start with the pre-Batch-6 table and a legacy sensitive event.
            await conn.execute(text("""CREATE TABLE audit_logs (
                id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id INT NULL, category VARCHAR(50) NOT NULL,
                action VARCHAR(100) NOT NULL, target_type VARCHAR(50), target_id VARCHAR(100), status VARCHAR(20),
                error_message TEXT, before_data JSON, after_data JSON, request_id VARCHAR(100),
                ip_address VARCHAR(45), user_agent TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB"""))
            await conn.execute(text("INSERT INTO audit_logs(category,action,status) VALUES('LEGACY','LEGACY','SUCCESS')"))
            for filename in ["001_account_lifecycle.sql", "002_simulated_checkout.sql", "003_order_lifecycle.sql",
                             "004_image_assets.sql", "005_audit_security.sql", "005_audit_security.sql"]:
                script = Path("../database/migrations", filename).read_text(encoding="utf-8")
                for statement in "\n".join(x for x in script.splitlines() if not x.lstrip().startswith("--")).split(";"):
                    if statement.strip():
                        await conn.execute(text(statement))
            assert tuple((await conn.execute(text("SELECT retention_class,expires_at,is_held FROM audit_logs WHERE id=1"))).one()) == ("UNCLASSIFIED", None, 0)
            assert (await conn.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='005_audit_security'"))).scalar_one() == 1
            script = Path("../database/init.sql").read_text(encoding="utf-8")
            script = "\n".join(x for x in script.splitlines() if not x.lstrip().startswith("--"))
            ddl = next(x for x in script.split(";") if re.match(r"\s*CREATE TABLE IF NOT EXISTS `audit_logs`", x))
            await conn.execute(text(ddl.replace("`audit_logs`", "`audit_fresh`", 1)))
            for table in ("audit_logs", "audit_fresh"):
                rows = (await conn.execute(text("SELECT COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT FROM information_schema.columns WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=:table AND COLUMN_NAME IN ('retention_class','expires_at','is_held') ORDER BY COLUMN_NAME"), {"table":table})).all()
                if table == "audit_logs":
                    upgraded = rows
                else:
                    assert upgraded == rows
        async with sessions() as db:
            db.add_all([Roles(role_id=i,name=n) for i,n in [(1,"Admin"),(2,"Seller"),(3,"Customer")]])
            await db.flush()
            db.add_all([Users(user_id=i,username=n,email=f"{n}@example.com",phone="0",address="private-address",
                role_id=role,password_hash=hash_password("test-only-value")) for i,n,role in [(1,"admin",1),(2,"seller",2),(3,"buyer",3)]])
            await db.commit()

        def client():
            return httpx.AsyncClient(transport=httpx.ASGITransport(env.app),base_url="https://testserver")
        def check(response, status=200):
            assert response.status_code == status, (response.status_code,response.text)
            return response.json()
        async def csrf(c):
            response = await c.get("/auth/csrf")
            token = check(response)["csrf_token"]
            c.headers["X-CSRF-Token"] = token
            return response
        async def count(action=None):
            async with sessions() as db:
                query = select(func.count()).select_from(AuditLog)
                if action:
                    query = query.where(AuditLog.action == action)
                return (await db.execute(query)).scalar_one()

        async with client() as admin, client() as buyer, client() as seller:
            check(await buyer.post("/auth/login",data={"username":"buyer@example.com","password":"test-only-value"}),403)
            response = await csrf(buyer)
            assert "httponly" in response.headers["set-cookie"].lower() and "secure" in response.headers["set-cookie"].lower()
            check(await buyer.post("/auth/login",data={"username":"buyer@example.com","password":"test-only-value"},headers={"Origin":"https://evil.example"}),403)
            check(await buyer.post("/auth/login",data={"username":"buyer@example.com","password":"test-only-value"},headers={"X-CSRF-Token":"forged"}),403)
            for c,n in [(admin,"admin"),(buyer,"buyer"),(seller,"seller")]:
                await csrf(c)
                check(await c.post("/auth/login",data={"username":f"{n}@example.com","password":"test-only-value"},headers={"Origin":"http://localhost:5173"}))
                await csrf(c)
            assert (await buyer.get("/auth/me")).headers.get("X-Request-ID")
            check(await buyer.get("/audit-logs"),403)
            check(await seller.get("/audit-logs"),403)
            before = await count("READ")
            check(await admin.get("/users/3"))
            assert await count("READ") == before + 1
            before = await count("READ")
            data = check(await admin.get("/audit-logs",params={"category":"SENSITIVE_READ","limit":1}))
            assert len(data["items"]) == 1 and await count("READ") == before + 1
            async with sessions() as db:
                rows = (await db.execute(select(AuditLog).where(AuditLog.category == "SENSITIVE_READ"))).scalars().all()
                assert all(r.retention_class == "HIGH_RISK" and r.expires_at.year == r.created_at.year+3 for r in rows)
                db.add(AuditLog(category="LEGACY",action="LEGACY",target_id="test-private-token",request_id="private-token",
                    before_data={"password":"test-private-password", "access_token":"test-private-token", "phone":"private-phone",
                                 "status":"test-private-token", "price":"test-private-token"},error_message="private-error"))
                await db.commit()
            response = await admin.get("/audit-logs",params={"category":"LEGACY"})
            check(response)
            assert all(secret not in response.text for secret in ["test-private-token","test-private-password","private-phone","private-error"])
            check(await admin.get("/audit-logs",params={"page":0}),422)
            check(await admin.get("/audit-logs",params={"category":"' OR 1=1 --"}))
            with monkeypatch.context() as patch:
                patch.setattr(audit,"record_required_action",AsyncMock(side_effect=RuntimeError("injected")))
                response = await admin.get("/users/3")
                check(response,503)
                assert "private-address" not in response.text
                check(await admin.get("/audit-logs"),503)
                check(await buyer.get("/users/1"),503)
            with monkeypatch.context() as patch:
                patch.setattr(user_service,"log_action",AsyncMock(side_effect=RuntimeError("injected")))
                check(await buyer.put("/users/3",json={"phone":"changed"}),500)
            assert check(await buyer.get("/users/3"))["phone"] == "0"

            at = datetime.now(timezone.utc).replace(tzinfo=None)
            async with sessions() as db:
                db.add_all([AuditLog(category="AUTH",action=action,retention_class="SECURITY",status="FAIL",
                    created_at=at-timedelta(days=100),expires_at=expiry,is_held=hold)
                    for action,expiry,hold in [("EXPIRED",at-timedelta(days=1),False),("HELD",at-timedelta(days=1),True),
                        ("FUTURE",at+timedelta(days=1),False)]])
                db.add(Orders(user_id=3,total=10))
                await db.commit()
            check(await admin.post("/audit-logs/cleanup",json={"dry_run":False}),403)
            assert check(await admin.post("/audit-logs/cleanup",json={}))["deleted"] == 0
            monkeypatch.setattr(settings,"AUDIT_DELETE_ENABLED",True,raising=False)  # Isolated DB only.
            with monkeypatch.context() as patch:
                patch.setattr(audit,"record_required_action",AsyncMock(side_effect=RuntimeError("injected")))
                check(await admin.post("/audit-logs/cleanup",json={"dry_run":False}),503)
            assert await count("EXPIRED") == 1
            assert check(await admin.post("/audit-logs/cleanup",json={"dry_run":False}))["deleted"] == 1
            assert await count("EXPIRED") == 0 and await count("HELD") == 1 and await count("FUTURE") == 1
            assert await count("LEGACY") == 2
            async with sessions() as db:
                assert (await db.execute(select(func.count()).select_from(Orders))).scalar_one() == 1

            check(await buyer.post("/auth/refresh-token"))
            check(await buyer.post("/auth/logout"))
            await csrf(buyer)
            check(await buyer.post("/auth/refresh-token"),401)
            check(await buyer.post("/auth/login",data={"username":"buyer@example.com","password":"test-only-value"}))
            await csrf(buyer)
            check(await admin.patch("/users/3/activation",json={"is_active":False}))
            check(await buyer.post("/auth/refresh-token"),401)
            check(await buyer.get("/auth/me"),401)
        print("PASS audit access/redaction/atomic rollback/retention/migration/CSRF/session revocation")
    finally:
        env.app.dependency_overrides.clear()
        env.app.state.limiter.enabled = True
        await engine.dispose()
