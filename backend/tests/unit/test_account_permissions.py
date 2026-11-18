"""第一批安全回歸：真實路由／Service，DB 與外部設定使用隔離替身。"""
import asyncio
import importlib
import secrets
import sys
from datetime import datetime, timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import IntegrityError


@pytest.fixture(scope="module")
def isolated_app():
    # 在匯入任何應用模組前隔離設定／DB／GCS，不讀 .env、不建立雲端 Client。
    with pytest.MonkeyPatch.context() as patch:
        config = ModuleType("app.core.config")
        config.settings = SimpleNamespace(
            SECRET_KEY=secrets.token_urlsafe(48), ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=15, REFRESH_TOKEN_EXPIRE_DAYS=7,
        )
        base = ModuleType("app.models.base")
        base.Base = declarative_base()

        async def get_db():
            raise AssertionError("測試不得開啟外部資料庫")
            yield

        base.get_db = get_db
        storage = ModuleType("app.core.gcp_storage")
        storage.gcs_storage = SimpleNamespace(upload_file=Mock())
        patch.setitem(sys.modules, "app.core.config", config)
        patch.setitem(sys.modules, "app.models.base", base)
        patch.setitem(sys.modules, "app.core.gcp_storage", storage)
        main = importlib.import_module("app.main")
        auth = importlib.import_module("app.services.auth_service")
        users = importlib.import_module("app.services.user_service")
        deps = importlib.import_module("app.dependencies")
        token = importlib.import_module("app.core.jwt")
        yield SimpleNamespace(app=main.app, auth=auth, users=users, deps=deps,
                              token=token, get_db=get_db)
        main.app.dependency_overrides.clear()


@pytest.fixture
def context(isolated_app, monkeypatch):
    env = isolated_app
    user = SimpleNamespace(user_id=7, role_id=3, username="customer",
                           email="customer@example.com", phone="0900000000",
                           address="測試地址", created_at=datetime(2026, 1, 1))
    result = Mock()
    result.scalars.return_value.first.return_value = user
    db = SimpleNamespace(execute=AsyncMock(return_value=result), add=Mock(),
                         flush=AsyncMock(), commit=AsyncMock(), rollback=AsyncMock())

    async def database():
        yield db

    env.app.dependency_overrides[env.get_db] = database
    env.app.state.limiter.enabled = False
    monkeypatch.setattr(env.auth, "log_action", AsyncMock())
    monkeypatch.setattr(env.users, "log_action", AsyncMock())
    client = TestClient(env.app, base_url="https://testserver")
    access, _ = env.token.create_access_token({"user_id": 7, "role_id": 3})
    client.cookies.set("access_token", access)
    # 驗證仍執行真實 JWT 簽章／期限檢查；只替換撤銷紀錄查詢。
    monkeypatch.setattr(env.token, "is_jti_blacklisted", AsyncMock(return_value=False))
    yield SimpleNamespace(env=env, client=client, db=db, result=result, user=user)
    client.close()
    env.app.state.limiter.enabled = True


def registration():
    return dict(username="newcustomer", email="new@example.com", password="test-only-value",
                phone="0900000000", address="測試地址")


@pytest.mark.parametrize("role", [1, 2])
def test_registration_rejects_privileged_roles(context, role):
    response = context.client.post("/auth/register", json={**registration(), "role_id": role})
    assert response.status_code == 422
    context.db.commit.assert_not_awaited()


def test_registration_defaults_to_customer_and_hashes_password(context):
    context.result.scalars.return_value.first.return_value = None

    async def commit():
        context.db.add.call_args.args[0].user_id = 8

    context.db.commit.side_effect = commit
    response = context.client.post("/auth/register", json=registration())
    assert response.status_code == 200
    saved = context.db.add.call_args.args[0]
    assert saved.role_id == 3
    assert context.env.auth.verify_password(registration()["password"], saved.password_hash)
    assert "password" not in response.json()


def test_duplicate_registration_is_rejected(context):
    assert context.client.post("/auth/register", json=registration()).status_code == 400
    context.db.commit.assert_not_awaited()


@pytest.mark.parametrize("field,value", [("role_id", 1), ("role_id", 2),
                                         ("password_hash", "forged"), ("user_id", 9),
                                         ("email", None)])
def test_update_rejects_protected_or_null_fields(context, field, value):
    response = context.client.put("/users/7", json={field: value})
    assert response.status_code == 422
    assert context.user.role_id == 3
    context.db.commit.assert_not_awaited()


def test_customer_can_update_own_profile_without_changing_role(context):
    response = context.client.put("/users/7", json={"phone": "0911111111", "address": "<b>新地址</b>"})
    assert response.status_code == 200
    assert response.json()["phone"] == "0911111111"
    assert response.json()["address"] == "新地址"
    assert response.json()["username"] == "customer"
    assert response.json()["role_id"] == 3
    context.db.commit.assert_awaited_once()
    context.env.users.log_action.assert_awaited_once()


def test_username_update_and_empty_name_validation(context):
    assert context.client.put("/users/7", json={"username": "newname"}).status_code == 200
    assert context.user.username == "newname"
    assert context.client.put("/users/7", json={"username": "<b></b>"}).status_code == 422


def test_cross_account_read_update_and_list_are_forbidden(context):
    assert context.client.get("/users/8").status_code == 403
    assert context.client.put("/users/8", json={"phone": "x"}).status_code == 403
    assert context.client.get("/users/").status_code == 403
    assert context.client.post("/users/", json=registration()).status_code == 403
    context.db.commit.assert_not_awaited()


def test_admin_can_update_profile_but_not_grant_roles_through_profile(context):
    context.user.role_id = 1
    access, _ = context.env.token.create_access_token({"user_id": 7, "role_id": 1})
    context.client.cookies.set("access_token", access)
    target = SimpleNamespace(**{**vars(context.user), "user_id": 8, "role_id": 3})
    target_result = Mock()
    target_result.scalars.return_value.first.return_value = target
    context.db.execute.side_effect = [context.result, target_result, target_result, target_result,
                                      context.result]
    response = context.client.put("/users/8", json={"phone": "0901234567"})
    assert response.status_code == 200
    assert response.json()["user_id"] == 8
    assert response.json()["phone"] == "0901234567"
    assert context.client.put("/users/8", json={"role_id": 2}).status_code == 422


def test_update_unique_conflict_rolls_back(context):
    context.db.flush.side_effect = IntegrityError("test", {}, Exception("duplicate"))
    response = context.client.put("/users/7", json={"email": "taken@example.com"})
    assert response.status_code == 409
    context.db.rollback.assert_awaited_once()
    context.db.commit.assert_not_awaited()


def test_missing_profile_returns_404(context, monkeypatch):
    monkeypatch.setattr(context.env.users, "get_user_by_id", AsyncMock(return_value=None))
    assert context.client.get("/users/7").status_code == 404
    assert context.client.put("/users/7", json={"phone": "x"}).status_code == 404


def test_stale_cookie_bearer_and_optional_auth_never_overwrite_database_role(context):
    old_token, _ = context.env.token.create_access_token({"user_id": 7, "role_id": 1})
    context.client.cookies.set("access_token", old_token)
    assert context.client.get("/auth/me").status_code == 401
    assert context.user.role_id == 3
    request = Mock(state=SimpleNamespace())
    with pytest.raises(HTTPException) as exc:
        asyncio.run(context.env.deps.get_current_user(request, old_token, context.db))
    assert exc.value.status_code == 401
    assert asyncio.run(context.env.deps.get_current_user_from_cookie_optional(
        request, old_token, context.db)) is None
    assert context.user.role_id == 3


def test_login_and_me_still_work(context, monkeypatch):
    context.user.password_hash = context.env.auth.hash_password("test-only-value")
    context.user.role = SimpleNamespace(name="Customer")
    monkeypatch.setattr(context.env.auth, "create_refresh_token", AsyncMock(return_value="test-refresh"))
    response = context.client.post("/auth/login", data={"username": context.user.email, "password": "test-only-value"})
    assert response.status_code == 200
    assert response.json()["role_id"] == 3
    assert "httponly" in response.headers.get_list("set-cookie")[0].lower()
    assert context.client.get("/auth/me").status_code == 200
    assert context.client.post("/auth/login", data={"username": context.user.email, "password": "wrong"}).status_code == 401


def test_invalid_token_and_missing_cookie_are_unauthorized(context):
    context.client.cookies.clear()
    assert context.client.get("/auth/me").status_code == 401
    context.client.cookies.set("access_token", "invalid")
    assert context.client.get("/auth/me").status_code == 401


def test_expired_token_and_malformed_identity_are_unauthorized(context):
    expired, _ = context.env.token.create_access_token(
        {"user_id": 7, "role_id": 3}, expires_delta=timedelta(seconds=-10))
    context.client.cookies.set("access_token", expired)
    assert context.client.get("/auth/me").status_code == 401
    malformed, _ = context.env.token.create_access_token({"user_id": "invalid", "role_id": 3})
    context.client.cookies.set("access_token", malformed)
    assert context.client.get("/auth/me").status_code == 401


def test_admin_create_is_customer_only(context):
    context.user.role_id = 1
    access, _ = context.env.token.create_access_token({"user_id": 7, "role_id": 1})
    context.client.cookies.set("access_token", access)
    assert context.client.post("/users/", json={**registration(), "role_id": 2}).status_code == 422

    async def commit():
        saved = context.db.add.call_args.args[0]
        saved.user_id = 8
        saved.created_at = datetime(2026, 1, 1)
        context.result.scalars.return_value.first.return_value = saved

    context.db.commit.side_effect = commit
    response = context.client.post("/users/", json=registration())
    assert response.status_code == 200
    assert response.json()["role_id"] == 3
    assert context.db.add.call_args.args[0].role_id == 3


def test_application_health_in_isolated_environment(context):
    assert context.client.get("/health").json() == {"status": "ok"}
    context.db.execute.assert_not_awaited()
