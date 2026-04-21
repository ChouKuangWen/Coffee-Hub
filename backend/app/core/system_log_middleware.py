# app/core/system_log_middleware.py
import time
from fastapi import Request
from app.core.logger import system_logger

async def system_log_middleware(request: Request, call_next):
    """
    Middleware：記錄「系統層級」的 log（System Log）

    設計目的：
    - 記錄每一個 request 的行為（method / path / status）
    - 記錄 latency（效能分析）
    - 搭配 request_id 做 tracing

    注意：
    - 只做觀測，不寫 business logic
    - 不應該操作 DB
    """

    # 取得 request_id（如果沒有就給預設值）
    request_id = getattr(request.state, "request_id", "-")

    # 記錄開始時間
    start_time = time.time()

    # 取得 client IP（如果有的話）
    client_ip = request.client.host if request.client else "-"

    try:
        # 呼叫下一層（可能是 endpoint 或其他 middleware）
        response = await call_next(request)

        # 計算處理時間
        process_time = time.time() - start_time

        # 記錄成功 log（INFO）
        system_logger.info({
            "request_id": request_id,
            "user_id": getattr(request.state, "user_id", None),  # 如果有 user_id 就記錄，沒有就 None
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "process_time": round(process_time, 4),
            "client_ip": client_ip,
            "query_params": str(request.query_params)
        })

        return response

    except Exception as e:
        # 發生錯誤時記錄 ERROR log
        process_time = time.time() - start_time

        system_logger.error({
            "request_id": request_id,
            "user_id": getattr(request.state, "user_id", None),
            "error": str(e),
            "path": request.url.path,
            "process_time": round(process_time, 4),
            "client_ip": client_ip,
            "query_params": str(request.query_params)
        })

        # 一定要 re-raise，不然 FastAPI 會吃掉錯誤
        raise