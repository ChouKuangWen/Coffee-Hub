from passlib.context import CryptContext

# 建立密碼加密的 context，使用 bcrypt 演算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 將使用者輸入的純文字密碼進行雜湊處理
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 驗證純文字密碼是否與加密後密碼相符
def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)






