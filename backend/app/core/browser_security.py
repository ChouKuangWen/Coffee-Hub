"""Signed double-submit CSRF; no exemptions for cookie-authenticated writes."""
import hashlib
import hmac
import logging
import secrets
import time
from urllib.parse import urlsplit
from starlette.responses import JSONResponse
from app.core.config import settings

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
logger = logging.getLogger(__name__)


def cookie_options():
    secure = getattr(settings, "COOKIE_SECURE", True)
    same = getattr(settings, "COOKIE_SAMESITE", "lax").lower()
    env = getattr(settings, "APP_ENV", "development")
    if same not in {"lax", "strict", "none"} or (same == "none" and not secure):
        raise ValueError("Unsafe cookie configuration")
    if not secure and env not in {"development", "test"}:
        raise ValueError("HTTPS cookies are required outside development/test")
    return dict(secure=secure, httponly=True, samesite=same, path="/")


def allowed_origins():
    origins = getattr(settings, "CORS_ORIGINS", ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:3000"])
    env = getattr(settings, "APP_ENV", "development")
    for origin in origins:
        parsed = urlsplit(origin)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment or parsed.path or "*" in origin
                or parsed.hostname in {"storage.googleapis.com"}
                or (parsed.scheme != "https" and (env not in {"development", "test"}
                    or parsed.hostname not in {"localhost", "127.0.0.1", "[::1]", "::1"}))):
            raise ValueError("CORS requires explicit trusted frontend origins")
    return origins


def new_csrf(session=None):
    payload = f"{int(time.time())}.{secrets.token_hex(32)}"
    binding = hashlib.sha256((session or "anonymous").encode()).hexdigest()
    signature = hmac.new(settings.SECRET_KEY.encode(), ("csrf:" + binding + ":" + payload).encode(), hashlib.sha256).hexdigest()
    return payload + "." + signature


def valid_csrf(cookie, header, session=None):
    if (not cookie or not header or len(cookie) > 200 or len(header) > 200
            or not cookie.isascii() or not header.isascii() or not hmac.compare_digest(cookie, header)):
        return False
    try:
        issued, nonce, signature = cookie.split(".")
        if len(nonce) != 64 or not 0 <= time.time() - int(issued) <= 3600:
            return False
        binding = hashlib.sha256((session or "anonymous").encode()).hexdigest()
        expected = hmac.new(settings.SECRET_KEY.encode(), f"csrf:{binding}:{issued}.{nonce}".encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
    except (ValueError, TypeError):
        return False


async def browser_security(request, call_next):
    if request.method not in SAFE_METHODS:
        origin = request.headers.get("origin")
        # Bearer authentication without ambient credentials is not vulnerable to CSRF.
        bearer_only = (request.headers.get("authorization", "").lower().startswith("bearer ")
                       and not request.cookies.get("access_token") and not request.cookies.get("refresh_token"))
        if (origin is not None and origin not in allowed_origins()) or (
                not bearer_only and not valid_csrf(request.cookies.get("csrf_token"), request.headers.get("x-csrf-token"), request.cookies.get("refresh_token"))):
            response = JSONResponse({"detail": "CSRF 驗證失敗，請重新整理後再試", "code":"CSRF_REJECTED"}, status_code=403)
        else:
            response = await call_next(request)
    else:
        response = await call_next(request)
    # Denials use a fresh transaction after the endpoint's rollback. No body/token/URL query is logged.
    if response.status_code in (401, 403) and not (request.url.path == "/auth/login" and response.status_code == 401):
        try:
            await persist_denial(request, response.status_code)
        except Exception as exc:
            logger.error("security_audit_unavailable request_id=%s error=%s", getattr(request.state, "request_id", None), type(exc).__name__)
            return JSONResponse({"detail":"Security audit unavailable; retry later"}, status_code=503)
    if request.url.path.startswith(("/auth", "/users", "/audit-logs", "/orders", "/order_items")):
        response.headers["Cache-Control"] = "no-store"
    return response


async def persist_denial(request, status_code):
    from app.models.base import get_db
    from app.services.audit_log_service import record_required_action
    provider = request.app.dependency_overrides.get(get_db, get_db)
    async for db in provider():
        try:
            await record_required_action(db, request, user_id=getattr(request.state, "user_id", None),
                category="SECURITY", action="ACCESS_DENIED", target_type="API", target_id=None, status="DENIED",
                after_data={"method":request.method, "route":getattr(request.scope.get("route"), "path", "unmatched"), "status_code":status_code})
            await db.commit()
        except Exception:
            await db.rollback()
            raise
