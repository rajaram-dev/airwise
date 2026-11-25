"""Security middleware: headers, request size limit, caching policy and rate limiter."""

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger("airwise.access")

MAX_BODY_BYTES = 16 * 1024
GENERAL_RATE_LIMIT = "60/minute"

limiter = Limiter(key_func=get_remote_address)

APP_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; "
    "form-action 'self'; frame-ancestors 'none'"
)
# FastAPI's interactive docs load Swagger UI from a CDN with an inline bootstrap script.
DOCS_CSP = (
    "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; frame-ancestors 'none'"
)
DOCS_PATHS = ("/docs", "/openapi.json")

SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(self), camera=(), microphone=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}
HSTS = "max-age=31536000; includeSubDomains"
# Revalidate on every load (cheap 304s via ETag) so updates show up immediately.
STATIC_CACHE = "public, no-cache"

CallNext = Callable[[Request], Awaitable[Response]]


def _body_too_large(request: Request) -> bool:
    length = request.headers.get("content-length")
    if length is None:
        return False
    return not length.isdigit() or int(length) > MAX_BODY_BYTES


def _is_https(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"


def _apply_headers(request: Request, response: Response) -> None:
    path = request.url.path
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    response.headers["Content-Security-Policy"] = (
        DOCS_CSP if path.startswith(DOCS_PATHS) else APP_CSP
    )
    if _is_https(request):
        response.headers["Strict-Transport-Security"] = HSTS
    if path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    elif path.startswith(("/css/", "/js/", "/img/")):
        response.headers["Cache-Control"] = STATIC_CACHE


async def security_middleware(request: Request, call_next: CallNext) -> Response:
    """Reject oversized bodies, add security headers and log a PII-free access line."""
    start = time.perf_counter()
    if _body_too_large(request):
        response: Response = JSONResponse(
            status_code=413,
            content={"error": "payload_too_large", "message": "Request body is too large."},
        )
    else:
        response = await call_next(request)
    _apply_headers(request, response)
    logger.info(
        "%s %s %s %.0fms",
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - start) * 1000,
    )
    return response
