from passlib.context import CryptContext
import base64
import binascii
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import UnsupportedAlgorithm

# 建立密碼加密的 context，使用 bcrypt 演算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 將使用者輸入的純文字密碼進行雜湊處理
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 驗證純文字密碼是否與加密後密碼相符
def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def validate_jwt_configuration(algorithm: str, key: str | bytes) -> None:
    """啟動時阻擋已知 JWT 金鑰混淆與不安全 ECDSA 後端；不輸出金鑰。"""
    supported = {"HS256", "HS384", "HS512", "RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}
    if algorithm not in supported:
        raise ValueError("JWT 必須設定單一明確支援的簽章演算法")
    if algorithm.startswith("HS"):
        raw = key.encode("utf-8") if isinstance(key, str) else key
        if not raw or b"-----BEGIN" in raw or raw.startswith((b"ssh-", b"ecdsa-")):
            raise ValueError("HMAC 金鑰不得使用非對稱金鑰或空值")
        candidates = [raw]
        try:
            candidates.append(base64.b64decode(raw, validate=True))
        except (ValueError, binascii.Error):
            pass
        for candidate in candidates:
            try:
                serialization.load_der_public_key(candidate)
            except (ValueError, TypeError):
                continue
            except UnsupportedAlgorithm:
                # 可識別為金鑰、但演算法不受支援，也不能當作共享密鑰。
                raise ValueError("HMAC 金鑰不得使用 DER 公鑰") from None
            raise ValueError("HMAC 金鑰不得使用 DER 公鑰")
    elif algorithm.startswith("ES"):
        from jose import jwk
        from jose.backends.cryptography_backend import CryptographyECKey
        if jwk.get_key(algorithm) is not CryptographyECKey:
            raise ValueError("ECDSA 簽章必須使用 cryptography 後端，禁止不安全的回退後端")






