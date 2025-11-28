# 使用官方 Python 映像作為基底
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝依賴
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案進容器
COPY . .

# 設定環境變數（防止 Python 輸出被快取）
ENV PYTHONUNBUFFERED=1

ENV PORT=8080
# FastAPI 入口點 (以 Uvicorn 啟動)
# ⚠️ Cloud Run 預設監聽 8080，所以要讓程式綁定該 port
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --worker-class uvicorn.workers.UvicornWorker app.main:app