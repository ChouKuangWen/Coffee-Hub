# tests/test_auth.py
from fastapi.testclient import TestClient
from backend.app.main import app  # 直接導入 FastAPI app，不用啟動伺服器

client = TestClient(app)

def test_register_and_login():
    # 測試註冊
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "123456"
    })
    assert response.status_code == 200

    # 測試登入
    response = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "123456"
    })
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens