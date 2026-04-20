# app/core/request_id_middleware.py
import uuid
from fastapi import Request

async def request_id_middleware(request: Request, call_next):
    """
    Middleware：產生 request_id，並綁定到整個 request lifecycle

    設計目的：
    - 每個 request 都有唯一 ID（trace 用）
    - 後續 logging（system / business / audit）可以串起來
    - 回傳給前端（方便 debug / trace）

    使用位置：
    - 必須放在「最外層 middleware」
    """

    #  產生唯一 request_id
    request_id = str(uuid.uuid4())

    #  綁定到 request.state
    request.state.request_id = request_id

    #  繼續往下執行（進入下一層 middleware / endpoint）
    response = await call_next(request)

    #  回傳給 client（方便前端 / tracing）
    response.headers["X-Request-ID"] = request_id

    return response