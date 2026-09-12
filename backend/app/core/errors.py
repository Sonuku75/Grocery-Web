import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("cartify.errors")

class CartifyException(HTTPException):
    """
    Base domain exception for Cartify application.
    """
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "An unexpected server error occurred.",
        code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None,
        detail: Optional[str] = None,
    ):
        msg = detail if detail is not None else message
        super().__init__(status_code=status_code, detail=msg)
        self.code = code
        self.message = msg
        self.details = details

class NotFoundError(CartifyException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"{resource} with identifier '{identifier}' was not found.",
            code="RESOURCE_NOT_FOUND",
        )

class UnauthorizedError(CartifyException):
    def __init__(self, message: str = "Authentication credentials were not provided or are invalid."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            code="UNAUTHORIZED",
        )

class ForbiddenError(CartifyException):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            code="FORBIDDEN",
        )

class RateLimitExceededError(CartifyException):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message="Rate limit exceeded. Please slow down your requests.",
            code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
        )

def setup_exception_handlers(app: FastAPI) -> None:
    """
    Registers centralized exception handlers to ensure 100% consistent error responses.
    Format:
    {
      "success": false,
      "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": ...
      },
      "request_id": "..."
    }
    """

    @app.exception_handler(CartifyException)
    async def cartify_exception_handler(request: Request, exc: CartifyException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
              "success": False,
              "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
              },
              "request_id": request_id,
            },
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        # Format field-level validation errors cleanly
        formatted_errors = []
        for err in exc.errors():
            formatted_errors.append({
                "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg"),
                "type": err.get("type"),
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request payload failed validation.",
                    "details": formatted_errors,
                },
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_SERVER_ERROR",
            503: "SERVICE_UNAVAILABLE",
            504: "GATEWAY_TIMEOUT",
        }
        code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": code,
                    "message": str(exc.detail),
                },
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        # Never expose internal SQL syntax or database credentials to client
        logger.error(f"Database error during request {request_id}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "A database operation failed while processing the request.",
                },
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.error(f"Unhandled exception during request {request_id}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred.",
                },
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id} if request_id else {},
        )
