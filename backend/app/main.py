# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api import auth, users, products, orders, order_items  # 載入 auth API 路由模組
from app.core.csp_middleware import CSPMiddleware
from app.core.rate_limit import limiter
import os

"""應用程式實例"""
app = FastAPI(
    title="JWT Auth API",
    description="簡易 JWT 驗證系統",
    version="1.0.0"
)

""" 限流器配置 """
# 將 limiter 掛載到 app 狀態中，讓全域都能存取
app.state.limiter = limiter
# 註冊錯誤處理：當使用者請求太快時，回傳 429 Too Many Requests
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

""" Swagger檢查路徑 """
# 1. 服務根路徑 (Root Path) - 確保 Cloud Run 基礎檢查通過
@app.get("/")
def read_root():
    """
    根路徑，用於基本測試和 Cloud Run 預設的健康檢查。
    """
    port = os.environ.get('PORT', '未設定')
    
    return {
        "message": "後端服務已啟動並運行中。",
        "status": "OK",
        "running_on_port": port
    }


# 2. Swagger專用檢查路徑
@app.get("/health")
def health_check():
    """
    專門檢查點，回傳成功狀態。
    """
    return {"status": "ok"}


""" 註冊中介軟體 """
#1. CORS Middleware: 處理跨域請求 (必須保持在 CSP 之前)，可依需求修改 CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "http://localhost:3000",
                   "http://127.0.0.1:3000",
                   "https://member-order-management-backend-system-818780839244.asia-east1.run.app",
                   "http://frontend_member.storage.googleapis.com",
                   "https://frontend_member.storage.googleapis.com",
                   "http://storage.googleapis.com",
                   "https://storage.googleapis.com",],  # 可改為前端網址，例如 http://localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. CSP Middleware: 處理內容安全策略
app.add_middleware(CSPMiddleware)

# 註冊路由
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(order_items.router, prefix="/order_items", tags=["Orders"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])