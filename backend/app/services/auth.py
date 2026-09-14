"""
Cartify Authentication Service (Module 1)

Business logic for:
- User registration (enforcing CUSTOMER role, unique email/phone)
- Secure login (timing-attack resistant, generic errors)
- Token refresh (rotation, family tracking, reuse detection)
- Logout (token revocation)
- Forgot password (enumeration-safe, 15-minute expiring tokens)
- Reset password (single-use validation, hash update, session invalidation)
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import CartifyException, UnauthorizedError
from app.core.security import (
    UserRole,
    create_access_token,
    generate_secure_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.db.base import generate_uuid
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse

logger = logging.getLogger("cartify.auth")

class AuthService:
    @classmethod
    async def register(
        cls, db: AsyncSession, data: RegisterRequest
    ) -> Tuple[TokenResponse, str]:
        """
        Registers a new user. Always assigns CUSTOMER role.
        Returns (TokenResponse, raw_refresh_token).
        """
        name = data.name or data.full_name or ""
        email = data.email.lower().strip()
        phone = (data.phone or data.mobile or "").strip() or None

        # Check existing email
        existing_email = await UserRepository.get_by_email(db, email)
        if existing_email:
            raise CartifyException(
                status_code=409,
                detail="A user with this email address already exists.",
                code="EMAIL_ALREADY_EXISTS",
            )

        # Check existing phone if provided
        if phone:
            existing_phone = await UserRepository.get_by_phone(db, phone)
            if existing_phone:
                raise CartifyException(
                    status_code=409,
                    detail="A user with this phone number already exists.",
                    code="PHONE_ALREADY_EXISTS",
                )

        # Create user with strict CUSTOMER role
        hashed_pw = get_password_hash(data.password)
        user_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "password_hash": hashed_pw,
            "role": UserRole.CUSTOMER,
            "is_active": True,
            "is_verified": False,
        }
        user = await UserRepository.create(db, user_data)

        # Generate tokens
        access_token = create_access_token(subject=user.id, role=user.role)
        raw_refresh_token = generate_secure_token(32)
        token_hash = hash_token(raw_refresh_token)
        family_id = generate_uuid()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await UserRepository.create_refresh_token(
            db=db,
            user_id=user.id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )

        from app.services.notification_service import NotificationService
        await NotificationService.emit_outbox_event(
            db=db,
            event_type="SECURITY_ALERTS",
            aggregate_type="USER",
            aggregate_id=user.id,
            user_id=user.id,
            payload={
                "user_id": user.id,
                "email": user.email,
                "activity_description": "Account registered successfully",
            },
        )

        user_resp = UserResponse.model_validate(user)
        token_resp = TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            user=user_resp,
        )
        return token_resp, raw_refresh_token

    @classmethod
    async def login(
        cls, db: AsyncSession, data: LoginRequest
    ) -> Tuple[TokenResponse, str]:
        """
        Authenticates user with email/phone and password.
        Uses timing-attack resistant error message.
        Returns (TokenResponse, raw_refresh_token).
        """
        identifier = (data.email or data.identifier or "").strip()
        user = await UserRepository.get_by_email_or_phone(db, identifier)

        # Generic error against account enumeration
        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise CartifyException(
                status_code=403,
                detail="User account has been deactivated.",
                code="ACCOUNT_DEACTIVATED",
            )

        # Issue tokens
        access_token = create_access_token(subject=user.id, role=user.role)
        raw_refresh_token = generate_secure_token(32)
        token_hash = hash_token(raw_refresh_token)
        family_id = generate_uuid()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await UserRepository.create_refresh_token(
            db=db,
            user_id=user.id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )

        user_resp = UserResponse.model_validate(user)
        token_resp = TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            user=user_resp,
        )
        return token_resp, raw_refresh_token

    @classmethod
    async def refresh(
        cls, db: AsyncSession, raw_refresh_token: str
    ) -> Tuple[TokenResponse, str]:
        """
        Validates refresh token, detects reuse of compromised tokens,
        rotates the token, and returns new tokens.
        """
        if not raw_refresh_token:
            raise UnauthorizedError("Refresh token was not provided.")

        token_hash = hash_token(raw_refresh_token)
        token_record = await UserRepository.get_refresh_token_by_hash(db, token_hash)

        if not token_record:
            raise UnauthorizedError("Invalid or unknown refresh token.")

        # Token family reuse detection
        if token_record.revoked_at is not None:
            # Stolen/reused token detected! Invalidate the entire family chain.
            logger.warning(
                f"Refresh token reuse detected for family {token_record.family_id}. Revoking all tokens."
            )
            await UserRepository.revoke_token_family(db, token_record.family_id)
            raise UnauthorizedError("Revoked refresh token presented. Session terminated.")

        # Check expiration
        now = datetime.now(timezone.utc)
        if token_record.expires_at < now:
            await UserRepository.revoke_refresh_token(db, token_record)
            raise UnauthorizedError("Refresh token has expired. Please login again.")

        # Fetch user
        user = await UserRepository.get_by_id(db, token_record.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User account not found or inactive.")

        # Rotate: Revoke current token
        await UserRepository.revoke_refresh_token(db, token_record)

        # Issue new token pair preserving family_id
        access_token = create_access_token(subject=user.id, role=user.role)
        new_raw_refresh = generate_secure_token(32)
        new_token_hash = hash_token(new_raw_refresh)
        new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await UserRepository.create_refresh_token(
            db=db,
            user_id=user.id,
            token_hash=new_token_hash,
            family_id=token_record.family_id,
            expires_at=new_expires_at,
        )

        user_resp = UserResponse.model_validate(user)
        token_resp = TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_refresh,
            token_type="bearer",
            user=user_resp,
        )
        return token_resp, new_raw_refresh

    @classmethod
    async def logout(cls, db: AsyncSession, raw_refresh_token: Optional[str]) -> None:
        """Revokes the presented refresh token."""
        if not raw_refresh_token:
            return

        token_hash = hash_token(raw_refresh_token)
        token_record = await UserRepository.get_refresh_token_by_hash(db, token_hash)
        if token_record and token_record.revoked_at is None:
            await UserRepository.revoke_refresh_token(db, token_record)

    @classmethod
    async def forgot_password(cls, db: AsyncSession, email: str) -> Optional[str]:
        """
        Generates a 15-minute single-use password reset token if account exists.
        Returns the raw token for logging/testing (email sending in production).
        Always returns safely to protect against user enumeration.
        """
        user = await UserRepository.get_by_email(db, email.lower().strip())
        if not user or not user.is_active:
            # Return None silently to protect against user enumeration
            return None

        # Invalidate existing pending tokens
        await UserRepository.invalidate_existing_reset_tokens(db, user.id)

        # Create single-use token valid for 15 minutes
        raw_token = generate_secure_token(32)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
        )

        await UserRepository.create_password_reset_token(
            db=db,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        from app.services.notification_service import NotificationService
        await NotificationService.emit_outbox_event(
            db=db,
            event_type="PASSWORD_RESET",
            aggregate_type="USER",
            aggregate_id=user.id,
            user_id=user.id,
            payload={
                "user_id": user.id,
                "email": user.email,
                "reset_code": "RESET_REQUESTED",
            },
        )

        logger.info(f"Password reset token generated for user {user.id}")
        return raw_token

    @classmethod
    async def reset_password(
        cls, db: AsyncSession, raw_token: str, new_password: str
    ) -> None:
        """
        Validates reset token, updates password hash, marks token used,
        and terminates all active refresh sessions for the user.
        """
        token_hash = hash_token(raw_token)
        reset_token = await UserRepository.get_valid_password_reset_token(db, token_hash)

        if not reset_token:
            raise CartifyException(
                status_code=400,
                detail="Invalid or expired password reset link.",
                code="INVALID_RESET_TOKEN",
            )

        user = await UserRepository.get_by_id(db, reset_token.user_id)
        if not user:
            raise CartifyException(
                status_code=404,
                detail="Associated user account not found.",
                code="USER_NOT_FOUND",
            )

        # Mark token as used
        await UserRepository.mark_password_reset_token_used(db, reset_token)

        # Update password hash
        user.password_hash = get_password_hash(new_password)

        from app.services.notification_service import NotificationService
        await NotificationService.emit_outbox_event(
            db=db,
            event_type="SECURITY_ALERTS",
            aggregate_type="USER",
            aggregate_id=user.id,
            user_id=user.id,
            payload={
                "user_id": user.id,
                "email": user.email,
                "activity_description": "Password was reset successfully",
            },
        )

        await db.commit()

        # Invalidate all active sessions for security
        await UserRepository.revoke_all_user_tokens(db, user.id)
