"""
Cartify API Dependencies (Module 1)

Provides:
- Current user authentication from JWT bearer tokens
- Admin authorization enforcement
- Multi-client refresh token resolution (cookie or body)
- Rate limiting dependencies
"""

from typing import Callable, Optional
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_reader, get_db_writer
from app.core.errors import CartifyException, ForbiddenError, UnauthorizedError
from app.core.security import UserRole, decode_access_token
from app.models.user import User
from app.services.rate_limiter import SlidingWindowRateLimiter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_reader),
) -> Optional[User]:
    """Returns authenticated user if a valid bearer token is present, else None."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = payload["sub"]
    stmt = select(User).where(User.id == user_id, User.is_active == True)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_reader),
) -> User:
    """Enforces valid JWT bearer token and returns active user."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload["sub"]
    stmt = select(User).where(User.id == user_id, User.is_active == True)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verifies that authenticated user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    return current_user

async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Restricts access to administrators only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required.",
        )
    return current_user

def rate_limit(limit: int = 100, window_seconds: int = 60) -> Callable:
    """
    Dependency factory that enforces sliding window rate limits per client IP / route.
    """
    async def _rate_limit_dependency(request: Request) -> None:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"

        endpoint_path = request.scope.get("path", "unknown")
        identifier = f"{client_ip}:{endpoint_path}"
        await SlidingWindowRateLimiter.check_and_raise(
            identifier=identifier,
            limit=limit,
            window_seconds=window_seconds,
        )
    return _rate_limit_dependency
