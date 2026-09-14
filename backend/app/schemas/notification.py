"""
Notification Pydantic Schemas (Module 13)

Schemas for Customer in-app notifications, delivery logs, templates, and admin queries.
Supports both camelCase and snake_case aliases for web, iOS, and Android clients.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    user_id: str = Field(..., alias="userId")
    type: str
    title: str
    body: str
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    priority: str
    status: str
    reference_key: Optional[str] = Field(None, alias="referenceKey")
    created_at: datetime = Field(..., alias="createdAt")
    read_at: Optional[datetime] = Field(None, alias="readAt")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")


class NotificationListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[NotificationResponse]
    total: int
    unread_count: int = Field(..., alias="unreadCount")
    next_cursor: Optional[str] = Field(None, alias="nextCursor")


class UnreadCountResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    unread_count: int = Field(..., alias="unreadCount")


class NotificationDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    notification_id: str = Field(..., alias="notificationId")
    user_id: str = Field(..., alias="userId")
    channel: str
    provider: str
    provider_message_id: Optional[str] = Field(None, alias="providerMessageId")
    status: str
    attempt_count: int = Field(..., alias="attemptCount")
    last_attempt_at: Optional[datetime] = Field(None, alias="lastAttemptAt")
    delivered_at: Optional[datetime] = Field(None, alias="deliveredAt")
    failed_at: Optional[datetime] = Field(None, alias="failedAt")
    failure_code: Optional[str] = Field(None, alias="failureCode")
    failure_message: Optional[str] = Field(None, alias="failureMessage")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class NotificationTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    key: str
    channel: str
    subject: Optional[str] = None
    title_template: str = Field(..., alias="titleTemplate")
    body_template: str = Field(..., alias="bodyTemplate")
    locale: str
    version: int
    is_active: bool = Field(..., alias="isActive")
    allowed_variables: List[str] = Field(default_factory=list, alias="allowedVariables")
