"""
Notification Preference Schemas (Module 13)

Schemas for managing multi-channel preferences per notification category.
"""

from typing import List
from pydantic import BaseModel, ConfigDict, Field


class NotificationPreferenceItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    category: str
    channel: str
    is_enabled: bool = Field(..., alias="isEnabled")
    is_mandatory: bool = Field(False, alias="isMandatory")


class NotificationPreferencesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    preferences: List[NotificationPreferenceItem]


class UpdateNotificationPreferenceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    category: str
    channel: str
    is_enabled: bool = Field(..., alias="isEnabled")
