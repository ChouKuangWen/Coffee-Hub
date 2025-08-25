# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, users, products, orders  # 載入 auth API 路由模組

app = FastAPI(
    title="JWT Auth API",
    description="簡易 JWT 驗證系統",
    version="1.0.0",
)

# 可依需求修改 CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可改為前端網址，例如 http://localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Authentication"])
app.include_router(products.router, prefix="/products", tags=["Authentication"])
app.include_router(orders.router, prefix="/orders", tags=["Authentication"])
#app.include_router(order_items.router, prefix="/order_items", tags=["Authentication"])