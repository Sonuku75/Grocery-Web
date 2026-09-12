"""
Cartify Address Schemas (Module 2)

Pydantic schemas for address creation, update, serialization, and validation.
Supports Indian PIN codes (6 digits) and phone numbers with international adaptability.
"""

from datetime import datetime
import re
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Regex patterns
INDIAN_PINCODE_PATTERN = re.compile(r"^[1-9][0-9]{5}$")
PHONE_PATTERN = re.compile(r"^(?:\+91|91|0)?[6-9]\d{9}$|^\+?[1-9]\d{7,14}$")

class AddressCreateRequest(BaseModel):
    label: str = Field("Home", description="Address label (e.g. Home, Work, Other)")
    recipient_name: Optional[str] = Field(None, min_length=2, max_length=100)
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=8, max_length=20)
    mobile: Optional[str] = Field(None, min_length=8, max_length=20)
    address_line_1: Optional[str] = Field(None, min_length=3, max_length=255)
    house_flat: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    street: Optional[str] = Field(None, max_length=255)
    area: Optional[str] = Field(None, max_length=255)
    landmark: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    country: str = Field("India", max_length=100)
    postal_code: Optional[str] = None
    pincode: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_default: bool = False

    @model_validator(mode="after")
    def reconcile_and_validate(self) -> "AddressCreateRequest":
        # 1. Reconcile recipient name
        if not self.recipient_name and self.full_name:
            self.recipient_name = self.full_name.strip()
        elif self.recipient_name:
            self.recipient_name = self.recipient_name.strip()
        else:
            raise ValueError("recipient_name is required")

        # 2. Reconcile phone / mobile
        raw_phone = self.phone or self.mobile
        if not raw_phone:
            raise ValueError("phone is required")
        cleaned_phone = re.sub(r"[\s\-\(\)]", "", raw_phone)
        if not PHONE_PATTERN.match(cleaned_phone):
            raise ValueError("Invalid phone number format")
        self.phone = cleaned_phone

        # 3. Reconcile address lines
        if not self.address_line_1 and self.house_flat:
            parts = [self.house_flat.strip()]
            if self.street:
                parts.append(self.street.strip())
            self.address_line_1 = ", ".join(parts)
        elif self.address_line_1:
            self.address_line_1 = self.address_line_1.strip()
        else:
            raise ValueError("address_line_1 is required")

        if not self.address_line_2 and self.area:
            self.address_line_2 = self.area.strip()

        # 4. Reconcile postal_code / pincode
        code = (self.postal_code or self.pincode or "").strip()
        if not code:
            raise ValueError("postal_code is required")
        if self.country.lower() == "india":
            if not INDIAN_PINCODE_PATTERN.match(code):
                raise ValueError("Invalid Indian PIN code: must be 6 digits and cannot start with 0")
        elif not re.match(r"^[A-Za-z0-9\s\-]{3,10}$", code):
            raise ValueError("Invalid postal code format")
        self.postal_code = code

        return self

class AddressUpdateRequest(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=50)
    recipient_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=8, max_length=20)
    address_line_1: Optional[str] = Field(None, min_length=3, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    landmark: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_default: Optional[bool] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = re.sub(r"[\s\-\(\)]", "", v)
            if not PHONE_PATTERN.match(cleaned):
                raise ValueError("Invalid phone number format")
            return cleaned
        return v

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not INDIAN_PINCODE_PATTERN.match(cleaned) and not re.match(r"^[A-Za-z0-9\s\-]{3,10}$", cleaned):
                raise ValueError("Invalid postal code format")
            return cleaned
        return v

class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    label: str
    recipient_name: str
    phone: str
    address_line_1: str
    address_line_2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    country: str
    postal_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    # Aliases for frontend parity
    @property
    def full_name(self) -> str:
        return self.recipient_name

    @property
    def mobile(self) -> str:
        return self.phone

    @property
    def house_flat(self) -> str:
        return self.address_line_1

    @property
    def street(self) -> Optional[str]:
        return self.address_line_2

    @property
    def area(self) -> Optional[str]:
        return self.address_line_2

    @property
    def pincode(self) -> str:
        return self.postal_code

    @property
    def address_type(self) -> str:
        return self.label

class AddressListResponse(BaseModel):
    items: List[AddressResponse]
    total: int
