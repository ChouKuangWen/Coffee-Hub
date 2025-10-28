#  會員後台管理系統（Member Order Management System）

##  專案簡介
本系統為一個以 **FastAPI + Vue3** 為核心的全端專案，實作了：
- 會員登入註冊  
- 訂單管理  
- 角色權限控管（RBAC）  
- JWT 驗證機制  
- API 安全防護與資料庫操作  

後端採用 **FastAPI** 框架搭配 **SQLAlchemy (Async ORM)** 與 **MySQL**；  
前端則以 **Vue3 + Vite** 建構。  

此系統結構清晰、模組化，可支援容器化部署並延伸至雲端環境（如 **GCP Cloud SQL**）。

---

##  專案結構與檔案說明
```bash
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
│   │   ├── schemas/                  # 請求/回傳格式定義
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
│   └── seed.sql                      # 預設資料（如角色、admin）
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

#  系統運作流程

##  1️ 登入與驗證流程
1. 使用者於前端登入頁輸入帳號與密碼。  
2. 前端呼叫後端 `/auth/login` API。  
3. 後端使用 `bcrypt` 驗證雜湊密碼。  
4. 若驗證成功：
   - 生成 JWT Token（含使用者 ID、角色等 payload）。  
   - 將 Token 存入 **HTTP-only Cookie**（安全、不可由 JavaScript 存取）。  
5. 後續 API 請求中，後端中介層自動從 Cookie 驗證身份。

---

##  2️ 權限驗證流程（RBAC）
1. 每個 API 端點皆設定最低角色需求（例如 Admin 才能操作）。  
2. `dependencies.py` 定義權限檢查函式：  
   - 從 Token 中解析角色資訊。  
   - 檢查該角色是否有權限操作。  
3. 若權限不足 → 回傳 `HTTP 403 Forbidden`；若成功 → 執行 CRUD。

---

##  3️ 資料存取流程
1. API 層呼叫對應的 CRUD 模組。  
2. CRUD 使用 SQLAlchemy ORM 執行非同步資料操作。  
3. 結果經由 Pydantic Schema 轉為 JSON 回傳前端。

---

##  角色導向存取控制（RBAC）

RBAC 採「角色綁定權限」方式，方便後期擴充。

| 角色     | 可執行操作                        | 權限範圍             |
|----------|-----------------------------------|--------------------|
| Admin    | 新增/刪除/修改/查詢所有使用者與訂單 | 全系統最高權限       |
| Manager  | 查詢與管理所有訂單，檢視使用者資料   | 管理層權限           |
| Customer | 查詢、編輯個人訂單與個人資料         | 限本人資料           |

---

##  安全機制

| 安全機制             | 說明                                           |
|--------------------|----------------------------------------------|
| HTTP-only Cookie    | Token 以此方式儲存，防止 XSS 攻擊竊取。       |
| JWT Token           | 驗證身份與角色權限，內含過期時間與角色資訊。 |
| bcrypt 密碼雜湊     | 所有密碼皆經雜湊後儲存，防止資料庫外洩風險。 |
| CSP (Content Security Policy) | 限制前端可載入的資源來源，防止惡意腳本。 |
| CORS 白名單         | 僅允許特定前端網域呼叫 API。                 |

---

##  技術棧

| 分類   | 使用技術                                  |
|--------|-----------------------------------------|
| 後端   | FastAPI、SQLAlchemy (Async ORM)、MySQL、JWT、bcrypt |
| 前端   | Vue3、Vite、Pinia、Axios、TailwindCSS    |
| 部署   | Docker、Google Cloud run、Google Cloud SQL  |
| 安全   | CSP、HTTP-only Cookie、CORS、RBAC        |

---

##  系統流程圖（概念示意）

```mermaid
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
