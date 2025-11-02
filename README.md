#  會員後台管理系統（Member Order Management System）

##  專案簡介
本專案是一個採用 **FastAPI + Vue 3 + MySQL** 為核心的**前後端分離**後台管理系統，旨在提供安全、高效、且易於部署的管理介面。系統實現了從基礎會員功能到複雜角色權限控制的完整後端服務。


##  核心技術棧 (Technology Stack)

| 領域 | 技術/框架 | 亮點說明 |
| :--- | :--- | :--- |
| **後端 (Backend)** | **FastAPI + Pydantic** | 高性能 Python 框架，結合 Pydantic 實現高效的資料模型與驗證。。 |
| **資料庫 (Database)** | **MySQL** | 穩定的關聯式資料庫。 |
| **ORM** | **SQLAlchemy (Async ORM)** | 採用非同步 ORM 模式，提升資料庫 I/O 效率。 |
| **前端 (Frontend)** | **Vue 3 + Vite** | 採用 Vue 3 Composition API 搭配 Vite 快速開發和打包。 |


##  系統安全機制與防護 (Security Measures)

本系統以安全性為優先考量，在身份驗證、資料傳輸與輸入處理等多層面實施了嚴格的安全防護，防禦常見 $\text{Web}$ 攻擊。

###  安全機制總覽

| 安全機制 | 類型 | 防禦目標與說明 |
| :--- | :--- | :--- |
|  **$\text{SQLAlchemy}$ $\text{ORM}$** | 資料庫操作安全 | **防禦 $\text{SQL}$ 注入攻擊。** 透過參數化查詢機制，避免將使用者輸入當作 SQL 指令執行。 |
|  **輸入淨化 ($\text{Sanitization}$)** | 輸入過濾 | **防禦 $\text{XSS}$ 攻擊。** 使用 Python 的 bleach 函式庫，嚴格移除所有 HTML 標籤，只允許純文本。 |
|  **$\text{JWT}$ 驗證機制** | 身份驗證 | **驗證使用者身份。** 採用無狀態 Tokens 進行認證。 |
|  **角色權限控管 ($\text{RBAC}$)** | 授權控制 | **防禦越權操作。** 確保用戶無法存取其權限範圍以外的資源。 |
|  **$\text{bcrypt}$ 密碼雜湊** | 資料儲存安全 | **防禦資料庫密碼洩露。** 儲存密碼時使用高強度 bcrypt 雜湊。 |
|  **$\text{HTTP-only Cookie}$** | Token 儲存安全 | **防禦 $\text{XSS}$ 攻擊竊取 $\text{Token}$。** 限制 JavaScript 無法讀取 Cookie 內容。 |
|  **$\text{CSP}$ 中介軟體** | API 安全防護 | **防禦 $\text{XSS}$ 和資料注入。** 透過 HTTP 響應頭，嚴格限制前端頁面可載入的資源來源。 |


###  JWT 身份驗證與撤銷機制詳解

本系統實施了一套高安全性的 **雙 Token 系統（Access 與 Refresh）**，旨在實現無狀態認證並提供即時撤銷能力。

| 機制名稱 | 實作細節 | 安全優勢 |
|-----------|-----------|-----------|
| **雙 Token 系統** | 採用短效期 **Access Token** 搭配長效期 **Refresh Token**。<br>**Refresh Token** 被追蹤於資料庫中，可被單獨撤銷。 |  降低風險：縮短 Access Token 的有效時間，極大降低 Token 被盜用後的攻擊窗口。 |
| **HTTP-only Cookie** | 登入後，Access Token 和 Refresh Token 皆透過 HTTP 響應頭設為 `HttpOnly=True` 傳輸。 |  防禦 XSS：JavaScript 無法讀取 Token，防止惡意腳本竊取 Token。 |
| **即時黑名單 (JTI Blacklisting)** | 每個 Access Token 都帶有唯一 ID（JTI）。<br>登出時，JTI 會被立即寫入 `JWTBlacklist` 資料庫。 |  登出立即生效：每次 API 請求驗證時，會檢查 JTI 是否在黑名單中，確保 Token 即時失效。 |
| **資料庫追蹤 Refresh Token** | Refresh Token 及其狀態 (`is_revoked`) 儲存於資料庫。 |  可控性：確保 Refresh Token 可在資料庫層面被強制過期或撤銷，防止惡意續期。 |


**總結**

此 JWT 認證架構結合了：

- **短期授權 + 長期憑證** 雙層防護機制
- **HTTP-only Cookie** 提升前端安全性
- **即時黑名單機制** 實現登出即失效
- **資料庫級 Refresh Token 控制** 確保可精準撤銷

最終達成 **無狀態、高安全性、可控撤銷** 的 JWT 認證系統。


---

##  核心功能

* 會員註冊、登入、登出
* 會員管理、商品管理、訂單處理 $\text{CRUD}$ 功能
* 精細化的角色權限控管 ($\text{RBAC}$)

##  部署與架構 (Deployment & Architecture)

本專案結構清晰、模組化，支援現代雲端部署：

*  **容器化部署：** 完整支援 $\text{Docker}$ 容器化，確保開發與生產環境一致。
*  **雲端延伸性：** 可輕鬆部署至 $\text{Google Cloud Platform (GCP)}$，例如使用 $\text{Cloud Run}$ 託管 $\text{API}$，並將資料庫遷移至 $\text{GCP Cloud SQL}$。

---

##  專案結構與檔案說明
```
Member-order-management-system/
├── backend/                          # 後端主程式
│   ├── app/
│   │   ├── api/                      # API 路由
│   │   │   ├── auth.py               # 會員 API（註冊、登入、管理）
│   │   │   ├── order_items.py        # 訂單項目 API
│   │   │   ├── orders.py             # 訂單管理 API
│   │   │   ├── products.py           # 商品 API
│   │   │   └── users.py              # 使用者管理 API
│   │   │
│   │   ├── core/                     # 核心設定模組
│   │   │   ├── config.py             # 環境變數與設定
│   │   │   ├── csp_middleware.py     # CSP 中介軟體
│   │   │   ├── jwt.py                # JWT 驗證與簽發
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
│   ├── src/
│   │   ├── components/               # 可重用元件
│   │   ├── views/                    # 頁面
│   │   │   ├── Dashboard.vue
│   │   │   ├── Login.vue
│   │   │   ├── Orders.vue
│   │   │   ├── Products.vue
│   │   │   ├── Register.vue
│   │   │   └── Users.vue
│   │   ├── api.js                    # 後端 API 串接設定
│   │   ├── router.js                 # Vue Router 設定
│   │   ├── main.js                   # Vue 入口
│   │   └── style.css                 # 全域樣式
│   ├── Dockerfile                    # 前端 Docker 設定
│   ├── package.json
│   └── vite.config.js
│
├── README.md
└── .gitignore
```
---

##  系統運作流程 (How It Works)

### 1️ 登入與驗證流程
1.  使用者輸入帳密，前端呼叫 `/auth/login` $\text{API}$。
2.  後端使用 $\text{bcrypt}$ 驗證雜湊密碼。
3.  驗證成功後，生成 $\text{JWT Token}$（含使用者 $\text{ID}$、角色等 $\text{payload}$）。
4.  $\text{Token}$ 寫入 **$\text{HTTP-only Cookie}$** 返回給前端，防止 $\text{XSS}$ 竊取。
5.  後續請求中，後端中介層自動從 $\text{Cookie}$ 讀取 $\text{Token}$ 驗證身份。

### 2️ 權限驗證流程 ($\text{RBAC}$)
1.  所有重要 $\text{API}$ 端點皆透過 $\text{FastAPI}$ 的**依賴注入 $(\text{dependencies.py})$** 設定最低角色需求。
2.  權限檢查函式解析 $\text{Token}$ 中的角色資訊。
3.  若權限不足，立即返回 `HTTP 403 Forbidden`；若權限足夠，則執行業務邏輯。

### 3️ 資料存取流程
1.  $\text{API}$ 層呼叫對應的 **$\text{CRUD}$ 模組**。
2.  $\text{CRUD}$ 模組使用 **$\text{SQLAlchemy (Async)}$** 執行參數化查詢，安全地操作 $\text{MySQL}$ 資料庫。
3.  數據驗證與轉換： $\text{CRUD}$ 結果經由 $\text{Pydantic Schema}$ 進行嚴格的資料驗證，並轉換為標準化 $\text{JSON}$ 回傳前端。

---

## 角色導向存取控制 ($\text{RBAC}$) 定義

$\text{RBAC}$ 採用「角色綁定權限」方式，方便後期擴充。

| 角色 | 可執行操作 | 權限範圍 |
| :--- | :--- | :--- |
| **Admin** | 新增/刪除/修改/查詢所有使用者與訂單 | 全系統最高權限 |
| **Manager** | 查詢與管理所有訂單，檢視使用者資料 | 管理層權限 |
| **Customer** | 查詢、編輯個人訂單與個人資料 | 限本人資料 |

---

## 概念流程圖

```
graph TD
    A[使用者] -->|Login.vue| B(POST /auth/login)
    B --> C{FastAPI 驗證}
    C -->|bcrypt 驗證成功| D[產生 JWT Token]
    D --> E[寫入 HTTP-only Cookie]
    E --> F{Middleware 中介層}
    F -->|每次請求自動讀取 Cookie 驗證| G{RBAC 權限檢查}
    G -->|權限足夠| H[CRUD 模組操作]
    H --> I[連線 MySQL 執行操作]
    I --> J[回傳 JSON 結果給前端]
    ```