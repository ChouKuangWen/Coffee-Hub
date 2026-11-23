"""手動執行的隔離 Docker 驗收；拒絕既有業務 DB，不得對開發／正式環境執行。"""
import asyncio
import json
import os
import re
from pathlib import Path

import asyncmy
import httpx


def statements(script):
    return [s.strip() for s in "\n".join(
        line for line in script.splitlines() if not line.lstrip().startswith("--")
    ).split(";") if s.strip()]


async def execute(cursor, script):
    for statement in statements(script):
        await cursor.execute(statement)


async def scalar(cursor, sql):
    await cursor.execute(sql)
    return (await cursor.fetchone())[0]


async def upgrade(cursor, start=1):
    for path in sorted(Path("/database/migrations").glob("*.sql")):
        if int(path.name[:3]) >= start:
            await execute(cursor, path.read_text(encoding="utf-8"))


async def old_database(cursor, name, omit_audit=False):
    assert name in ("coffeehub_phase1_legacy", "coffeehub_phase1_interrupted")
    script = Path("/database/legacy.sql").read_text(encoding="utf-8")
    script = script.replace("member_order_management_backend_system", name)
    for statement in statements(script):
        if omit_audit and re.search(r"CREATE TABLE IF NOT EXISTS `audit_logs`", statement):
            continue
        await cursor.execute(statement)
    await cursor.execute("INSERT INTO roles(role_id,name) VALUES(1,'Admin'),(2,'Seller'),(3,'Customer')")
    await cursor.execute("INSERT INTO users(user_id,username,password_hash,email,phone,address,role_id) VALUES(1,'legacy-seller','test-hash','seller@example.com','0','test',2),(2,'legacy-buyer','test-hash','buyer@example.com','0','test',3)")
    await cursor.execute("INSERT INTO products(product_id,name,price,stock,owner_id,main_image) VALUES(1,'legacy-product',21,7,1,'https://example.invalid/legacy.jpg')")
    await cursor.execute("INSERT INTO orders(order_id,user_id,total) VALUES(1,2,42)")
    await cursor.execute("INSERT INTO order_items(order_item_id,order_id,product_id,quantity,price) VALUES(1,1,1,2,21)")
    if not omit_audit:
        await cursor.execute("INSERT INTO audit_logs(category,action,status) VALUES('LEGACY','LEGACY','SUCCESS')")


async def preserved(cursor):
    await cursor.execute("SELECT username,is_active,token_version FROM users WHERE user_id=2")
    assert tuple(await cursor.fetchone()) == ("legacy-buyer", 1, 0)
    await cursor.execute("SELECT name,stock,main_image FROM products WHERE product_id=1")
    assert tuple(await cursor.fetchone()) == ("legacy-product", 7, "https://example.invalid/legacy.jpg")
    await cursor.execute("SELECT quantity,price,product_name,seller_id,shipped_at FROM order_items WHERE order_item_id=1")
    row = await cursor.fetchone()
    assert row[0] == 2 and row[1] == 21 and row[2:] == (None, None, None)
    await cursor.execute("SELECT total,stock_deducted,stock_returned_at FROM orders WHERE order_id=1")
    assert tuple(await cursor.fetchone()) == (42, 0, None)
    assert await scalar(cursor, "SELECT COUNT(*) FROM schema_migrations") == 5


async def column_signature(cursor):
    await cursor.execute("SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT FROM information_schema.columns WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,COLUMN_NAME")
    return await cursor.fetchall()


async def live_auth(cursor):
    # 真正 Uvicorn + app.models.base，不使用 ASGITransport 或設定／DB 替身。
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8080", follow_redirects=True) as client:
        def check(response, status=200):
            assert response.status_code == status, (response.status_code, response.url.path)
            return response.json()
        async def csrf():
            client.headers["X-CSRF-Token"] = check(await client.get("/auth/csrf"))["csrf_token"]
        check(await client.get("/health"))
        await csrf()
        data = {"username": "phase1-live", "email": "phase1-live@example.com",
                "password": "phase1-test-only-value", "phone": "0", "address": "test"}
        check(await client.post("/auth/register", json=data))
        check(await client.post("/auth/login", data={"username": data["email"], "password": data["password"]}))
        await csrf()  # 登入後 CSRF 綁定 Refresh 會話。
        assert check(await client.get("/auth/me"))["role_id"] == 3
        check(await client.post("/auth/refresh-token"))
        client.headers.pop("X-CSRF-Token")
        check(await client.post("/auth/logout"), 403)
        await csrf()
        check(await client.post("/auth/logout"))
        check(await client.get("/auth/me"), 401)
        assert await scalar(cursor, "SELECT COUNT(*) FROM refresh_tokens WHERE is_revoked=TRUE") == 1
        assert await scalar(cursor, "SELECT COUNT(*) FROM audit_logs WHERE action='LOGIN'") >= 1


async def main():
    assert os.environ["APP_ENV"] == "test"
    assert os.environ["PHASE1_RUN_ID"].startswith("coffeehub-phase1-")
    assert os.environ["DB_HOST"] == "127.0.0.1" and os.environ["DB_PORT"] == "33381"
    assert os.environ["IMAGE_STORAGE_ENABLED"] == "false"
    assert os.environ["IMAGE_DELETE_ENABLED"] == "false"
    conn = await asyncmy.connect(host="127.0.0.1", port=33381, user="root",
                                password=os.environ["DB_PASSWORD"], charset="utf8mb4", autocommit=True)
    results = {}
    try:
        async with conn.cursor() as cursor:
            assert Path(await scalar(cursor, "SELECT @@datadir")).resolve() == Path("/var/lib/mysql/coffeehub-batch3-phase1")
            await cursor.execute("SHOW DATABASES")
            allowed = {"mysql", "information_schema", "performance_schema", "sys", "coffeehub_phase1"}
            assert {r[0] for r in await cursor.fetchall()} <= allowed, "Existing DB detected; abort before init.sql"
            results["mysql_version"] = await scalar(cursor, "SELECT VERSION()")
            await execute(cursor, Path("/database/init.sql").read_text(encoding="utf-8"))
            assert await scalar(cursor, "SELECT COUNT(*) FROM schema_migrations") == 5
            fresh_columns = await column_signature(cursor)
            await upgrade(cursor)  # 已有 001～005 標記，存在性檢查不重複新增。
            assert fresh_columns == await column_signature(cursor)
            results["fresh_init_and_migration_rerun"] = "PASS"

            await old_database(cursor, "coffeehub_phase1_legacy")
            await upgrade(cursor)
            await preserved(cursor)
            await cursor.execute("SELECT retention_class,expires_at,is_held FROM audit_logs WHERE action='LEGACY'")
            assert tuple(await cursor.fetchone()) == ("UNCLASSIFIED", None, 0)
            assert fresh_columns == await column_signature(cursor), "Fresh/upgraded column schema differs"
            await upgrade(cursor)
            await preserved(cursor)
            assert await scalar(cursor, "SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='orders' AND index_name='uq_orders_checkout' AND non_unique=0") == 2
            assert await scalar(cursor, "SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_schema=DATABASE() AND table_name='order_items' AND column_name='seller_id' AND referenced_table_name='users'") == 1
            results["legacy_upgrade_preservation_schema_indexes_rerun"] = "PASS"

            await old_database(cursor, "coffeehub_phase1_interrupted", omit_audit=True)
            for name in ("001_account_lifecycle.sql", "002_simulated_checkout.sql"):
                await execute(cursor, Path("/database/migrations", name).read_text(encoding="utf-8"))
            try:
                await execute(cursor, Path("/database/migrations/003_order_lifecycle.sql").read_text(encoding="utf-8"))
            except asyncmy.errors.ProgrammingError:
                assert await scalar(cursor, "SELECT COUNT(*) FROM schema_migrations WHERE version='003_order_lifecycle'") == 0
                assert await scalar(cursor, "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='orders' AND column_name='stock_deducted'") == 1
            else:
                raise AssertionError("Missing audit table should fail migration 003")
            legacy = Path("/database/legacy.sql").read_text(encoding="utf-8")
            audit_ddl = next(s for s in statements(legacy) if re.search(r"CREATE TABLE IF NOT EXISTS `audit_logs`", s))
            await cursor.execute(audit_ddl)
            await upgrade(cursor, start=3)
            await preserved(cursor)
            results["migration_failure_no_false_marker_and_resumable_ddl"] = "PASS"

            await cursor.execute("USE member_order_management_backend_system")
            await cursor.execute("INSERT INTO roles(role_id,name) VALUES(1,'Admin'),(2,'Seller'),(3,'Customer')")
            await live_auth(cursor)
            results["live_uvicorn_mysql_register_login_refresh_logout_csrf"] = "PASS"
    finally:
        await conn.ensure_closed()
    print(json.dumps(results))  # 僅輸出結果／版本，不輸出測試憑證。


if __name__ == "__main__":
    asyncio.run(main())
