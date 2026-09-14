"""
Device Registration Schemas (Module 13)

Schemas for push notification device token registration and management.
Device tokens are never returned raw to prevent token exposure.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RegisterDeviceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    platform: str
    device_token: str = Field(..., alias="deviceToken", min_length=10, max_length=255)
    app_version: Optional[str] = Field(None, alias="appVersion")


class DeviceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    platform: str
    masked_token: str = Field(..., alias="maskedToken")
    app_version: Optional[str] = Field(None, alias="appVersion")
    is_active: bool = Field(..., alias="isActive")
    last_seen_at: datetime = Field(..., alias="lastSeenAt")
    created_at: datetime = Field(..., alias="createdAt")


class DeviceListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[DeviceResponse]
