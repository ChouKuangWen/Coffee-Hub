import pytest
from app.core.security import hash_password, verify_password

# 測試：相同的密碼每次加密應該產生不同的雜湊（bcrypt 有加 salt）
def test_hash_password_returns_different_hashs_for_same_input():
    password = "testpassword"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2  # 雖然輸入一樣，但因為 bcrypt 有隨機 salt，每次結果都不同
    assert hash1.startswith("$2b$")  # 確認雜湊值的格式開頭是 bcrypt 標準（$2b$）

# 測試：正確的密碼應能通過驗證
def test_verify_password_correct():
    password = "mypassword123"
    hashed = hash_password(password)  # 將密碼轉雜湊
    assert verify_password(password, hashed) is True  # 比對密碼

# 測試：錯誤的密碼應該無法通過驗證
def test_verify_password_incorrect():
    password = "mypassword123"
    wrong_password = "wrongpassword"
    hashed = hash_password(password)
    assert verify_password(wrong_password, hashed) is False  # 使用錯的密碼驗證應該回傳 False

