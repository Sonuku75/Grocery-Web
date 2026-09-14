"""
Cartify Security Headers Middleware (Module 15.4)

Enforces mandatory HTTP security headers across all API responses:
- X-Content-Type-Options: nosniff (MIME sniffing defense)
- X-Frame-Options: DENY (Clickjacking protection)
- Referrer-Policy: strict-origin-when-cross-origin (Privacy protection)
- Permissions-Policy: camera=(), microphone=(), geolocation=() (Least privilege feature policy)
- Cache-Control: no-store, no-cache, must-revalidate, private (Prevents intermediate caching of private data)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Baseline defensive security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Sensitive account and auth routes must never be cached by shared proxies or browsers
        path = request.url.path
        if "/api/v1/account" in path or "/api/v1/auth" in path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response
