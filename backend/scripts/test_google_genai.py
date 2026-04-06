import os
import asyncio
from dotenv import load_dotenv
import google.genai as genai

# 載入 .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# 建立 Client，強制使用 v1
client = genai.Client(
    api_key=api_key,
    http_options={'api_version': 'v1'}
)

async def test_models():
    print("="*50)
    print("[*] 測試 Google GenAI API v1")

    # 列出可用模型
    print("[*] 可用模型清單：")
    try:
        for m in client.models.list():   # 直接迭代 Pager
            print(f"- {m.name}")
    except Exception as e:
        print(f"[!] 列出模型失敗: {e}")

    # 測試文字生成
    try:
        response = await client.aio.models.generate_content(
            model="gemini-1.5-flash",
            contents="請用三個字描述咖啡的風味"
        )
        print("\n[✓] 文字生成結果：")
        print(response.text)
    except Exception as e:
        print(f"[!] generate_content 錯誤: {e}")

    # 測試 Embedding
    try:
        embed_response = client.models.embed_content(
            model="text-embedding-004",
            contents="咖啡風味測試"
        )
        print("\n[✓] Embedding 向量長度：", len(embed_response.embedding.values))
    except Exception as e:
        print(f"[!] embed_content 錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(test_models())

