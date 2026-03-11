# app/services/rag_service.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma

# 引入定義好的模型
from app.models.chat_message import ChatMessage

# 載入環境變數
load_dotenv()

class RAGService:
    def __init__(self):
        # 1. 初始化 Embedding 模型 (用於向量檢索)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        # 2. 載入向量資料庫 (目錄需與同步腳本 scripts/vector_sync.py 一致)
        # 如果目錄不存在，Chroma 會自動建立一個空的
        self.vector_db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embeddings
        )

        # 3. 初始化 Gemini 2.0 Flash 模型
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.7,  # 適度的創造力，適合咖啡推薦
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

    async def get_response(self, db: AsyncSession, user_id: int, query: str) -> str:
        """
        核心邏輯：檢索知識 + 讀取歷史 -> 產生回覆 -> 儲存紀錄
        """

        # --- A. 歷史記憶處理 (從 MySQL 抓取) ---
        # 抓取該使用者最近 5 筆訊息，確保對話連貫
        history_records = db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.created_at.desc()).limit(5).all()

        # 將資料庫紀錄轉為字串格式，順序改為從舊到新 (reversed)
        history_context = ""
        for msg in reversed(history_records):
            role_label = "使用者" if msg.role == "user" else "AI"
            history_context += f"{role_label}: {msg.content}\n"

        # --- B. 知識檢索 (從 ChromaDB 抓取) ---
        # 根據提問，找尋資料庫中最相關的 3 個咖啡商品資訊
        docs = self.vector_db.similarity_search(query, k=3)
        product_context = "\n".join([doc.page_content for doc in docs])

        # --- C. 組合 Prompt (System Instruction) ---
        system_prompt = f"""
        你是一位專業且親切的 Coffee Hub 咖啡顧問。
        請根據以下提供的【咖啡產品資訊】與【對話歷史】來精確回答使用者的問題。

        回答規範：
        1. 如果【咖啡產品資訊】中沒有相關內容，請誠實告知，並根據咖啡常識給予一般性建議。
        2. 盡量根據使用者的口味偏好推薦適合的咖啡。
        3. 回答必須使用繁體中文。

        【咖啡產品資訊】:
        {product_context}

        【對話歷史】:
        {history_context}
        """

        # --- D. 呼叫 Gemini 2.0 Flash ---
        response = await self.llm.ainvoke([
            ("system", system_prompt),
            ("human", query)
        ])
        ai_content = response.content

        # --- E. 儲存對話紀錄 (存入 MySQL) ---
        try:
            # 儲存使用者的提問
            user_msg = ChatMessage(user_id=user_id, role="user", content=query)
            # 儲存 AI 的回覆
            ai_msg = ChatMessage(user_id=user_id, role="model", content=ai_content)

            db.add(user_msg)
            db.add(ai_msg)
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"資料庫儲存失敗: {e}")

        return ai_content

# 單例模式方便在 API 路由中直接 import 使用
rag_service = RAGService()