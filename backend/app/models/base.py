from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine #建立非同步資料庫引擎
from sqlalchemy.orm import sessionmaker, declarative_base #產生DB session、建立ORM基底類別
from dotenv import load_dotenv
import os
load_dotenv()

#定義連線資料庫的基本資訊
db_user = os.getenv("db_user")
db_password = os.getenv("db_password")
db_host = os.getenv("db_host")
db_port = os.getenv("db_port")
db_name = os.getenv("db_name")

#SQLAlchemy 資料庫連線字串 mysql+asyncmy://帳號:密碼@主機:埠號/資料庫?參數
db_url = f"mysql+asyncmy://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"

#建立資料庫連線引擎，建立session 宣告ORM
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

