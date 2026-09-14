"""
Cartify Notification Delivery Webhook Endpoints (Module 13)

Receives delivery receipts and status updates from third-party notification gateways:
- Constant-time HMAC signature verification
- Deduplication against replay attacks
- Delivery record state updates (SENT -> DELIVERED / FAILED / BOUNCED)
"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_writer
from app.schemas.common import ApiResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notification-webhooks", tags=["Notification Webhooks"])


@router.post(
    "/{provider}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Receive provider delivery status receipt",
)
async def receive_delivery_webhook(
    request: Request,
    provider: str = Path(..., description="Provider name, e.g. mock_email, sendgrid, twilio"),
    x_notification_signature: Optional[str] = Header(None, alias="X-Notification-Signature"),
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[dict]:
    """
    Webhook endpoint for asynchronous delivery receipts.
    Guarantees constant-time cryptographic verification and idempotent event ingestion.
    """
    raw_bytes = await request.body()
    signature = x_notification_signature or x_webhook_signature or ""

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required webhook signature header.",
        )

    try:
        parsed_json = json.loads(raw_bytes.decode("utf-8")) if raw_bytes else {}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON in webhook request body.",
        )

    result = await NotificationService.process_delivery_webhook(
        db=db,
        provider=provider,
        payload_bytes=raw_bytes,
        signature_header=signature,
        payload_json=parsed_json,
    )

    return ApiResponse(
        success=True,
        data=result,
        message="Delivery receipt processed successfully",
    )
