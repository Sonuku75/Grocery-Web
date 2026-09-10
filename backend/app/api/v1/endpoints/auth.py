from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_reader, get_db_writer, rate_limit
from app.models.user import User
from app.schemas.auth import LoginPayload, RegisterPayload, TokenResponse, UserResponse
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter()

@router.post(
    "/register",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(limit=10, window_seconds=60))],
    summary="Register new user account",
)
async def register(
    data: RegisterPayload,
    db: AsyncSession = Depends(get_db_writer),
):
    token_response = await AuthService.register(db=db, data=data)
    return ApiResponse[TokenResponse](
        success=True,
        data=token_response,
        message="Account registered successfully.",
    )

@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    dependencies=[Depends(rate_limit(limit=30, window_seconds=60))],
    summary="User login with email or mobile and password",
)
async def login(
    data: LoginPayload,
    db: AsyncSession = Depends(get_db_reader),
):
    token_response = await AuthService.login(db=db, data=data)
    return ApiResponse[TokenResponse](
        success=True,
        data=token_response,
        message="Login successful.",
    )

@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return ApiResponse[UserResponse](
        success=True,
        data=UserResponse.model_validate(current_user),
        message="Profile retrieved.",
    )
