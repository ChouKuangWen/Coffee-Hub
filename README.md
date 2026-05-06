#  Coffee Hub - 職人咖啡交易平台 (Coffee Hub Trading Platform)
基於 **FastAPI + Vue 3 + MySQL（Async）** 建構的全端系統，
專注於 **後端架構設計、系統穩定性與可觀測性（Observability）**。
 **三層架構重構 (API / Service / CRUD)**，並強化了 **交易安全性、審計追蹤、非同步併發處理**。 
目標是打造一個 **可擴展、可維護、具備安全防護** 的全端平台。
---

##  專案簡介
Coffee Hub 是一個支援多角色的應用系統，包含：

- 商品管理（Product）
- 訂單管理（Order）
- 購物車（Cart）
- 權限控管（RBAC）

本專案重點不在於功能數量，而在於：

- 系統架構設計（Layered Architecture）
- 非同步處理（Async）
- 錯誤處理與資料一致性（Transaction Control）
- 系統可觀測性（Logging / Audit Log）

---

## 專案價值

本專案以「後端工程實務」為核心，著重：
- **架構設計**：設計並落實 API / Service / CRUD 三層分離，提升維護性與測試性。
- **交易安全**：統一由 Service 層管理 commit/rollback，確保資料一致性。
- **可觀測性**：導入 request_id middleware、system log、audit log，提升問題追蹤能力。
- **安全防護**：實作 CSP、Rate Limiting、JWT + HttpOnly Cookie，符合企業級安全需求。
- **雲端部署**：使用 GCP Cloud Run + Cloud SQL，支援容器化與水平擴展

---

## 系統架構

<div align="center">
  <a href="docs/architecture.svg" target="_blank">
    <img src="docs/architecture.svg" alt="Coffee Hub System Architecture" width="850">
  </a>
  <p align="center">
    <em>Coffee Hub 系統架構圖：展示從入口防護、FastAPI 三層架構到 RAG AI 服務的完整流量與事務控管。</em>
  </p>
</div>


---

## 核心設計（Engineering Design）

### 1.分層架構（Layered Architecture）

- API：處理 request / response
- Service：商業邏輯與流程控制
- CRUD：資料庫操作

提升可維護性與測試性

---

### 2.Transaction 控制

- commit / rollback 統一由 Service 層管理
- CRUD 不直接 commit

確保資料一致性與錯誤復原能力

---

### 3.非同步架構（Async）

- 使用 async / await
- FastAPI + SQLAlchemy Async

提升併發處理能力

---

### 4️.可觀測性（Observability）

- request_id middleware（請求追蹤）
- system log（API 層）
- audit log（非同步紀錄使用者行為）

可追蹤系統行為與錯誤來源

---

### 錯誤處理策略
- DB error → rollback
- 記錄 log，不影響主流程

---


## 核心技術棧 (Technology Stack)

| 類別 | 技術 |
|------|------|
| Backend | FastAPI（Python, async） |
| Database | MySQL |
| ORM | SQLAlchemy Async |
| Frontend | Vue 3 |
| Auth | JWT（HttpOnly Cookie） |
| Security | CSP / Rate Limit / Bcrypt |
| Cloud | GCP Cloud Run + Cloud SQL |
| Container | Docker |

---

## 安全設計（Security）

- CSP（Content Security Policy）防止 XSS
- Rate Limiting（SlowAPI）防止濫用
- JWT + HttpOnly Cookie
- 密碼雜湊（bcrypt）

---

## 核心功能（Core Features）

- RBAC 多角色權限控管（Admin / Seller / Customer）
- 訂單管理（建立 / 更新 / 刪除）
- 購物車狀態管理（Pinia）

---

### Service Layer 架構
- 商業邏輯與資料庫解耦
- 集中 transaction 控制

---

### 錯誤處理策略
- DB error → rollback
- 記錄 log，但不影響主流程

---

### Logging 系統
- System Log（middleware）
- Audit Log（BackgroundTasks 非同步寫入）

---

## 金流設計（簡述）

> 目前尚未串接第三方金流，僅預留設計

- 訂單狀態支援付款流程（PENDING / PAID）
- 預留第三方支付整合（如 Webhook 回調）
- 設計考量：冪等性 / 狀態一致性

---


##  專案結構與檔案說明
```
Member-order-management-system/
├── backend/                          # 後端主程式
│   ├── app/
│   │   ├── api/                      # API 路由
│   │   ├── core/                     # 核心設定模組 middleware / logging / security
│   │   ├── crud/                     # 資料庫操作層
│   │   ├── models/                   # ORM 模型
│   │   ├── schemas/                  # Pydantic定義驗證API請求與回傳的資料結構
│   │   ├── services/                 # 商業邏輯層（Transaction / Business rules）
│   │   ├── dependencies.py           # 依賴與權限判斷
│   │   └── main.py                   # FastAPI 進入點
│   │
│   ├── scripts/                      # 開發輔助腳本（資料同步 / RAG / 實驗用）
│   │
│   ├── tests/                        # 單元測試
│   │
│   ├── Dockerfile                    # 後端 Docker 設定
│   └── requirements.txt              # 依賴套件列表
│
├── database/                         # 資料庫初始化 SQL
│
├── frontend/                         # 前端專案
│   ├── public/                       # 靜態資源
│   │
│   ├── src/
│   │   ├── assets/                   # 靜態資源（CSS / 圖片模組化）
│   │   ├── components/               # 可重用元件
│   │   ├── stores/                   # Pinia 狀態管理（auth / cart）
│   │   ├── views/                    # 頁面
│   │   ├── App.vue                   # 根元件
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

## 測試（Testing）

- pytest（基礎功能測試）
- 持續補強中（API / transaction / service）

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

## 專案未來規劃 (Roadmap)

本專案持續優化性能與擴展功能，目前已規劃以下三大核心迭代目標：

---
### 1.  AI 智能助手整合 (RAG 檢索增強生成)
* **技術路徑**：導入大語言模型 (LLM) 並結合向量資料庫。
* **功能目標**：實作「咖啡職人 AI 助手」，能根據平台現有商品資訊回答用戶提問，並根據用戶口味偏好提供精準的咖啡豆推薦。

### 2.  進階防禦機制 (CSRF Token 實作)
* **技術路徑**：在現有 `SameSite` Cookie 防護基礎上，新增 **Double Submit Cookie** 驗證機制。
* **功能目標**：針對金流結帳、修改權限等高敏感操作提供銀行級防禦，確保請求 100% 來自合法授權前端。
---
