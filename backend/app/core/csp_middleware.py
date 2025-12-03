from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.requests import Request
import secrets
import base64

"""
CSP 中介軟體定義 (Content Security Policy)

此中介軟體為每個請求生成一個唯一的 Nonce (一次性密碼)，
並將其注入到 Content-Security-Policy 標頭中，以及 request.state
供前端模板使用。
"""
class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. 生成一個加密安全的 Nonce (至少 16 bytes)
        #    使用 base64 編碼，使其在 HTTP 標頭中易於傳輸
        nonce = base64.b64encode(secrets.token_bytes(16)).decode('utf-8')

        # 2. 將 Nonce 儲存到 request.state，以便在 HTML 渲染時可以被模板引擎訪問
        request.state.csp_nonce = nonce

        # 3. 注入 Nonce 到 CSP 策略中 (使用 f-string 替換佔位符)
        #    注意: Nonce 必須以單引號括起來，例如: 'nonce-xxxxxxxx'
        csp_policy = (
            "default-src 'self';"
            # 腳本來源: 允許自身來源的腳本，以及使用此 Nonce 的內嵌腳本/外部腳本
            f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net;"
            # 樣式來源: 允許自身來源的樣式，以及使用此 Nonce 的內嵌樣式
            f"style-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net;"
            "img-src 'self' data: https://fastapi.tiangolo.com;"               # 允許自身圖片和 Base64 圖片 (用於小圖標)
            "connect-src 'self';"                 # 允許前端與後端 API (同源) 通訊
            "object-src 'none';"                  # 徹底阻止所有 <object>, <embed> 等插件
            "base-uri 'self';"                    # 限制 <base> 標籤的 URI
        )

        response = await call_next(request)

        # 4. 將 CSP 標頭新增到響應中
        #    如果響應是 HTML 頁面，此標頭將指導瀏覽器安全地執行腳本。
        response.headers["Content-Security-Policy"] = csp_policy

        # 新增 X-Content-Type-Options: nosniff
        response.headers["X-Content-Type-Options"] = "nosniff"

        return response
