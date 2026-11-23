"""JWT 套件遷移：舊 Token 由隔離的舊版環境預先簽發，不將舊依賴帶回安裝清單。"""
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import jwt
import pytest
from fastapi import HTTPException
from freezegun import freeze_time
from tests.unit.test_account_permissions import isolated_app


def test_old_hs256_tokens_with_hex_string_key(isolated_app, monkeypatch):
    algorithm = "HS256"
    corpus_path = os.getenv("COFFEEHUB_LEGACY_JWT_CORPUS")
    if not corpus_path:
        pytest.skip("需提供由 python-jose 3.5.0 產生的隔離測試 Token；不讀正式金鑰")
    corpus = json.loads(Path(corpus_path).read_text(encoding="utf-8"))
    assert corpus["issuer_library"] == "python-jose 3.5.0"
    entry = next(item for item in corpus["entries"] if item["algorithm"] == algorithm)
    assert len(entry["signing_key"]) == 64
    assert all(c in "0123456789abcdef" for c in entry["signing_key"])
    module = isolated_app.token
    monkeypatch.setattr(module, "ALGORITHM", algorithm)
    monkeypatch.setattr(module, "SECRET_KEY", entry["signing_key"])
    for kind in ("access", "refresh"):
        assert module.decode_token(entry[kind], kind)["sid"] == "legacy-session"
    assert module.decode_token(entry["future_iat"], "access")["iat"] == 4102444700
    # 維持 64 字元十六進位字串，不使用 bytes.fromhex 改變金鑰內容。
    access, _ = module.create_access_token({"user_id": 1, "role_id": 3, "session_id": "legacy-session"})
    assert module.decode_token(access, "access")["sub"] == "1"
    monkeypatch.setattr(module, "SECRET_KEY", entry["verification_key"])
    assert module.decode_token(entry["access"], "access")["role_id"] == 3
    # 已保存的舊 Refresh 字串不重新簽發，仍與 Session 紀錄精確比對。
    session = SimpleNamespace(token=entry["refresh"], expires_at=datetime(2099, 1, 1))
    result = Mock()
    result.scalars.return_value.first.return_value = session
    db = SimpleNamespace(execute=AsyncMock(return_value=result))
    assert asyncio.run(module.verify_refresh_token(entry["refresh"], db))["jti"] == "legacy-session"


@freeze_time("2026-11-22 00:00:00")
def test_claim_validation_preserves_legacy_rules(isolated_app, monkeypatch):
    module = isolated_app.token
    now = int(datetime.now(timezone.utc).timestamp())
    payload = {"sub": "1", "jti": "test", "sid": "session", "version": 0,
               "token_type": "access", "role_id": 3, "exp": now}

    def signed(changes):
        return jwt.encode(dict(payload, **changes), module.SECRET_KEY, algorithm=module.ALGORITHM)

    # 舊版接受 exp 與目前整秒相等、只檢查 iat 型別，並依 nbf 限制啟用時間。
    assert module.decode_token(signed({"iat": now + 3600, "nbf": now}), "access")["sub"] == "1"
    invalid = [{"exp": now - 1}, {"nbf": now + 1}, {"iat": "invalid"}, {"iat": None},
               {"exp": []}, {"exp": None}, {"exp": float("inf")}, {"sub": 1}, {"jti": 1},
               {"aud": ""}, {"aud": []}, {"at_hash": None}, {"version": True}]
    for changes in invalid:
        with pytest.raises(HTTPException) as exc:
            module.decode_token(signed(changes), "access")
        assert exc.value.status_code == 401
    for missing in ("exp", "sub", "jti"):
        claims = dict(payload)
        claims.pop(missing)
        with pytest.raises(HTTPException):
            module.decode_token(jwt.encode(claims, module.SECRET_KEY, algorithm=module.ALGORITHM), "access")
    invalid_signature = jwt.encode(payload, "different-test-key-with-at-least-64-bytes-" * 2,
                                   algorithm=module.ALGORITHM)
    with pytest.raises(HTTPException):
        module.decode_token(invalid_signature, "access")
    with pytest.raises(HTTPException):
        module.decode_token(jwt.encode(payload, "", algorithm="none"), "access")


def test_jti_blacklist_is_enforced(isolated_app, monkeypatch):
    module = isolated_app.token
    access, _ = module.create_access_token({"user_id": 1, "role_id": 3, "session_id": "session"})
    monkeypatch.setattr(module, "is_jti_blacklisted", AsyncMock(return_value=True))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(module.verify_access_token(access, Mock()))
    assert exc.value.status_code == 401
