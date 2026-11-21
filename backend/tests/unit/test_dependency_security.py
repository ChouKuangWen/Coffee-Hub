"""必要相依安全回歸：不讀 .env、不連線雲端或資料庫。"""
import base64
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


def test_ecdsa_cannot_fall_back_to_python_ecdsa(monkeypatch):
    from app.core.security import validate_jwt_configuration
    from cryptography.hazmat.primitives.asymmetric import ec
    from jose import jwk, jwt
    from jose.backends.ecdsa_backend import ECDSAECKey
    validate_jwt_configuration("ES256", "not-inspected-by-provider-check")
    private = ec.generate_private_key(ec.SECP256R1())
    pem = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
    public = private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    signed = jwt.encode({"sub":"test"}, pem, algorithm="ES256")
    assert jwt.decode(signed, public, algorithms=["ES256"])["sub"] == "test"
    monkeypatch.setitem(jwk.ALGORITHMS.KEYS, "ES256", ECDSAECKey)
    with pytest.raises(ValueError):
        validate_jwt_configuration("ES256", "test")


def test_rsa_verifier_rejects_hmac_public_key_forgery(isolated_app, monkeypatch):
    """重現公告中的 DER 公鑰當作 HMAC 密鑰；固定 RSA 驗證必須拒絕。"""
    from jose import jwt

    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private.public_key()
    der = public.public_bytes(serialization.Encoding.DER,
                              serialization.PublicFormat.SubjectPublicKeyInfo)
    pem = public.public_bytes(serialization.Encoding.PEM,
                              serialization.PublicFormat.SubjectPublicKeyInfo)
    signing_key = private.private_bytes(serialization.Encoding.PEM,
                                        serialization.PrivateFormat.PKCS8,
                                        serialization.NoEncryption())
    payload = {"sub": "1", "jti": "test", "token_type": "access", "sid": "test",
               "version": 0, "exp": 4102444800}
    monkeypatch.setattr(isolated_app.token, "ALGORITHM", "RS256")
    monkeypatch.setattr(isolated_app.token, "SECRET_KEY", pem)
    legitimate = jwt.encode(payload, signing_key, algorithm="RS256")
    assert isolated_app.token.decode_token(legitimate, "access")["sub"] == "1"
    forged = jwt.encode(payload, der, algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        isolated_app.token.decode_token(forged, "access")
    assert exc.value.status_code == 401


def test_fixed_algorithm_and_cookie_csrf_cannot_be_bypassed(isolated_app, monkeypatch):
    from jose import jwt
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
