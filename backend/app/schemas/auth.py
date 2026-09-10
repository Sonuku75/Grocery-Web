from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class LoginPayload(BaseModel):
    identifier: str = Field(..., description="Email or mobile number")
    password: str = Field(..., min_length=6)

class RegisterPayload(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    mobile: str = Field(..., min_length=8, max_length=32)
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    mobile: str
    full_name: str
    avatar_url: Optional[str] = None
    role: str
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
