# scripts/vector_sync.py
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import select
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# 引用定義好的非同步 Session
from app.models.base import AsyncSessionLocal
from app.models.products import Products

load_dotenv()

# --- 配置區 ---
CHROMA_DIR = "./chroma_db"
SYNC_STATUS_FILE = "scripts/sync_status.json"

class VectorSyncManager:
    def __init__(self):
        # 1. 初始化 Embedding 模型 (翻譯官)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # 2. 初始化向量資料庫 (倉庫)
        self.vector_db = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=self.embeddings
        )

    def get_last_sync_time(self):
        """從 json 讀取上次同步成功的時間點"""
        if os.path.exists(SYNC_STATUS_FILE):
            try:
                with open(SYNC_STATUS_FILE, "r") as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data.get("last_sync"))
            except (json.JSONDecodeError, ValueError):
                pass
        return datetime.min

    def update_sync_status(self, sync_time):
        """將本次同步時間寫入狀態檔案"""
        os.makedirs(os.path.dirname(SYNC_STATUS_FILE), exist_ok=True)
        with open(SYNC_STATUS_FILE, "w") as f:
            json.dump({"last_sync": sync_time.isoformat()}, f)

    async def run(self):
        """執行非同步同步邏輯"""
        last_sync = self.get_last_sync_time()
        current_sync_time = datetime.now()

        print(f"[*] 開始同步任務。上次同步時間: {last_sync}")

        # 3. 使用你定義的 AsyncSessionLocal 進行非同步查詢
        async with AsyncSessionLocal() as db:
            # 抓取在上次同步後有更新過的產品
            stmt = select(Products).where(Products.updated_at > last_sync)
            result = await db.execute(stmt)
            updated_products = result.scalars().all()

            if not updated_products:
                print("[✓] 沒有偵測到變動的產品，同步跳過。")
                return

            print(f"[*] 偵測到 {len(updated_products)} 個變動產品，準備轉換向量並存入 Chroma...")

            documents = []
            ids = []
            for p in updated_products:
                # 組合語意內容
                content = (
                    f"產品名稱: {p.name}\n"
                    f"類別: {p.category}\n"
                    f"描述: {p.description}\n"
                    f"價格: {p.price}"
                )
                
                # 封裝成 LangChain Document
                doc = Document(
                    page_content=content,
                    metadata={"product_id": p.id, "source": "mysql"}
                )
                documents.append(doc)
                # 使用 product_id 作為向量庫 ID，確保更新時會自動覆蓋而非重複
                ids.append(f"prod_{p.id}")

            # 4. 寫入向量資料庫
            # 因為 Chroma 的 add_documents 內部是同步 IO，在非同步迴圈中建議交給 executor 執行
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self.vector_db.add_documents(documents, ids=ids)
            )

            # 5. 更新同步狀態
            self.update_sync_status(current_sync_time)
            print(f"[✓] 同步完成！已更新 {len(updated_products)} 筆資料。")

if __name__ == "__main__":
    manager = VectorSyncManager()
    # 啟動非同步進入點
    asyncio.run(manager.run())