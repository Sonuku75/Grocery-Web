"""
Cartify Session Service (Module 15.1)

Provides multi-device session management and granular session revocation.
Never persists raw session tokens — stores only SHA-256 hashes.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CartifyException, NotFoundError
from app.core.security import generate_secure_token, hash_token
from app.models.user_session import UserSession
from app.repositories.user_session import UserSessionRepository
from app.schemas.account import UserSessionResponse
from app.services.security_event_service import SecurityEventService

logger = logging.getLogger("cartify.session")


class SessionService:
    @classmethod
    async def create_session(
        cls,
        db: AsyncSession,
        user_id: str,
        device_name: Optional[str] = None,
        platform: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        ttl_days: int = 30,
    ) -> Tuple[UserSession, str]:
        """
        Creates a new user session with a cryptographically secure token.
        Persists the SHA-256 hash and returns (session_record, raw_token).
        """
        raw_token = generate_secure_token(32)
        session_identifier = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=ttl_days)

        session = await UserSessionRepository.create(
            db=db,
            user_id=user_id,
            session_identifier=session_identifier,
            expires_at=expires_at,
            device_name=device_name,
            platform=platform,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return session, raw_token

    @classmethod
    async def get_active_sessions(
        cls,
        db: AsyncSession,
        user_id: str,
        current_token: Optional[str] = None,
    ) -> List[UserSessionResponse]:
        """
        Returns all active sessions for a user with masked IP addresses and
        indicates which session corresponds to current_token if provided.
        """
        sessions = await UserSessionRepository.get_active_by_user_id(db, user_id)
        current_hash = hash_token(current_token) if current_token else None

        responses = []
        for s in sessions:
            masked_ip = SecurityEventService.mask_ip_for_display(s.ip_address)
            is_current = (current_hash is not None and s.session_identifier == current_hash)
            responses.append(
                UserSessionResponse(
                    id=s.id,
                    device_name=s.device_name,
                    platform=s.platform,
                    ip_address=masked_ip,
                    last_seen_at=s.last_seen_at,
                    created_at=s.created_at,
                    expires_at=s.expires_at,
                    is_current=is_current,
                )
            )
        return responses

    @classmethod
    async def revoke_session(
        cls,
        db: AsyncSession,
        session_id: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Revokes a specific session belonging to user_id.
        """
        session = await UserSessionRepository.get_by_id(db, session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError("Session not found or already revoked.")

        revoked = await UserSessionRepository.revoke(db, session_id, user_id)
        if revoked:
            await SecurityEventService.record_security_event(
                db=db,
                user_id=user_id,
                event_type="SESSION_REVOKED",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"session_id": session_id, "device_name": session.device_name},
            )
        return revoked

    @classmethod
    async def revoke_all_sessions(
        cls,
        db: AsyncSession,
        user_id: str,
        current_token: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """
        Revokes all active sessions for user_id, optionally preserving current_token.
        """
        except_identifier = hash_token(current_token) if current_token else None
        count = await UserSessionRepository.revoke_all_for_user(
            db, user_id, except_identifier=except_identifier
        )

        await SecurityEventService.record_security_event(
            db=db,
            user_id=user_id,
            event_type="ALL_SESSIONS_REVOKED",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"revoked_count": count, "kept_current": current_token is not None},
        )
        return count
