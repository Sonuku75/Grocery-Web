"""
Cartify Request Tracing & Timeout Middleware (Module 0)

Assigns unique X-Request-ID to incoming requests, tracks duration,
enforces request timeouts, and injects diagnostic response headers.
"""

import asyncio
import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = logging.getLogger("cartify.access")

class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate unique Request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            # Enforce server-side request timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=settings.REQUEST_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"TIMEOUT: {request.method} {request.url.path} "
                f"duration_ms={duration_ms:.2f} request_id={request_id}"
            )
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "success": False,
                    "error": {
                        "code": "GATEWAY_TIMEOUT",
                        "message": f"Request processing exceeded timeout limit of {settings.REQUEST_TIMEOUT_SECONDS}s.",
                    },
                    "request_id": request_id,
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Response-Time-Ms": f"{duration_ms:.2f}",
                },
            )

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Inject diagnostic response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        # Structured access logging
        logger.info(
            f"{request.method} {request.url.path} status={response.status_code} "
            f"duration_ms={duration_ms:.2f} request_id={request_id}"
        )

        return response
