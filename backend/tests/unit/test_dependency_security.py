"""必要相依安全回歸：不讀 .env、不連線雲端或資料庫。"""
import base64
import hashlib
import hmac
import json
from unittest.mock import AsyncMock
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient
from tests.unit.test_account_permissions import isolated_app


def test_hmac_configuration_rejects_public_key_encodings():
    from app.core.security import validate_jwt_configuration
    public = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
    der = public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    pem = public.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    for value in (der, base64.b64encode(der).decode(), pem, b""):
        with pytest.raises(ValueError):
            validate_jwt_configuration("HS256", value)
    validate_jwt_configuration("HS256", "a-test-only-random-shaped-shared-key")
    with pytest.raises(ValueError):
        validate_jwt_configuration("none", "test")


def test_configuration_rejects_all_other_algorithms():
    from app.core.security import validate_jwt_configuration
    for algorithm in ("HS384", "HS512", "RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "none"):
        with pytest.raises(ValueError):
            validate_jwt_configuration(algorithm, "test-only-key")


def test_hs256_verifier_rejects_public_key_forgery(isolated_app, monkeypatch):
    """攻擊者以 DER 公鑰偽造 HMAC；必須無法通過既有 HS256 共享金鑰驗證。"""
    import jwt

    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private.public_key()
    der = public.public_bytes(serialization.Encoding.DER,
                              serialization.PublicFormat.SubjectPublicKeyInfo)
    payload = {"sub": "1", "jti": "test", "token_type": "access", "sid": "test",
               "version": 0, "exp": 4102444800}
    legitimate = jwt.encode(payload, isolated_app.token.SECRET_KEY, algorithm="HS256")
    assert isolated_app.token.decode_token(legitimate, "access")["sub"] == "1"
    # PyJWT 自己也會拒絕以 DER 公鑰簽發 HMAC；攻擊者不受函式庫限制。
    encode = lambda value: base64.urlsafe_b64encode(value).rstrip(b"=")
    message = b".".join(encode(json.dumps(value).encode()) for value in
                        ({"alg": "HS256", "typ": "JWT"}, payload))
    forged = (message + b"." + encode(hmac.new(der, message, hashlib.sha256).digest())).decode()
    with pytest.raises(HTTPException) as exc:
        isolated_app.token.decode_token(forged, "access")
    assert exc.value.status_code == 401


def test_fixed_algorithm_and_cookie_csrf_cannot_be_bypassed(isolated_app, monkeypatch):
    import jwt
    from app.core import browser_security
    token = jwt.encode({"sub":"1", "jti":"test", "token_type":"access", "sid":"test", "version":0,
                        "exp":4102444800}, isolated_app.token.SECRET_KEY, algorithm="HS512")
    with pytest.raises(HTTPException) as exc:
        isolated_app.token.decode_token(token, "access")
    assert exc.value.status_code == 401
    monkeypatch.setattr(browser_security, "persist_denial", AsyncMock())
    with TestClient(isolated_app.app, base_url="https://testserver") as client:
        client.cookies.set("access_token", "cookie-session")
        response = client.post("/auth/logout", headers={"Authorization":"Bearer arbitrary"})
        assert response.status_code == 403 and response.json()["code"] == "CSRF_REJECTED"


def test_urlencoded_field_limit_is_enforced():
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    async def parse(request):
        form = await request.form(max_fields=2)
        return JSONResponse({"count":len(form)})
    with TestClient(Starlette(routes=[Route("/form", parse, methods=["POST"])])) as client:
        assert client.post("/form", data={"username":"test", "password":"test"}).status_code == 200
        assert client.post("/form", data={"a":"1", "b":"2", "c":"3"}).status_code == 400
