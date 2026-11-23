# Coffee Hub — v1.0 本機 Docker 作品集

以 FastAPI、SQLAlchemy Async、MySQL 8 與 Vue 3 建立的多角色咖啡交易系統。本版本以 **本機 Docker** 為展示及驗收目標，不使用付費雲端。

## 功能與架構

- **Customer／Seller 買家**：登入、會員資料、購物車、模擬建單及取消申請。
- **Seller**：經 Admin 核准後使用原帳號管理本人商品、圖片及本人訂單品項出貨。
- **Admin**：Seller 申請審核、會員停用／啟用、取消審核與退庫存、完成訂單、Audit Log 查詢。
- **資料一致性**：依資料庫價格成交，訂單／明細／扣庫存／清車共用交易，防重送、避免超賣；取消核准最多退庫存一次。

| 層次 | 技術 |
|---|---|
| 網頁與入口 | Vue 3、Pinia、Vue Router、Nginx |
| API 與業務處理 | Python FastAPI、Pydantic、Service／CRUD |
| 資料庫 | MySQL 8、SQLAlchemy Async、asyncmy |
| 驗證與安全 | PyJWT HS256、bcrypt、HttpOnly Cookie、CSRF、資料歸屬檢查、必要審計 |
| 圖片 | 專案本機圖片；上傳流程使用 fake-gcs-server，保留 GCS SDK 架構 |

## 本機啟動（Windows PowerShell）

需要 Git、Docker Desktop 的 Linux containers 及 PowerShell；不需要本機 Python、Node、GCP 帳號或金鑰。請在專案根目錄執行：

```powershell
.\scripts\Start-LocalDemo.ps1
# 若 18881 已被使用，可另選本機連接埠：
# .\scripts\Start-LocalDemo.ps1 -Port 18882
```

腳本沿用三份 Compose，建立唯一專案、全新 MySQL／模擬圖片 Volume，僅將 Nginx 綁定 `127.0.0.1`。它從 Git 已追蹤檔案建立來源快照，產生本機測試憑證；確認空庫後才載入一次原始 `init.sql`、`seed.sql`。失敗時保留資源，不清空重試。

成功後輸出網址與 `state.json` 路徑。設定、測試憑證與來源快照位於專案外的暫存目錄，請保留並妥善保存；不要提交其 `demo.env`。**再次執行腳本會建立另一套環境，不是更新既有環境。**

既有環境重啟／停止，使用啟動時輸出的狀態檔；不再執行 SQL：

```powershell
$s = Get-Content '啟動時輸出的 state.json 完整路徑' -Raw | ConvertFrom-Json
$composeArgs = @('compose', '-p', $s.project, '--env-file', $s.env_file,
  '-f', 'docker-compose.integration.yml', '-f', 'docker-compose.local.yml',
  '-f', 'docker-compose.demo.yml')
docker @composeArgs up -d
# 按需停止，保留資料：
# docker @composeArgs stop
```

原本的 `docker-compose.yml` 保留為歷史開發設定，不是本機作品集的啟動入口。

## 展示站與測試站

| 既有本機環境 | 用途 |
|---|---|
| `http://localhost:18881` | 原始 seed 展示；保留會員、商品與歷史訂單 |
| `http://localhost:18880` | 獨立測試資料；可驗證購物車、模擬結帳、出貨及取消等寫入流程 |

兩者使用不同 Compose Project／Volume；同名資料庫不表示共用資料。上述連接埠是本次驗收配置，其他電腦以實際啟動輸出為準。模擬交易必須同時設定 `APP_ENV=test`、`ENABLE_SIMULATED_CHECKOUT=true`，不包含付款或物流。

## 原始資料與商品圖片

`database/init.sql` 已包含 001～005 的必要 Schema 與版本紀錄；舊資料庫升級使用 `database/migrations/`，不要對既有資料庫執行 init 或 seed：兩者含重建／清空指令。

原始 `database/seed.sql` 提供 3 角色、6 權限、11 角色權限關聯、30 會員、20 商品、30 訂單、**32 筆明細**。Admin 是 user1～user2、Seller 是 user3～user10、Customer 是 user11～user30；登入使用 Email，測試密碼見原檔註解。這些帳號僅供本機展示。

商品圖片位於 `frontend/public/images/products/`，命名為 `product-商品ID.png`（亦支援 WebP／JPG／JPEG，每個 ID 建議只放一種格式）。商品 1～19 已有圖片，20 保持下架。展示 Compose 唯讀掛載資料夾，放入／替換圖片後整頁重新整理即可，不修改資料庫。圖片由專案作者確認具備展示使用權。

`VITE_LOCAL_PRODUCT_IMAGES=true` 僅由展示 Compose 啟用：舊外部網址對應本機檔案，缺圖顯示佔位；同站模擬器的新上傳圖片仍使用登記網址。Nginx 限制外部圖片來源，不主動連線真實 GCS。

## 安全、驗收及限制

- 授權使用資料庫最新角色及帳號狀態；角色異動／停用透過 Token Version 撤銷所有裝置會話，登出只撤銷當前會話。
- Cookie 寫入請求需要 CSRF；高風險操作與必要 Audit Log 共同成功或回滾。圖片上傳驗證內容、大小、數量及所有權；清理預設 dry-run，實際刪除開關關閉。
- 舊訂單沒有可信商品／Seller 快照與扣庫存證據，維持 NULL／false；不能直接出貨或核准退庫存。新模擬訂單由購物車建立，不偽造歷史資料。
- 不實作正式金流、物流、退款金流或 RAG／AI 推薦。GCP 設定與既有經驗保留於歷史資料，本版本不宣稱已部署至 Cloud Run／Cloud SQL 或完成真實 GCS 驗收。

| 驗收項目 | 狀態 |
|---|---|
| Windows Chrome、三角色登入／登出、商品與主要管理畫面 | PASS（無頭瀏覽器操作） |
| 手機尺寸買家頁面 | SIMULATED（Chrome viewport，非手機真機） |
| 隔離 MySQL 備份還原、模擬交易與短時間 API 查詢 | PASS；範圍及數據見 Phase 3 紀錄 |
| 圖片上傳儲存與清理安全測試 | SIMULATED／Mock；沿用 Phase 2 證據 |
| 真實 GCS IAM／Generation、Android／iPhone 真機、完整瀏覽器矩陣 | NOT RUN |
| SRS 的 100 帳號／1,000 商品／20 並行效能標準 | NOT RUN；小樣本不等同容量驗收 |

驗收證據：[Phase 1](docs/acceptance/phase1-docker-mysql.json)、[Phase 2](docs/acceptance/phase2-local.json)、[Phase 3](docs/acceptance/phase3-local.json)。未在本階段重跑所有歷史測試。

[弱點追蹤](docs/security/batch6-dependency-review.json) 仍保留 **7 個未解公告（5 Moderate、2 Low）**，涉及 Pygments、multidict、pytest、Bleach、OpenTelemetry。本機核心流程通過不代表漏洞已修補、風險已接受或正式安全驗收通過；公開服務前仍需完成後續安全處置。
