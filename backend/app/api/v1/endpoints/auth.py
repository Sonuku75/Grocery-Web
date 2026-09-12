"""
Cartify Authentication Endpoints (Module 1)

Endpoints:
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- POST /api/v1/auth/forgot-password
- POST /api/v1/auth/reset-password
"""

from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import rate_limit
from app.core.config import settings
from app.core.database import get_db_writer
from app.core.errors import UnauthorizedError
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.common import ApiResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

def set_refresh_cookie(response: Response, raw_token: str) -> None:
    """Sets an HttpOnly, SameSite=Lax cookie for web browsers."""
    response.set_cookie(
        key="cartify_refresh_token",
        value=raw_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
    )

def clear_refresh_cookie(response: Response) -> None:
    """Clears the refresh cookie on logout or password reset."""
    response.delete_cookie(
        key="cartify_refresh_token",
        path="/",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )

@router.post(
    "/register",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(limit=settings.RATE_LIMIT_REGISTER, window_seconds=60))],
)
async def register(
    payload: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[TokenResponse]:
    """
    Register a new customer account.
    Returns JWT access and refresh tokens, and sets HttpOnly cookie for web browsers.
    """
    token_resp, raw_refresh = await AuthService.register(db=db, data=payload)
    set_refresh_cookie(response, raw_refresh)
    return ApiResponse(
        success=True,
        message="Account registered successfully.",
        data=token_resp,
    )

@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    dependencies=[Depends(rate_limit(limit=settings.RATE_LIMIT_LOGIN, window_seconds=60))],
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[TokenResponse]:
    """
    Authenticate with email/phone and password.
    Returns JWT access and refresh tokens, and sets HttpOnly cookie for web browsers.
    """
    token_resp, raw_refresh = await AuthService.login(db=db, data=payload)
    set_refresh_cookie(response, raw_refresh)
    return ApiResponse(
        success=True,
        message="Login successful.",
        data=token_resp,
    )

@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
)
async def refresh_tokens(
    response: Response,
    payload: Optional[RefreshRequest] = None,
    cartify_refresh_token: Optional[str] = Cookie(None, alias="cartify_refresh_token"),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[TokenResponse]:
    """
    Refresh access token using token rotation.
    Accepts refresh token from either HttpOnly cookie or JSON body.
    """
    raw_token = (payload.refresh_token if payload and payload.refresh_token else None) or cartify_refresh_token
    if not raw_token:
        raise UnauthorizedError("No refresh token provided in cookie or payload.")

    token_resp, new_raw_refresh = await AuthService.refresh(db=db, raw_refresh_token=raw_token)
    set_refresh_cookie(response, new_raw_refresh)
    return ApiResponse(
        success=True,
        message="Token refreshed successfully.",
        data=token_resp,
    )

@router.post(
    "/logout",
    response_model=ApiResponse[MessageResponse],
)
async def logout(
    response: Response,
    payload: Optional[RefreshRequest] = None,
    cartify_refresh_token: Optional[str] = Cookie(None, alias="cartify_refresh_token"),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[MessageResponse]:
    """
    Revokes the active refresh token and clears the authentication cookie.
    """
    raw_token = (payload.refresh_token if payload and payload.refresh_token else None) or cartify_refresh_token
    await AuthService.logout(db=db, raw_refresh_token=raw_token)
    clear_refresh_cookie(response)
    return ApiResponse(
        success=True,
        message="Logged out successfully.",
        data=MessageResponse(message="Logged out successfully."),
    )

@router.post(
    "/forgot-password",
    response_model=ApiResponse[MessageResponse],
    dependencies=[Depends(rate_limit(limit=settings.RATE_LIMIT_FORGOT_PASSWORD, window_seconds=60))],
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[MessageResponse]:
    """
    Generates a password reset token.
    Always returns a generic success message to prevent user enumeration attacks.
    """
    await AuthService.forgot_password(db=db, email=payload.email)
    return ApiResponse(
        success=True,
        message="If an account exists with this email, a password reset link has been sent.",
        data=MessageResponse(
            message="If an account exists with this email, a password reset link has been sent."
        ),
    )

@router.post(
    "/reset-password",
    response_model=ApiResponse[MessageResponse],
    dependencies=[Depends(rate_limit(limit=settings.RATE_LIMIT_RESET_PASSWORD, window_seconds=60))],
)
async def reset_password(
    payload: ResetPasswordRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[MessageResponse]:
    """
    Resets account password using a single-use token, and revokes all active sessions.
    """
    await AuthService.reset_password(
        db=db, raw_token=payload.token, new_password=payload.new_password
    )
    clear_refresh_cookie(response)
    return ApiResponse(
        success=True,
        message="Password has been reset successfully. Please login with your new password.",
        data=MessageResponse(
            message="Password has been reset successfully. Please login with your new password."
        ),
    )
