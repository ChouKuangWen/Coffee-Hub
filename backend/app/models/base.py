from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine #建立非同步資料庫引擎
from sqlalchemy.orm import sessionmaker, declarative_base #產生DB session、建立ORM基底類別
from dotenv import load_dotenv
import os
load_dotenv()

#定義連線資料庫的基本資訊
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

# Cloud Run 中，我們透過這個變數連線到 Cloud SQL Proxy
cloud_sql_conn_name = os.getenv("DB_CONNECTION_NAME")


# 雲端/本地 環境判斷
if cloud_sql_conn_name:
    # 模式 1:Cloud Run開發
    # Cloud Run (使用 Unix Socket)，Cloud SQL Proxy 會在 /cloudsql/ 建 Socket 檔案
    print(f"INFO: Using Cloud SQL Proxy via Unix Socket: {cloud_sql_conn_name}")
    # 注意: asyncmy/PyMySQL 驅動程式的 Unix Socket 格式
    # 格式: mysql+asyncmy://<user>:<password>@/<dbname>?unix_socket=/cloudsql/<CONNECTION_NAME>
    db_url = (
        f"mysql+asyncmy://{db_user}:{db_password}@/?"
        f"unix_socket=/cloudsql/{cloud_sql_conn_name}&"
        f"database={db_name}&"  # <--- 將資料庫名稱作為單獨參數
        f"charset=utf8mb4"
    )

else:
    # 模式 2: 本地開發
    # 從 .env 檔案中讀取
    print("本地開發")
    #SQLAlchemy 資料庫連線字串 mysql+asyncmy://帳號:密碼@主機:埠號/資料庫?參數
    db_url = f"mysql+asyncmy://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"

# 建立資料庫連線引擎，建立session 宣告ORM
"""
expire_on_commit 是 True。session.commit() 提交後，所有ORM 物件都會進入「過期」狀態。
當你再次存取這些物件的屬性時，它們會重新從資料庫載入最新的值。
expire_on_commit 設定為 False 時，提交後，ORM 物件不會自動過期。
可以繼續存取這些物件的屬性，而無需再次觸發資料庫查詢來重新載入它們的值。
"""
async_engine = create_async_engine(db_url, echo=True)  #正式環境中，為減少日誌輸出量將echo設定為False
AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

#FastAPI 依賴注入產生一個 DB Session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

