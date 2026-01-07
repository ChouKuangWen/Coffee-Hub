# backend/app/core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

def user_or_ip_identifier(request: Request):
    """
    自定義識別邏輯：
    1. 優先檢查是否有登入（由 JWT 注入的 user_id）
    2. 若未登入，則回傳 Client IP 作為識別關鍵字
    """
    # 從 dependencies/jwt 抓出request.state
    user_id = getattr(request.state, "user_id", None)
    
    if user_id:
        # 登入使用者：以 "user_id" 作為計數 Key
        return f"user_{user_id}"
    
    # 未登入使用者：以 IP 位址作為計數 Key (例如 "192.168.1.1")
    # 這就是預留給「未登入使用者限制」的地方
    return get_remote_address(request)

# 初始化限流器
# 預設使用我們定義的識別邏輯
limiter = Limiter(key_func=user_or_ip_identifier)