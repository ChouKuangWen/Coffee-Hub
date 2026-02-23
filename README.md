#  Coffee Hub - 職人咖啡交易平台 (Coffee Hub Trading Platform)

##  專案簡介
**Coffee Hub** 是一個基於 **FastAPI + Vue 3 + MySQL** 構建的高性能職人咖啡交易平台。本專案採前後端分離架構，不僅實作了精準的角色權限控制 (RBAC)，更從傳統的後台管理系統進化為支援「買家消費」與「賣家銷售」的電商系統。

系統整合了 **JWT 雙 Token 驗證**、**CSP 安全防護**、**API 限流保護**，並能透過 **Docker** 容器化部署至 **Google Cloud Platform (GCP)**。

---

## 核心技術棧 (Technology Stack)

| 領域 | 技術 / 框架 | 亮點說明 |
|------|---------------|-----------|
| **後端 (Backend)** | **FastAPI** (Python 3.10+) | 非同步 (Async) 高性能架構，自動生成 OpenAPI 文件。 |
| **資料庫 (Database)** | **MySQL 8.0** | 穩定的關聯式資料庫，支援複雜訂單與庫存邏輯。 |
| **ORM** | **SQLAlchemy (Async)** | 採用非同步注入與參數化查詢，兼顧效能與安全性。 |
| **前端 (Frontend)** | **Vue 3 (Composition API)** | 搭配 Vite 與 Pinia 實作更新 (Optimistic UI) 購物車。 |
| **安全 (Security)** | **Slowapi + CSP + Bcrypt** | 實作 API 限流、動態 Nonce CSP 防護與密碼雜湊。 |
| **雲端 (Cloud)** | **GCP (Cloud Run + SQL)** | 完整雲端容器化部署方案，具備自動擴展與私有網路連線。 |

---

##  核心特色 (Core Features)

本專案不僅提供完整的管理功能，更以 **安全性與架構設計** 為核心。

---

### 權限與商務邏輯 (RBAC)
- **多角色權限分流**：一套系統架構精準識別 **Admin (管理員)**、**Seller (賣家)**、**Customer (買家)**。
- **買家體驗**：響應式商品瀏覽、基於 Pinia 的全域購物車系統、個人訂單追蹤。
- **賣家商務控制台**：獨立的商品管理介面、庫存追蹤與訂單處理邏輯。

---
### 深度安全防護
- **內容安全策略 (CSP)**：自研 `CSPMiddleware` 實作 **Nonce 動態注入**，阻斷 XSS 與惡意內聯腳本。
- **API 限流機制**：整合 `Slowapi` 針對登入與敏感操作進行頻率限制，防止暴力破解。
- **身分驗證優化**：透過 **Http-only & Secure Cookies** 傳輸 JWT，有效防禦憑證盜取並提升 Session 安全性。

---
### 非同步架構
- **非同步**：從 API 路由到資料庫 CRUD 全面採用 `async/await`，最大化系統併發處理能力。
- **自動化模型驗證**：利用 `Pydantic` 進行嚴格的輸入/輸出資料清洗，確保 API 數據的一致性。

---
###  雲端部署優勢
- **前端靜態託管**：專案編譯後部署於 **Google Cloud Storage (GCS)**，享受低延遲與高可用性。
- **私有網路連線**：Cloud Run 透過 **Serverless VPC Access** 經由內部私人 IP 存取 Cloud SQL，確保資料庫不暴露於公網。

---

##  專案結構與檔案說明
```
Member-order-management-system/
├── backend/                          # 後端主程式
│   ├── app/
│   │   ├── api/                      # API 路由
│   │   │   ├── auth.py               # 會員 API（註冊、登入、管理）
│   │   │   ├── cart.py               # 購物車 API
│   │   │   ├── order_items.py        # 訂單項目 API
│   │   │   ├── orders.py             # 訂單管理 API
│   │   │   ├── products.py           # 商品 API
│   │   │   ├── upload.py             # 商品圖片上傳至Cloud Storage API
│   │   │   └── users.py              # 使用者管理 API
│   │   │
│   │   ├── core/                     # 核心設定模組
│   │   │   ├── config.py             # 環境變數與設定
│   │   │   ├── csp_middleware.py     # CSP 中介軟體
│   │   │   ├── gcp_storage.py        # Google Cloud Storage 圖片上傳功能
│   │   │   ├── jwt.py                # JWT 驗證與簽發
│   │   │   ├── rate_limit.py         # API 限流
│   │   │   ├── sanitizer.py          # 輸入清理與防 XSS
│   │   │   └── security.py           # 密碼加密與驗證
│   │   │
│   │   ├── crud/                     # 資料庫操作層
│   │   │   ├── order_items.py
│   │   │   ├── orders.py
│   │   │   ├── products.py
│   │   │   └── users.py
│   │   │
│   │   ├── models/                   # ORM 模型
│   │   │   ├── base.py
│   │   │   ├── cart_item.py
│   │   │   ├── jwt_blacklist.py
│   │   │   ├── order_items.py
│   │   │   ├── orders.py
│   │   │   ├── products.py
│   │   │   ├── refresh_token.py
│   │   │   ├── roles.py
│   │   │   ├── used_jwt.py
│   │   │   └── users.py
│   │   │
│   │   ├── schemas/            # Pydantic定義驗證API請求與回傳的資料結構
│   │   │   ├── cart.py.py
│   │   │   ├── order_items.py
│   │   │   ├── orders.py
│   │   │   ├── products.py
│   │   │   ├── roles.py
│   │   │   └── users.py
│   │   │
│   │   ├── dependencies.py           # 依賴與權限判斷
│   │   └── main.py                   # FastAPI 進入點
│   │
│   ├── tests/                        # 單元測試
│   │   ├── test_auth.py
│   │   └── test_security.py
│   │
│   ├── Dockerfile                    # 後端 Docker 設定
│   └── requirements.txt              # 依賴套件列表
│
├── database/                         # 資料庫初始化 SQL
│   ├── init.sql                      # 建表指令
│   └── seed.sql                      # 預設資料（如角色admin）
│
├── frontend/                         # 前端專案
│   ├── public/
│   │   ├── images/
│   │   └── vite.svg
│   │
│   ├── src/
│   │   ├── assets/
│   │   ├── components/               # 可重用元件
│   │   │   └── Navbar.vue
│   │   │
│   │   ├── stores/
│   │   │   ├── auth.js
│   │   │   └── cart.js
│   │   │
│   │   ├── views/                    # 頁面
│   │   │   ├── Cart.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── Home.vue
│   │   │   ├── Login.vue
│   │   │   ├── Orders.vue
│   │   │   ├── ProductDetail.vue
│   │   │   ├── Products.vue
│   │   │   ├── Register.vue
│   │   │   └── Users.vue
│   │   │
│   │   ├── App.vue
│   │   ├── api.js                    # 後端 API 串接設定
│   │   ├── main.js                   # Vue 入口
│   │   ├── router.js                 # Vue Router 設定
│   │   └── style.css                 # 全域樣式
│   │
│   ├── .dockerignor
│   ├── .gitignore
│   ├── Dockerfile                    # 前端 Docker 設定
│   ├── index.html
│   ├── nginx.conf
│   ├── package-lock.json
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── README.md
└── .gitignore
```
---

## 專案未來規劃 (Roadmap)

本專案持續優化性能與擴展功能，目前已規劃以下三大核心迭代目標：

---
### 1.  AI 智能助手整合 (RAG 檢索增強生成)
* **技術路徑**：導入大語言模型 (LLM) 並結合向量資料庫。
* **功能目標**：實作「咖啡職人 AI 助手」，能根據平台現有商品資訊回答用戶提問，並根據用戶口味偏好提供精準的咖啡豆推薦。

### 2.  進階防禦機制 (CSRF Token 實作)
* **技術路徑**：在現有 `SameSite` Cookie 防護基礎上，新增 **Double Submit Cookie** 驗證機制。
* **功能目標**：針對金流結帳、修改權限等高敏感操作提供銀行級防禦，確保請求 100% 來自合法授權前端。

### 3.  前後台分離部署
* **技術路徑**：將「買家商城前台」與「專業管理後台」拆分為獨立的專案。
* **功能目標**：大幅縮減首屏載入體積，並讓管理端能實施更嚴格的網路存取限制 。


---
## 安裝與使用方式

1. 環境安裝
```
git clone https://github.com/ChouKuangWen/Coffee-Hub.git
cd Coffee-Hub
```
```
pip install -r requirements.txt
```

2. 環境變數設定
```
# Database 設定
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=mysql
DB_PORT=3306
DB_NAME=coffee_hub_db

# MySQL 初始化設定
MYSQL_ROOT_PASSWORD=your_password
MYSQL_DATABASE=coffee_hub_db

# JWT 設定
SECRET_KEY=使用_openssl_rand_hex_32_生成的隨機字串
ALGORITHM=HS256

# GCP 雲端相關 (選填)
GCP_BUCKET_NAME=your-gcs-bucket-name
```

3. 啟動
```
docker-compose up --build
```

4. 訪問網址
啟動成功後，您可以透過以下網址存取服務：
```
http://localhost:3000
```
---
