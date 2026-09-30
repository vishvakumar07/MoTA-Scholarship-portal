"""Pydantic v2 schemas for authentication endpoints."""

from __future__ import annotations

import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


#  -  - - Register  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200, examples=["Arjun Kumar"])
    email: EmailStr = Field(..., examples=["arjun.kumar@example.com"])
    phone_number: str | None = Field(None, examples=["+919876543210"])
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Accept +91XXXXXXXXXX or 10-digit
        clean = re.sub(r"\s+", "", v)
        if not re.match(r"^(\+91)?[6-9]\d{9}$", clean):
            raise ValueError("Invalid Indian phone number format. Use +91XXXXXXXXXX or 10 digits.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z\s'.,-]+$", v):
            raise ValueError("Full name may only contain letters, spaces, and common punctuation.")
        return v.strip()


class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    message: str = "Registration successful."


#  -  - - Login  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserInfo"


#  -  - - Refresh  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


#  -  - - Logout  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class LogoutResponse(BaseModel):
    message: str = "Logged out successfully."


#  -  - - User info (embedded in responses)  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    is_email_verified: bool
    roles: list[str] = []
