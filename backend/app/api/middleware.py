import asyncio
import logging
import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.errors import CartifyException

logger = logging.getLogger("cartify.access")

class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.perf_counter()
        
        try:
            # Enforce strict request timeout to prevent hanging connections under 100k load
            response = await asyncio.wait_for(
                call_next(request),
                timeout=settings.REQUEST_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request Timeout: method={request.method} path={request.url.path} "
                f"duration_ms={duration_ms:.2f} request_id={request_id}"
            )
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "success": False,
                    "error": "Request timed out. The server was unable to complete processing within the allocated time window.",
                    "code": "GATEWAY_TIMEOUT",
                    "request_id": request_id,
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Response-Time-Ms": f"{duration_ms:.2f}",
                },
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"Unhandled Exception: method={request.method} path={request.url.path} "
                f"duration_ms={duration_ms:.2f} request_id={request_id} error={str(e)}"
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": "An unexpected internal server error occurred.",
                    "code": "INTERNAL_SERVER_ERROR",
                    "request_id": request_id,
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Response-Time-Ms": f"{duration_ms:.2f}",
                },
            )

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        # High-traffic structured log
        logger.info(
            f"{request.method} {request.url.path} status={response.status_code} "
            f"duration_ms={duration_ms:.2f} request_id={request_id}"
        )
        return response

def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CartifyException)
    async def cartify_exception_handler(request: Request, exc: CartifyException):
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "code": exc.code,
                "extra": exc.extra,
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )
