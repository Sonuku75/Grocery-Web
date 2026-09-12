"""
Cartify Authentication Pydantic Schemas (Module 1)
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator
from app.schemas.user import UserResponse

class RegisterRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, min_length=8, max_length=20)
    mobile: Optional[str] = Field(None, min_length=8, max_length=32)
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")

    @model_validator(mode="after")
    def populate_aliases(self) -> "RegisterRequest":
        if not self.name and self.full_name:
            self.name = self.full_name
        elif not self.name:
            raise ValueError("name is required")
        if not self.phone and self.mobile:
            self.phone = self.mobile
        return self

class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    identifier: Optional[str] = None
    password: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def check_identifier(self) -> "LoginRequest":
        if not self.email and self.identifier:
            self.email = self.identifier
        if not self.email:
            raise ValueError("email is required")
        return self

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Raw refresh token if not using HttpOnly cookies")

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1, description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password must be at least 8 characters")

class MessageResponse(BaseModel):
    message: str

# Backward compatibility aliases
RegisterPayload = RegisterRequest
LoginPayload = LoginRequest
