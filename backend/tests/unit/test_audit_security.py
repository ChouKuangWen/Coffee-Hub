from datetime import datetime, timedelta
import pytest
from tests.unit.test_account_permissions import isolated_app


def test_retention_calendar_and_unknown_protection(isolated_app):
    from app.services.audit_log_service import retention, safe_data
    at = datetime(2024, 2, 29)
    assert retention("ORDER", "CANCEL", at) == ("HIGH_RISK", datetime(2027, 2, 28))
    assert retention("SENSITIVE_READ", "READ", at)[0] == "HIGH_RISK"
    assert retention("IMAGE", "CLEANUP", at) == ("BUSINESS", datetime(2025, 2, 28))
    assert retention("AUTH", "LOGIN_FAILED", at) == ("SECURITY", at + timedelta(days=90))
    assert retention("UNKNOWN", "UNKNOWN", at) == ("UNCLASSIFIED", None)
    data = safe_data({"password":"private", "access_token":"private", "phone":"private", "role_id":2,
                      "status":"private", "changed_fields":["email","private"], "price":"12.50"})
    assert "private" not in str(data) and data["role_id"] == 2 and data["price"] == "12.50"


def test_signed_csrf_tampering_expiry_and_cookie_config(isolated_app, monkeypatch):
    from app.core import browser_security as browser
    token = browser.new_csrf()
    assert browser.valid_csrf(token, token)
    assert not browser.valid_csrf(token, "forged")
    assert not browser.valid_csrf("forged", "forged")
    assert not browser.valid_csrf("é", "é")
    bound = browser.new_csrf("session-one")
    assert browser.valid_csrf(bound, bound, "session-one")
    assert not browser.valid_csrf(bound, bound, "session-two")
    assert not browser.valid_csrf(token, token, "session-one")
    original = browser.time.time()
    monkeypatch.setattr(browser.time,"time",lambda:original + 3601)
    assert not browser.valid_csrf(token, token)
    monkeypatch.setattr(browser.settings,"COOKIE_SECURE",False,raising=False)
    monkeypatch.setattr(browser.settings,"COOKIE_SAMESITE","none",raising=False)
    with pytest.raises(ValueError):
        browser.cookie_options()


def test_validation_omits_password_input(isolated_app):
    from fastapi.testclient import TestClient
    async def no_database():
        yield None
    isolated_app.app.dependency_overrides[isolated_app.get_db] = no_database
    isolated_app.app.state.limiter.enabled = False
    try:
        with TestClient(isolated_app.app, base_url="https://testserver") as client:
            token = client.get("/auth/csrf").json()["csrf_token"]
            response = client.post("/auth/register", headers={"X-CSRF-Token":token},
                json={"password":{"private":"never-echo-this"}})
            assert response.status_code == 422
            assert "never-echo-this" not in response.text and '"input"' not in response.text
    finally:
        isolated_app.app.dependency_overrides.clear()
        isolated_app.app.state.limiter.enabled = True


def test_asyncmy_nested_mapping_is_escaped_as_a_value():
    """Regression for GHSA-qhqw-rrw9-25rm; no connection or SQL execution."""
    import asyncio
    from asyncmy.connection import Connection
    from asyncmy.cursors import Cursor

    async def scenario():
        connection = Connection()
        connection.server_status = 0
        try:
            payload = {"attacker' OR 1=1 --": "untrusted"}
            statement = Cursor(connection).mogrify("SELECT %s", (payload,))
            assert statement == "SELECT " + connection.escape(str(payload))
            assert statement.startswith("SELECT '") and statement.endswith("'")
        finally:
            await connection.ensure_closed()
    asyncio.run(scenario())
