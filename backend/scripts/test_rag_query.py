import os
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
import google.genai as genai

# 載入 .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# 配置
CHROMA_DIR = "./chroma_db"

# 1. 核心修正：強制指定 API 版本為 v1，避開出錯的 v1beta
# 並且不要使用 'models/' 前綴
client = genai.Client(
    api_key=api_key,
    http_options={'api_version': 'v1'}
)

async def get_ai_refined_query(user_query):
    """意圖解析"""
    prompt = f"你是一位咖啡顧問。請將需求轉換為 3 個正面關鍵字（如：不要酸 -> 堅果,巧克力,深焙）。需求：{user_query}"
    try:
        # 模型名稱不加 models/
        response = await client.aio.models.generate_content(
            model="models/gemini-2.5-flash-lite", 
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"[!] 意圖解析失敗: {e}")
        return user_query

async def get_ai_expert_response(user_query, context_docs):
    """
    專業店長 RAG 回覆系統
    整合：精簡輸出、拒答無關內容、Gemini 2.5 Flash Lite
    """
    
    # 1. 基礎檢查：如果向量庫沒撈到東西，直接拒絕，省下 API 消耗
    if not context_docs:
        return "抱歉，目前店內沒有符合您需求的咖啡豆喔！要不要試試其他的？"

    # 2. 格式化產品資訊，讓 LLM 容易閱讀
    product_info = "\n\n".join([f"【產品資訊】\n{doc.page_content}" for doc in context_docs])
    
    # 3. 嚴謹的 System Prompt 設計
    prompt = f"""
    # Role
    你是一位親切、專業且說話精簡的精品咖啡店店長。

    # Task
    請根據提供的【產品資訊】，回答客人的提問：『{user_query}』。

    # Constraints (嚴格遵守)
    1. 僅限根據提供的資訊回答。如果資訊中沒有相關產品，或問題與咖啡完全無關，請回答：「抱歉，我只能提供店內的咖啡建議喔！」
    2. 回答必須精簡。禁止長篇大論，總字數控制在 120 字以內。
    3. 內容結構：提及豆名、解釋為何符合需求（如：焙度、風味標籤）、最後附上價格。
    4. 語氣要像在店門口熱情招待客人，但直接講重點。

    # 產品資訊內容：
    {product_info}
    """

    try:
        # 4. 冷靜期與非同步呼叫
        await asyncio.sleep(1) 
        
        # 使用最新的 2.5 Flash Lite 模型
        response = await client.aio.models.generate_content(
            model="models/gemini-2.5-flash-lite",
            contents=prompt
        )
        
        # 確保回傳內容不為空，並去除多餘空格
        answer = response.text.strip()
        return answer if answer else "店長正在思考中，請稍後再問我一次。"

    except Exception as e:
        # 5. 錯誤處理：對外顯示親切訊息，對內 log 錯誤
        print(f"[!] API 呼叫失敗: {e}")
        return "店長現在去補貨了（系統忙碌中），請稍微等我一下喔！"

async def test_query():
    print("="*50)
    print("[*] 正在啟動穩定版 RAG 測試 (API Version: v1)")

    # 2. Embedding 修正：同樣去掉 'models/'
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key,
        api_version="v1",
        task_type="retrieval_query"
    )

    if not os.path.exists(CHROMA_DIR):
        print(f"[!] 找不到向量庫")
        return
    
    vector_db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

    user_query = "我想學程式"
    refined_query = await get_ai_refined_query(user_query)
    print(f"[*] 優化詞: {refined_query}")

    loop = asyncio.get_event_loop()
    docs = await loop.run_in_executor(None, lambda: vector_db.similarity_search(refined_query, k=2))

    expert_answer = await get_ai_expert_response(user_query, docs)
    print(f"\n[✓] 建議：\n{expert_answer}")

if __name__ == "__main__":
    asyncio.run(test_query())