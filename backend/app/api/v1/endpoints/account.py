"""
Cartify Account & Security Endpoints (Module 15.2)

High-security REST APIs for customer profile management, credential updates,
staged email/phone verification, multi-device sessions, and safe account deletion.

All operations strictly bind to server-authoritative authenticated user identity.
Client-provided user_id is never accepted.
"""

from typing import List, Optional
from fastapi import APIRouter, Cookie, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, rate_limit
from app.core.database import get_db_reader, get_db_writer
from app.models.user import User
from app.repositories.account_security_event import AccountSecurityEventRepository
from app.schemas.account import (
    AccountChangePasswordRequest,
    AccountDeletionCancelResponse,
    AccountDeletionRequestSchema,
    AccountDeletionResponse,
    AccountProfileResponse,
    AccountSecuritySummaryResponse,
    InitiateEmailChangeRequest,
    InitiatePhoneChangeRequest,
    ProfileUpdateRequest,
    SecurityEventSummaryResponse,
    SessionRevokeResponse,
    UserSessionResponse,
    VerifyEmailChangeRequest,
    VerifyPhoneChangeRequest,
)
from app.schemas.auth import MessageResponse
from app.schemas.common import ApiResponse
from app.services.account_deletion_service import AccountDeletionService
from app.services.account_service import AccountService
from app.services.profile_service import ProfileService
from app.services.security_event_service import SecurityEventService
from app.services.session_service import SessionService

router = APIRouter(prefix="/account", tags=["Account"])


def get_request_context(request: Request):
    """Extracts client IP, User-Agent, and Request-ID safely."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = None

    user_agent = request.headers.get("User-Agent")
    request_id = request.headers.get("X-Request-ID")
    return client_ip, user_agent, request_id


# -----------------------------------------------------------------------------
# 1. Account Overview & Profile
# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=ApiResponse[AccountProfileResponse],
    summary="Retrieve safe account overview",
)
async def get_account_overview(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[AccountProfileResponse]:
    """
    Returns sanitized account overview for current authenticated user.
    Never exposes passwords, tokens, hashes, or private audit internals.
    """
    profile = await ProfileService.get_profile(db=db, user_id=current_user.id)
    return ApiResponse(
        success=True,
        message="Account overview retrieved successfully.",
        data=profile,
    )


@router.patch(
    "/profile",
    response_model=ApiResponse[AccountProfileResponse],
    summary="Update customer profile",
    dependencies=[Depends(rate_limit(limit=30, window_seconds=60))],
)
async def update_account_profile(
    payload: ProfileUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AccountProfileResponse]:
    """
    Updates allowed profile attributes (name, phone, avatar_url, date_of_birth, bio).
    Direct email modifications are forbidden and must use the verified email-change endpoint.
    Protected against mass assignment: role, id, is_active, is_verified are strictly ignored.
    """
    client_ip, user_agent, request_id = get_request_context(request)
    updated = await ProfileService.update_profile(
        db=db,
        user=current_user,
        data=payload,
        ip_address=client_ip,
        user_agent=user_agent,
        request_id=request_id,
    )
    return ApiResponse(
        success=True,
        message="Profile updated successfully.",
        data=updated,
    )


# -----------------------------------------------------------------------------
# 2. Email Change Workflow (Staged Verification)
# -----------------------------------------------------------------------------

@router.post(
    "/email-change",
    response_model=ApiResponse[MessageResponse],
    summary="Initiate staged email change",
    dependencies=[Depends(rate_limit(limit=5, window_seconds=60))],
)
async def initiate_email_change(
    payload: InitiateEmailChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[MessageResponse]:
    """
    Initiates staged email change after verifying current password.
    Generates a secure verification code and records security audit event.
    """
    client_ip, user_agent, _ = get_request_context(request)
    await AccountService.initiate_email_change(
        db=db,
        user=current_user,
        new_email=payload.new_email,
        current_password=payload.current_password,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return ApiResponse(
        success=True,
        message="Verification code has been sent to your new email address.",
        data=MessageResponse(message="Verification code dispatched."),
    )


@router.post(
    "/email-change/verify",
    response_model=ApiResponse[MessageResponse],
    summary="Verify and complete email change",
    dependencies=[Depends(rate_limit(limit=10, window_seconds=60))],
)
async def verify_email_change(
    payload: VerifyEmailChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[MessageResponse]:
    """
    Verifies staged email change token/code and updates account email address transactionally.
    """
    client_ip, user_agent, _ = get_request_context(request)
    await AccountService.verify_email_change(
        db=db,
        user=current_user,
        verification_code=payload.code,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return ApiResponse(
        success=True,
        message="Email address has been verified and updated successfully.",
        data=MessageResponse(message="Email updated successfully."),
    )


# -----------------------------------------------------------------------------
# 3. Phone Change Workflow (Staged Verification)
# -----------------------------------------------------------------------------

@router.post(
    "/phone-change",
    response_model=ApiResponse[MessageResponse],
    summary="Initiate staged phone number update",
    dependencies=[Depends(rate_limit(limit=5, window_seconds=60))],
)
async def initiate_phone_change(
    payload: InitiatePhoneChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[MessageResponse]:
    """
    Initiates staged phone number change after verifying current password.
    Generates a secure 6-digit OTP and records security audit event.
    """
    client_ip, user_agent, _ = get_request_context(request)
    await AccountService.initiate_phone_change(
        db=db,
        user=current_user,
        new_phone=payload.new_phone,
        current_password=payload.current_password,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return ApiResponse(
        success=True,
        message="Verification OTP has been sent to your new phone number.",
        data=MessageResponse(message="OTP dispatched."),
    )


@router.post(
    "/phone-change/verify",
    response_model=ApiResponse[MessageResponse],
    summary="Verify and complete phone number update",
    dependencies=[Depends(rate_limit(limit=10, window_seconds=60))],
)
async def verify_phone_change(
    payload: VerifyPhoneChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[MessageResponse]:
    """
    Verifies staged phone change OTP and updates account phone number transactionally.
    """
    client_ip, user_agent, _ = get_request_context(request)
    await AccountService.verify_phone_change(
        db=db,
        user=current_user,
        verification_code=payload.code,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return ApiResponse(
        success=True,
        message="Phone number has been verified and updated successfully.",
        data=MessageResponse(message="Phone number updated successfully."),
    )


# -----------------------------------------------------------------------------
# 4. Password Change
# -----------------------------------------------------------------------------

@router.post(
    "/change-password",
    response_model=ApiResponse[MessageResponse],
    summary="Change account password",
    dependencies=[Depends(rate_limit(limit=5, window_seconds=60))],
)
async def change_password(
    payload: AccountChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[MessageResponse]:
    """
    Changes account password with current password verification.
    Revokes all active refresh tokens and user sessions, and sends a security alert.
    """
    client_ip, user_agent, request_id = get_request_context(request)
    await AccountService.change_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        ip_address=client_ip,
        user_agent=user_agent,
        request_id=request_id,
    )
    return ApiResponse(
        success=True,
        message="Password changed successfully. All active sessions have been terminated for security.",
        data=MessageResponse(message="Password changed successfully."),
    )


# -----------------------------------------------------------------------------
# 5. Multi-Device Sessions
# -----------------------------------------------------------------------------

@router.get(
    "/sessions",
    response_model=ApiResponse[List[UserSessionResponse]],
    summary="List active device sessions",
)
async def get_active_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_cookie: Optional[str] = Cookie(None, alias="session_token"),
) -> ApiResponse[List[UserSessionResponse]]:
    """
    Lists active device sessions for the authenticated customer.
    Masks IP addresses for privacy and identifies the current session.
    Never exposes raw tokens, hashes, or session secrets.
    """
    current_token = x_session_id or session_cookie
    sessions = await SessionService.get_active_sessions(
        db=db,
        user_id=current_user.id,
        current_token=current_token,
    )
    return ApiResponse(
        success=True,
        message="Active sessions retrieved successfully.",
        data=sessions,
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Revoke a specific device session",
    dependencies=[Depends(rate_limit(limit=30, window_seconds=60))],
)
async def revoke_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[MessageResponse]:
    """
    Revokes an active session. Strictly enforces user ownership to prevent IDOR attacks.
    """
    client_ip, user_agent, _ = get_request_context(request)
    await SessionService.revoke_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return ApiResponse(
        success=True,
        message="Session revoked successfully.",
        data=MessageResponse(message="Session revoked."),
    )


@router.post(
    "/sessions/revoke-others",
    response_model=ApiResponse[SessionRevokeResponse],
    summary="Revoke all other device sessions",
    dependencies=[Depends(rate_limit(limit=10, window_seconds=60))],
)
async def revoke_other_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_cookie: Optional[str] = Cookie(None, alias="session_token"),
) -> ApiResponse[SessionRevokeResponse]:
    """
    Revokes all active sessions belonging to current user except the current session.
    """
    client_ip, user_agent, _ = get_request_context(request)
    current_token = x_session_id or session_cookie
    count = await SessionService.revoke_all_sessions(
        db=db,
        user_id=current_user.id,
        current_token=current_token,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return ApiResponse(
        success=True,
        message=f"{count} other session(s) revoked successfully.",
        data=SessionRevokeResponse(
            revoked_count=count,
            message=f"{count} other session(s) revoked successfully.",
        ),
    )


@router.post(
    "/sessions/revoke-all",
    response_model=ApiResponse[SessionRevokeResponse],
    summary="Revoke all active device sessions",
    dependencies=[Depends(rate_limit(limit=10, window_seconds=60))],
)
async def revoke_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[SessionRevokeResponse]:
    """
    Revokes all active sessions belonging to the authenticated user.
    """
    client_ip, user_agent, _ = get_request_context(request)
    count = await SessionService.revoke_all_sessions(
        db=db,
        user_id=current_user.id,
        current_token=None,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return ApiResponse(
        success=True,
        message=f"{count} session(s) revoked successfully.",
        data=SessionRevokeResponse(
            revoked_count=count,
            message=f"{count} session(s) revoked successfully.",
        ),
    )


# -----------------------------------------------------------------------------
# 6. Security Posture & Auditing
# -----------------------------------------------------------------------------

@router.get(
    "/security",
    response_model=ApiResponse[AccountSecuritySummaryResponse],
    summary="Retrieve account security summary",
)
async def get_account_security_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[AccountSecuritySummaryResponse]:
    """
    Returns safe high-level security summary.
    Does not expose sensitive audit internals, provider tokens, or IP logs.
    """
    summary = await AccountService.get_security_summary(db=db, user=current_user)
    return ApiResponse(
        success=True,
        message="Account security summary retrieved successfully.",
        data=summary,
    )


@router.get(
    "/security/events",
    response_model=ApiResponse[List[SecurityEventSummaryResponse]],
    summary="List recent security audit events",
)
async def list_security_events(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[List[SecurityEventSummaryResponse]]:
    """
    Returns paginated list of recent security audit events for current user.
    IP addresses are masked for privacy, and all credentials/metadata are redacted.
    """
    events = await AccountSecurityEventRepository.list_by_user_id(
        db=db, user_id=current_user.id, limit=limit, offset=offset
    )
    summaries = [
        SecurityEventSummaryResponse(
            id=e.id,
            event_type=e.event_type,
            created_at=e.created_at,
            ip_address=SecurityEventService.mask_ip_for_display(e.ip_address),
            user_agent_summary=e.user_agent[:100] if e.user_agent else None,
        )
        for e in events
    ]
    return ApiResponse(
        success=True,
        message="Security events retrieved successfully.",
        data=summaries,
    )


# -----------------------------------------------------------------------------
# 7. Non-Destructive Account Deletion Lifecycle
# -----------------------------------------------------------------------------

@router.post(
    "/deletion-request",
    response_model=ApiResponse[AccountDeletionResponse],
    summary="Schedule non-destructive account deletion",
    dependencies=[Depends(rate_limit(limit=5, window_seconds=60))],
)
async def request_account_deletion(
    payload: AccountDeletionRequestSchema,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AccountDeletionResponse]:
    """
    Schedules account deletion with a 30-day grace period.
    Verifies password and ensures there are no active in-flight orders.
    Does NOT destroy data immediately, safeguarding historical order/payment records.
    """
    client_ip, user_agent, _ = get_request_context(request)
    scheduled = await AccountDeletionService.request_deletion(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        reason=payload.reason,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return ApiResponse(
        success=True,
        message="Account deletion scheduled with 30-day grace period. You can cancel before completion.",
        data=scheduled,
    )


@router.post(
    "/deletion-request/cancel",
    response_model=ApiResponse[AccountDeletionCancelResponse],
    summary="Cancel pending account deletion",
    dependencies=[Depends(rate_limit(limit=5, window_seconds=60))],
)
async def cancel_account_deletion(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AccountDeletionCancelResponse]:
    """
    Cancels an active pending account deletion request for the current user.
    """
    client_ip, user_agent, _ = get_request_context(request)
    await AccountDeletionService.cancel_deletion(
        db=db,
        user=current_user,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return ApiResponse(
        success=True,
        message="Account deletion request cancelled successfully.",
        data=AccountDeletionCancelResponse(
            message="Account deletion request cancelled successfully."
        ),
    )
