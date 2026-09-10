from typing import Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CartifyException, NotFoundError
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import LoginPayload, RegisterPayload, TokenResponse, UserResponse

class AuthService:
    @classmethod
    async def register(cls, db: AsyncSession, data: RegisterPayload) -> TokenResponse:
        # Check if email or mobile exists
        stmt = select(User).where(or_(User.email == data.email, User.mobile == data.mobile))
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            if existing.email == data.email:
                raise CartifyException(
                    status_code=409,
                    detail="A user with this email address already exists.",
                    code="EMAIL_ALREADY_EXISTS",
                )
            raise CartifyException(
                status_code=409,
                detail="A user with this mobile number already exists.",
                code="MOBILE_ALREADY_EXISTS",
            )

        hashed_pw = get_password_hash(data.password)
        user = User(
            email=data.email,
            mobile=data.mobile,
            full_name=data.full_name,
            hashed_password=hashed_pw,
            role="customer",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        token = create_access_token(subject=user.id, role=user.role)
        user_resp = UserResponse.model_validate(user)
        return TokenResponse(access_token=token, user=user_resp)

    @classmethod
    async def login(cls, db: AsyncSession, data: LoginPayload) -> TokenResponse:
        stmt = select(User).where(
            or_(User.email == data.identifier, User.mobile == data.identifier),
            User.is_active == True,
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise CartifyException(
                status_code=401,
                detail="Invalid credentials provided.",
                code="INVALID_CREDENTIALS",
            )

        token = create_access_token(subject=user.id, role=user.role)
        user_resp = UserResponse.model_validate(user)
        return TokenResponse(access_token=token, user=user_resp)

    @classmethod
    async def get_user_by_id(cls, db: AsyncSession, user_id: str) -> UserResponse:
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", user_id)
        return UserResponse.model_validate(user)
