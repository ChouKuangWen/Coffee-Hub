#  會員後台管理系統（Member Order Management System）

##  專案簡介
本專案是一個採用 **FastAPI + Vue 3 + MySQL** 為核心的**前後端分離**後台管理系統，旨在提供安全、高效、且易於部署的管理介面。系統實現了從基礎會員功能到複雜角色權限控制的完整後台服務。

---

##  核心技術棧 (Technology Stack)

| 領域 | 技術 / 框架 | 亮點說明 |
|------|---------------|-----------|
| **後端 (Backend)** | $\text{FastAPI}$ + $\text{Pydantic}$ | 高性能 Python 框架，結合 Pydantic 實現高效的資料模型與驗證。 |
| **資料庫 (Database)** | $\text{MySQL}$ | 穩定的關聯式資料庫。 |
| **ORM** | $\text{SQLAlchemy (Async ORM)}$ | 採用非同步 ORM 模式，提升資料庫 $\text{I/O}$ 效率。 |
| **前端 (Frontend)** | $\text{Vue 3}$ + $\text{Vite}$ | 採用 Vue 3 Composition API 搭配 Vite 快速開發和打包。 |
| **部署 (Deployment)** | $\text{Docker}$ / $\text{Docker Compose}$ | 容器化部署，確保開發與生產環境一致。 |
| **雲端 (Cloud)** | $\text{GCP}$ ( $\text{Cloud Run}$) | 支援伺服器部署與資料庫遷移的雲端延伸性。 |

---

##  核心特色 (Core Features)

本專案不僅提供完整的管理功能，更以 **安全性與架構設計** 為核心。

---

###  A. 系統功能完整

- **會員流程**：包含會員註冊、登入、登出。
- **基礎 CRUD 功能**：提供會員、商品、訂單的新增、查詢、修改、刪除功能。
- **精細化授權**：實作角色權限控管 ($\text{RBAC}$) 架構，確保用戶僅能存取其權限範圍內的資源。

---

###  B. 安全與驗證機制

- **雙 Token 撤銷機制**：採用短效期 $\text{Access Token}$ 與長效期 $\text{Refresh Token}$ 雙層防護。
- **即時黑名單 ($\text{JTI Blacklisting}$)**：確保使用者登出時， $\text{Access Token}$ 立即失效，防止被盜用。
- **前端安全防護**：透過 $\text{HTTP-only Cookie}$ 傳輸 Token，防禦 $\text{XSS}$ 惡意腳本竊取憑證。
- **輸入與密碼安全**：
  - 使用 $\text{bcrypt}$ 雜湊儲存密碼，強化資料安全。
  - 實作輸入淨化 ($\text{Sanitization}$)，使用 Python 的 $\text{bleach}$ 函式庫移除 $\text{HTML}$ 標籤以防禦 $\text{XSS}$。
- **API 層防護**：
  - 部署 $\text{CSP}$ 中介軟體以限制可載入資源。
  - 透過 $\text{SQLAlchemy ORM}$ 的參數化查詢防禦 $\text{SQL}$ 注入攻擊。

---

###  C. 架構與部署優勢

- **容器化設計**：完整的 $\text{Docker}$ 與 $\text{Docker Compose}$ 配置，確保環境一致與快速部署。
- **非同步高效能**：利用 $\text{FastAPI}$ 的非同步特性與 $\text{SQLAlchemy Async ORM}$，提升系統整體 I/O 效能。

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

## 系統運作流程 (How It Works)
###  系統架構總覽
```mermaid
graph TD
    %% =====================
    %%  樣式定義
    %% =====================
    classDef frontend fill:#EDF2F7,stroke:#4A5568,stroke-width:2px,color:#2D3748;
    classDef security fill:#FFF5F5,stroke:#C53030,stroke-width:2px,color:#9B2C2C;
    classDef decision fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#92400E;
    classDef backend fill:#F0FFF4,stroke:#2F855A,stroke-width:2px,color:#22543D;
    classDef database fill:#EBF8FF,stroke:#2B6CB0,stroke-width:2px,color:#2A4365;
    classDef error fill:#FED7D7,stroke:#9B2C2C,stroke-width:2px,color:#742A2A;

    %% =====================
    %% ① 前端互動層
    %% =====================
    subgraph L1["① 前端互動層 · Vue 3"]
        UI[" 使用者"]:::frontend
        Axios[" Axios"]:::frontend
        UI --> Axios
    end

    %% =====================
    %% ② 安全防護與中介層
    %% =====================
    subgraph L2["② Middleware"]
        Sanitizer[" Input Sanitizer"]:::security
        IsLogin{"登入 / 註冊？"}:::decision
        Axios --> Sanitizer --> IsLogin
    end

    %% =====================
    %% ③ 後端核心邏輯（橫向展開）
    %% =====================
    subgraph L3["③ FastAPI 核心邏輯"]
        direction LR

        %% 登入流程
        subgraph AUTH[" 登入流程"]
            Bcrypt{"Bcrypt 驗證"}:::decision
            JWT[" JWT 簽發"]:::backend
            Cookie[" HTTP-only Cookie"]:::security
            Bcrypt -->|成功| JWT --> Cookie
        end

        %% 已登入流程
        subgraph VALID[" 已登入流程"]
            TokenCheck{"JWT 檢查"}:::decision
            RBAC{"RBAC 權限"}:::decision
            Business[" Async CRUD"]:::backend
            Pydantic[" Pydantic"]:::backend
            TokenCheck --> RBAC --> Business
            Business <--> Pydantic
        end
    end

    %% =====================
    %% ④ 資料持久層
    %% =====================
    subgraph L4["④ MySQL"]
        ORM[" SQLAlchemy ORM"]:::database
        DB[(" MySQL")]:::database
        ORM <--> DB
    end

    %% =====================
    %%  主流程串接（變成橫向）
    %% =====================
    IsLogin -- 是 --> Bcrypt
    IsLogin -- 否 --> TokenCheck

    Bcrypt -.-> ORM
    Business <-->|await| ORM

    Cookie --> UI

    %% =====================
    %%  錯誤處理（集中）
    %% =====================
    Error401["401"]:::error
    Error403["403"]:::error

    Bcrypt -- 失敗 --> Error401
    TokenCheck -- 失效 --> Error401
    RBAC -- 拒絕 --> Error403

    Error401 -.-> UI
    Error403 -.-> UI
```

###  身份驗證與安全防護流程 (Authentication & Security)
```mermaid
graph TD
    %% =========================
    %%  Style Definitions
    %% =========================
    classDef frontend fill:#EDF2F7,stroke:#4A5568,stroke-width:2px,color:#2D3748;
    classDef security fill:#FFF5F5,stroke:#C53030,stroke-width:2px,color:#9B2C2C;
    classDef decision fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#92400E;
    classDef backend fill:#F0FFF4,stroke:#2F855A,stroke-width:2px,color:#22543D;
    classDef database fill:#EBF8FF,stroke:#2B6CB0,stroke-width:2px,color:#2A4365;

    %% =========================
    %% ① Frontend Layer
    %% =========================
    subgraph L1["① 前端互動層 · Vue 3"]
        UI[" 使用者介面"]:::frontend
        Axios[" Axios API Client<br/>withCredentials: true"]:::frontend
        UI -->|操作| Axios
    end

    L1 ~~~ L2

    %% =========================
    %% ② Security & Middleware
    %% =========================
    subgraph L2["② 安全防護與中介層 · Middleware"]
        direction TB
        Sanitizer[" Global Input Sanitizer<br/>Bleach / XSS / Header Check"]:::security
        IsLogin{"是否為登入請求？"}:::decision

        Axios -->|HTTP Request| Sanitizer
        Sanitizer --> IsLogin
    end

    L2 ~~~ L3

    %% =========================
    %% ③ Backend Core
    %% =========================
    subgraph L3["③ 後端核心邏輯 · FastAPI"]
        direction TB

        %% --- Auth Flow ---
        subgraph AUTH[" 登入與簽發階段"]
            Bcrypt{"密碼驗證<br/>Bcrypt"}:::decision
            Issue[" 簽發雙 Token<br/>Access / Refresh"]:::backend
            Cookie[" 寫入 HTTP-only Cookie<br/>HttpOnly · Secure · SameSite"]:::security

            Bcrypt -- 驗證成功 --> Issue --> Cookie
        end

        %% --- Validation Flow ---
        subgraph VALID[" 驗證與自動刷新階段"]
            ACValid{"Access Token<br/>是否有效？"}:::decision
            JTICheck{"JTI 是否<br/>在黑名單？"}:::decision

            RFValid{"Refresh Token<br/>是否有效？"}:::decision
            ReIssue[" 重新簽發 Token<br/>更新 Cookie"]:::backend
            ReLogin[" 重新登入"]:::security

            ACValid -- 有效 --> JTICheck
            ACValid -- 過期 --> RFValid

            RFValid -- 有效 --> ReIssue
            RFValid -- 失效 --> ReLogin

            JTICheck -- 通過 --> Business[" 執行業務邏輯"]:::backend
        end

        IsLogin -- 是 --> Bcrypt
        IsLogin -- 否 --> ACValid
    end

    L3 ~~~ L4

    %% =========================
    %% ④ Persistence Layer
    %% =========================
    subgraph L4["④ Database"]
        ORM[" SQLAlchemy<br/>Async ORM"]:::database
        DBUser[(" 使用者資料庫")]:::database
        DBJTI[(" JTI 黑名單<br/> MySQL")]:::database

        ORM <--> DBUser
    end

    %% =========================
    %%  Cross-layer Interaction
    %% =========================
    Bcrypt -.->|查詢帳號| DBUser
    JTICheck -.->|檢查| DBJTI
    Business <-->|await| ORM

    Cookie -->|登入成功| UI
    ReIssue -->|Token 更新| UI
    Business -->|JSON Response| UI

    %% =========================
    %%  Error Handling
    %% =========================
    Error401["401 Unauthorized"]:::security
    Bcrypt -- 驗證失敗 --> Error401
    JTICheck -- 已註銷 --> Error401
```

### RBAC 權限校驗流程 (Authorization)
```mermaid
graph TD
    %% 樣式定義
    classDef frontend fill:#EDF2F7,stroke:#4A5568,stroke-width:2px,color:#2D3748;
    classDef security fill:#FFF5F5,stroke:#C53030,stroke-width:2px,color:#9B2C2C;
    classDef decision fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#92400E;
    classDef backend fill:#F0FFF4,stroke:#2F855A,stroke-width:2px,color:#22543D;
    classDef database fill:#EBF8FF,stroke:#2B6CB0,stroke-width:2px,color:#2A4365;

    %% 1. 前端請求 (入口)
    subgraph Layer1 [1. 請求進入 - FastAPI Router]
        Request["API 請求 (例如: DELETE /users/id)"]:::frontend
    end

    %% 增加層級間距
    Layer1 ~~~ Layer2

    %% 2. 依賴注入與角色解析 (中介判斷)
    subgraph Layer2 [2. 角色解析層 - dependencies.py]
        Extract_Payload["解析 JWT Payload"]:::backend
        Get_RoleID["取得使用者 role_id"]:::backend
        Target_Requirement{該 API 要求的<br/>role_id 門檻?}:::decision
    end

    %% 增加層級間距
    Layer2 ~~~ Layer3

    %% 3. 數值判定路徑 (核心邏輯)
    subgraph Layer3 [3. role_id 數值判定邏輯]
        direction TB
        
        Check_Admin{"role_id == 1 ?"}:::decision
        Check_Manager{"role_id == 2 ?"}:::decision
        Check_Customer{"role_id == 3 ?"}:::decision

        Admin_Perm[授予 Admin 權限<br/>全系統最高操作]:::backend
        Manager_Perm[授予 Manager 權限<br/>訂單與資料檢視]:::backend
        Customer_Perm[授予 Customer 權限<br/>限本人資料操作]:::backend

        Target_Requirement -->|門檻: 1| Check_Admin
        Target_Requirement -->|門檻: 2| Check_Manager
        Target_Requirement -->|門檻: 3| Check_Customer

        Check_Admin -- 是 --> Admin_Perm
        Check_Manager -- 是 --> Manager_Perm
        Check_Customer -- 是 --> Customer_Perm
    end

    %% 增加層級間距
    Layer3 ~~~ Layer4

    %% 4. 執行結果
    subgraph Layer4 [4. 執行結果]
        Business[執行 Async CRUD<br/>資料庫操作]:::database
        Error403[403 Forbidden<br/>權限不足]:::security
        
        Admin_Perm --> Business
        Manager_Perm --> Business
        Customer_Perm --> Business
        
        Check_Admin -- 否 --> Error403
        Check_Manager -- 否 --> Error403
        Check_Customer -- 否 --> Error403
    end

    %% 流程連線
    Request ==> Extract_Payload
    Extract_Payload --> Get_RoleID
    Get_RoleID --> Target_Requirement
    Business ==>|回傳結果| Request
```

### 資料存取流程 (Data Flow)
```mermaid
graph TD
    %% 樣式定義
    classDef frontend fill:#EDF2F7,stroke:#4A5568,stroke-width:2px,color:#2D3748;
    classDef logic fill:#F0FFF4,stroke:#16A34a,stroke-width:2px,color:#166534;
    classDef schema fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#92400E;
    classDef database fill:#EBF8FF,stroke:#2563EB,stroke-width:2px,color:#1E3A8A;
    classDef async fill:#F5F3FF,stroke:#7C3AED,stroke-width:2px,color:#4C1D95;

    %% 1. 請求輸入層
    subgraph Layer1 [1. 請求與模型驗證層]
        Request["API 請求 (POST/PUT/GET)"]:::frontend
        In_Schema["Pydantic In-Schema<br/>(資料清洗與型別校驗)"]:::schema
    end

    %% 增加層級間距
    Layer1 ~~~ Layer2

    %% 2. 業務邏輯與非同步控制
    subgraph Layer2 [2. 非同步業務邏輯層 - CRUD]
        Async_Call["Async Function (await)"]:::async
        Business_Logic["業務邏輯處理<br/>(資料轉換/計算)"]:::logic
    end

    %% 增加層級間距
    Layer2 ~~~ Layer3

    %% 3. ORM 與 資料庫互動
    subgraph Layer3 [3. SQLAlchemy Async ORM 層]
        Session["AsyncSession 實例"]:::database
        Query_Build["SQLAlchemy Query Builder<br/>(防止 SQL 注入)"]:::database
        Execute["await session.execute()"]:::async
    end

    %% 增加層級間距
    Layer3 ~~~ Layer4

    %% 4. 資料庫與回應轉換
    subgraph Layer4 [4. 資料持久化與輸出]
        MySQL[("MySQL Database<br/>(存取/更新數據)")]:::database
        Out_Schema["Pydantic Out-Schema<br/>(過濾敏感欄位，如密碼)"]:::schema
    end

    %% 流程連線
    Request ==> In_Schema
    In_Schema --> Async_Call
    Async_Call --> Business_Logic
    Business_Logic --> Session
    Session --> Query_Build
    Query_Build --> Execute
    Execute <==>|非同步 I/O| MySQL
    
    %% 回傳路徑
    MySQL --> Out_Schema
    Out_Schema ==>|JSON Response| Request
```
---

---

##  雲端部署架構 (Cloud Deployment Architecture)

本專案採用 **GCP (Google Cloud Platform)** 進行雲端部署，透過容器化與雲端部署確保系統的可用性與安全性。

###  部署流程圖

```mermaid
flowchart TD
    %% 節點定義與樣式
    subgraph Initialization [1. 初始化與資料庫建立]
        A[啟用 Compute Engine API] --> B[建立 Cloud SQL MySQL 8.0]
        B --> B1[配置私人 IP 與 PSA 連線]
        B --> C[建立 Cloud Storage Bucket]
        C --> C1[上傳 init.sql 與 seed.sql]
        C1 --> C2[匯入資料至 Cloud SQL]
    end

    subgraph Connectivity [2. 網路與權限連通]
        B1 --> D[建立 Serverless VPC Access Connector]
        D --> D1[確認 Connector 與 VPC 子網關聯]
        D1 --> E[IAM 權限授權]
        E --> E1[授予 Cloud SQL Client 角色]
        E --> E2[授予 Service Account User 角色]
    end

    subgraph Backend_Deployment [3. 後端 Cloud Run 部署]
        E1 & E2 --> F[部署 Cloud Run 服務]
        F --> F1[設定 VPC Connector 流量轉送]
        F --> F2[注入環境變數與 Container Port]
        F --> F3[調整 IAM 允許 allUsers 叫用]
    end

    subgraph Frontend_Deployment [4. 前端 GCS 靜態部署]
        G[Vue 專案編譯 base='./'] --> G1[上傳 dist 檔案至 Bucket]
        G1 --> G2[設定 gsutil 公開讀取權限]
        G2 --> G3[啟用靜態網站代管功能]
    end

    %% 最終連線
    G3 --> H{系統上線}
    F3 --> H
```

###  部署組件說明

#### 🔹 前端部署 (Frontend - Vue 3)
* **平台：** Google Cloud Storage (GCS)
* **策略：** **靜態網站代管 (Static Website Hosting)**
* **說明：** * 透過 `npm run build` 產生dist檔案並上傳至 GCS Bucket。
    * 設定 Bucket 為公開讀取，並配置 `index.html` 為入口點（SPA 支援）。

#### 🔹 後端部署 (Backend - FastAPI)
* **平台：** Google Cloud Run
* **策略：** **容器化部署 (Docker)**
* **說明：** * **Dockerfile 驅動：** 直接讀取 GitHub 儲存庫中的 `Dockerfile` 進行映像檔構建，確保部署環境與開發環境高度一致。
    * **VPC Connector：** 建立 **Serverless VPC Access**，讓 Cloud Run 能透過內部私人 IP 安全存取資料庫，避免暴露於公開網路。
    * **Auto-scaling：** 根據流量自動調整實體數量，實現高效能與成本優化。

#### 🔹 資料庫部署 (Database - MySQL)
* **平台：** Google Cloud SQL
* **策略：** **代管式關聯資料庫 (Managed MySQL)**
* **說明：** * 使用 MySQL 8.0 實體。
    * **網路安全性：** 僅開啟 **Private IP**，確保資料庫不會暴露於公網。
    * **初始化：** 透過 Cloud Storage 儲存槽自動匯入 `init.sql` 與 `seed.sql`，完成資料表結構與管理員帳號 (Admin) 的初始設定。

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
│   │   │   ├── Home.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── Login.vue
│   │   │   ├── Orders.vue
│   │   │   ├── Products.vue
│   │   │   ├── Register.vue
│   │   │   └── Users.vue
│   │   ├── App.vue
│   │   ├── api.js                    # 後端 API 串接設定
│   │   ├── router.js                 # Vue Router 設定
│   │   ├── main.js                   # Vue 入口
│   │   └── style.css                 # 全域樣式
│   │
│   ├── .dockerignor
│   ├── .gitignore
│   ├── index.html
│   ├── nginx.conf
│   ├── package-lock.json
│   ├── Dockerfile                    # 前端 Docker 設定
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── README.md
└── .gitignore
```
---

## 角色導向存取控制 ($\text{RBAC}$) 定義

$\text{RBAC}$ 採用「角色綁定權限」方式，方便後期擴充。

| 角色 | 可執行操作 | 權限範圍 |
| :--- | :--- | :--- |
| **Admin** | 新增/刪除/修改/查詢所有使用者與訂單 | 全系統最高權限 |
| **Manager** | 查詢與管理所有訂單，檢視使用者資料 | 管理層權限 |
| **Customer** | 查詢、編輯個人訂單與個人資料 | 限本人資料 |

---


## 專案未來規劃 (Roadmap)

本專案持續優化性能與擴展功能。

以下為我們正在規劃或計劃納入的未來開發目標。

---

###  核心功能與使用者體驗

| 項目 | 詳細說明 | 目標價值 |
| --- | --- | --- |
| **1. 使用者前台介面** | 完成獨立的客戶購物前台應用程式，並與現有的後端 `API` 進行完整串接。 | 提供完整的 B2C 購物流程體驗。 |
| **2. 開放式瀏覽 API** | 實作專門的公開 `API` 端點，允許未註冊使用者（訪客）瀏覽商品列表和詳情。 | 提升商品曝光率與可訪問性。 |
| **3. Cloud Storage 整合** | 結合雲端儲存服務（`Google Cloud Storage`），讓賣家可以直接上傳和管理商品圖片。 | 提高圖片載入效率，減輕伺服器負載。 |
| **4. 商品庫存同步** | 實作嚴謹的庫存管理機制，在訂單成立時自動扣減庫存，並在取消或退貨時回補。 | 確保庫存數據的即時性與準確性。 |
| **5. 後臺統計儀表板** | 建立數據視覺化儀表板，提供關鍵指標（如銷售額、熱門商品、用戶行為）的圖表分析。 | 輔助管理員進行商業決策。 |

---

###  品質、性能與自動化

| 項目 | 詳細說明 | 目標價值 |
|------|-----------|-----------|
| **6. CI/CD 自動化** | 建立 `GitHub Actions` 工作流，實現程式碼合併後的自動測試、建置 `Docker` 映像檔和自動部署。 | 提升開發效率、縮短交付週期、保證部署品質。 |
| **7. Log / 錯誤追蹤** | 整合錯誤監控服務，以便即時追蹤、診斷環境中的運行錯誤。 | 快速定位問題，提升系統穩定性和維護效率。 |

---