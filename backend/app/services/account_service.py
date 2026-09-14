"""
Cartify Account Service (Module 15.1)

Coordinates sensitive account attribute verification workflows (staged email and phone changes).
Guarantees re-authentication with current password, uniqueness enforcement, and cryptographic OTP verification.
"""

from datetime import datetime, timedelta, timezone
import logging
import secrets
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CartifyException, UnauthorizedError
from app.core.security import hash_token, verify_password
from app.models.account_change_request import ChangeType
from app.models.user import User
from app.repositories.account_change_request import AccountChangeRequestRepository
from app.repositories.user import UserRepository
from app.services.security_event_service import SecurityEventService

logger = logging.getLogger("cartify.account")

CHANGE_TOKEN_EXPIRE_MINUTES = 15


class AccountService:
    @classmethod
    def generate_verification_code(cls) -> str:
        """Generates a secure 6-digit numeric verification OTP."""
        return f"{secrets.randbelow(900000) + 100000}"

    @classmethod
    async def initiate_email_change(
        cls,
        db: AsyncSession,
        user: User,
        new_email: str,
        current_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """
        Initiates staged email change after verifying current password.
        Returns the raw 6-digit OTP code for notification dispatch.
        """
        # 1. Re-authenticate
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedError("Incorrect password. Identity verification required.")

        normalized_email = new_email.strip().lower()

        # 2. Check if identical to current email
        if normalized_email == user.email.lower():
            raise CartifyException(
                status_code=400,
                detail="New email address cannot be the same as your current email.",
                code="EMAIL_UNCHANGED",
            )

        # 3. Check if already taken
        existing = await UserRepository.get_by_email(db, normalized_email)
        if existing:
            raise CartifyException(
                status_code=409,
                detail="This email address is already in use by another account.",
                code="EMAIL_ALREADY_IN_USE",
            )

        # 4. Generate verification code & hash
        raw_code = cls.generate_verification_code()
        token_hash = hash_token(raw_code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=CHANGE_TOKEN_EXPIRE_MINUTES)

        await AccountChangeRequestRepository.create(
            db=db,
            user_id=user.id,
            change_type=ChangeType.EMAIL,
            target_value=normalized_email,
            verification_token_hash=token_hash,
            expires_at=expires_at,
        )

        # 5. Record security event
        await SecurityEventService.record_security_event(
            db=db,
            user_id=user.id,
            event_type="EMAIL_CHANGE_REQUESTED",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"target_email": normalized_email},
        )

        return raw_code

    _otp_attempts_tracker: dict = {}

    @classmethod
    async def _increment_and_check_otp_attempts(
        cls, user_id: str, change_type: str
    ) -> int:
        """
        Increments failed verification attempts in Redis (falling back to memory).
        Returns the current failed attempt count.
        """
        key = f"otp_attempts:{user_id}:{change_type}"
        try:
            from app.core.redis import redis_client
            count = await redis_client.incr(key)
            if count == 1:
                from app.core.config import settings
                await redis_client.expire(key, settings.OTP_EXPIRE_MINUTES * 60)
            return count
        except Exception:
            cls._otp_attempts_tracker[key] = cls._otp_attempts_tracker.get(key, 0) + 1
            return cls._otp_attempts_tracker[key]

    @classmethod
    async def _clear_otp_attempts(cls, user_id: str, change_type: str) -> None:
        key = f"otp_attempts:{user_id}:{change_type}"
        try:
            from app.core.redis import redis_client
            await redis_client.delete(key)
        except Exception:
            cls._otp_attempts_tracker.pop(key, None)

    @classmethod
    async def verify_email_change(
        cls,
        db: AsyncSession,
        user: User,
        verification_code: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Verifies the staged email change OTP, updates user.email, and records audit event.
        Enforces maximum attempt bounds and revokes other sessions upon completion.
        """
        pending = await AccountChangeRequestRepository.get_active_by_user_and_type(
            db=db, user_id=user.id, change_type=ChangeType.EMAIL
        )

        if not pending:
            raise CartifyException(
                status_code=400,
                detail="Invalid or expired verification code.",
                code="INVALID_VERIFICATION_CODE",
            )

        code_hash = hash_token(verification_code.strip())
        if pending.verification_token_hash != code_hash:
            from app.core.config import settings
            attempts = await cls._increment_and_check_otp_attempts(user.id, ChangeType.EMAIL.value)
            if attempts >= settings.MAX_OTP_ATTEMPTS:
                await AccountChangeRequestRepository.mark_completed(db, pending.id)
                raise CartifyException(
                    status_code=400,
                    detail="Maximum verification attempts exceeded. Verification code invalidated.",
                    code="MAX_ATTEMPTS_EXCEEDED",
                )
            remaining = settings.MAX_OTP_ATTEMPTS - attempts
            raise CartifyException(
                status_code=400,
                detail=f"Invalid verification code. {remaining} attempt(s) remaining.",
                code="INVALID_VERIFICATION_CODE",
            )

        # Clear failed attempts on success
        await cls._clear_otp_attempts(user.id, ChangeType.EMAIL.value)

        # Double check target email wasn't registered in the interim
        conflict = await UserRepository.get_by_email(db, pending.target_value)
        if conflict and conflict.id != user.id:
            raise CartifyException(
                status_code=409,
                detail="This email address is already in use by another account.",
                code="EMAIL_ALREADY_IN_USE",
            )

        # Apply change
        old_email = user.email
        user.email = pending.target_value
        await AccountChangeRequestRepository.mark_completed(db, pending.id)
        await db.commit()
        await db.refresh(user)

        # Revoke other active sessions for account security
        try:
            from app.repositories.user_session import UserSessionRepository
            await UserSessionRepository.revoke_all_for_user(db, user.id)
        except Exception:
            pass

        # Record security event
        await SecurityEventService.record_security_event(
            db=db,
            user_id=user.id,
            event_type="EMAIL_CHANGED",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"old_email": old_email, "new_email": user.email},
        )

        return True

    @classmethod
    async def initiate_phone_change(
        cls,
        db: AsyncSession,
        user: User,
        new_phone: str,
        current_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """
        Initiates staged phone number change after verifying current password.
        Returns the raw 6-digit OTP code for SMS dispatch.
        """
        # 1. Re-authenticate
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedError("Incorrect password. Identity verification required.")

        clean_phone = new_phone.strip()

        # 2. Check if identical to current phone
        if user.phone and clean_phone == user.phone:
            raise CartifyException(
                status_code=400,
                detail="New phone number cannot be the same as your current phone number.",
                code="PHONE_UNCHANGED",
            )

        # 3. Check if already taken
        existing = await UserRepository.get_by_phone(db, clean_phone)
        if existing:
            raise CartifyException(
                status_code=409,
                detail="This phone number is already registered to another account.",
                code="PHONE_ALREADY_IN_USE",
            )

        # 4. Generate verification code & hash
        raw_code = cls.generate_verification_code()
        token_hash = hash_token(raw_code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=CHANGE_TOKEN_EXPIRE_MINUTES)

        await AccountChangeRequestRepository.create(
            db=db,
            user_id=user.id,
            change_type=ChangeType.PHONE,
            target_value=clean_phone,
            verification_token_hash=token_hash,
            expires_at=expires_at,
        )

        # 5. Record security event
        await SecurityEventService.record_security_event(
            db=db,
            user_id=user.id,
            event_type="PHONE_CHANGE_REQUESTED",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"target_phone": clean_phone},
        )

        return raw_code

    @classmethod
    async def verify_phone_change(
        cls,
        db: AsyncSession,
        user: User,
        verification_code: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Verifies the staged phone change OTP, updates user.phone, and records audit event.
        Enforces maximum attempt bounds and revokes other sessions upon completion.
        """
        pending = await AccountChangeRequestRepository.get_active_by_user_and_type(
            db=db, user_id=user.id, change_type=ChangeType.PHONE
        )

        if not pending:
            raise CartifyException(
                status_code=400,
                detail="Invalid or expired verification code.",
                code="INVALID_VERIFICATION_CODE",
            )

        code_hash = hash_token(verification_code.strip())
        if pending.verification_token_hash != code_hash:
            from app.core.config import settings
            attempts = await cls._increment_and_check_otp_attempts(user.id, ChangeType.PHONE.value)
            if attempts >= settings.MAX_OTP_ATTEMPTS:
                await AccountChangeRequestRepository.mark_completed(db, pending.id)
                raise CartifyException(
                    status_code=400,
                    detail="Maximum verification attempts exceeded. Verification code invalidated.",
                    code="MAX_ATTEMPTS_EXCEEDED",
                )
            remaining = settings.MAX_OTP_ATTEMPTS - attempts
            raise CartifyException(
                status_code=400,
                detail=f"Invalid verification code. {remaining} attempt(s) remaining.",
                code="INVALID_VERIFICATION_CODE",
            )

        # Clear failed attempts on success
        await cls._clear_otp_attempts(user.id, ChangeType.PHONE.value)

        # Double check target phone wasn't registered in the interim
        conflict = await UserRepository.get_by_phone(db, pending.target_value)
        if conflict and conflict.id != user.id:
            raise CartifyException(
                status_code=409,
                detail="This phone number is already registered to another account.",
                code="PHONE_ALREADY_IN_USE",
            )

        # Apply change
        old_phone = user.phone
        user.phone = pending.target_value
        await AccountChangeRequestRepository.mark_completed(db, pending.id)
        await db.commit()
        await db.refresh(user)

        # Revoke other active sessions for account security
        try:
            from app.repositories.user_session import UserSessionRepository
            await UserSessionRepository.revoke_all_for_user(db, user.id)
        except Exception:
            pass

        # Record security event
        await SecurityEventService.record_security_event(
            db=db,
            user_id=user.id,
            event_type="PHONE_CHANGED",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"old_phone": old_phone, "new_phone": user.phone},
        )

        return True

    @classmethod
    async def change_password(
        cls,
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> bool:
        """
        Verifies current password, checks distinct new password, updates hash,
        revokes active refresh tokens and sessions, and records audit event.
        """
        # 1. Verify current password
        if not verify_password(current_password, user.password_hash):
            raise CartifyException(
                status_code=400,
                detail="Current password is incorrect.",
                code="CURRENT_PASSWORD_INVALID",
            )

        # 2. Reject same password
        if current_password == new_password:
            raise CartifyException(
                status_code=400,
                detail="New password cannot be identical to current password.",
                code="SAME_PASSWORD",
            )

        # 3. Update password hash
        from app.core.security import get_password_hash
        user.password_hash = get_password_hash(new_password)
        await db.commit()
        await db.refresh(user)

        # 4. Invalidate all active refresh tokens and sessions
        await UserRepository.revoke_all_user_tokens(db, user.id)
        from app.repositories.user_session import UserSessionRepository
        await UserSessionRepository.revoke_all_for_user(db, user.id)

        # 5. Record security event
        await SecurityEventService.record_security_event(
            db=db,
            user_id=user.id,
            event_type="PASSWORD_CHANGED",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata={"activity": "password_changed_successfully"},
        )

        # 6. Emit security notification
        try:
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
                    "activity_description": "Your Cartify account password was changed successfully.",
                },
            )
        except Exception as ex:
            logger.warning(f"Failed to dispatch password changed outbox notification: {ex}")

        return True

    @classmethod
    async def get_security_summary(
        cls, db: AsyncSession, user: User
    ) -> "AccountSecuritySummaryResponse":
        """
        Compiles high-level security overview without leaking raw audit logs or secrets.
        """
        from app.repositories.user_session import UserSessionRepository
        from app.repositories.account_deletion import AccountDeletionRepository
        from app.repositories.account_security_event import AccountSecurityEventRepository
        from app.schemas.account import AccountSecuritySummaryResponse

        active_sessions = await UserSessionRepository.get_active_by_user_id(db, user.id)
        pending_deletion = await AccountDeletionRepository.get_pending_by_user_id(db, user.id)
        recent_events = await AccountSecurityEventRepository.list_by_user_id(db, user.id, limit=20)

        last_security_event_at = recent_events[0].created_at if recent_events else None
        pw_events = [e for e in recent_events if e.event_type == "PASSWORD_CHANGED"]
        password_last_changed_at = pw_events[0].created_at if pw_events else None

        return AccountSecuritySummaryResponse(
            email_verified=user.is_verified,
            phone_verified=user.phone is not None,
            active_sessions=len(active_sessions),
            has_pending_deletion=pending_deletion is not None,
            last_security_event_at=last_security_event_at,
            password_last_changed_at=password_last_changed_at,
        )
