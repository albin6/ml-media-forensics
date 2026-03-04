from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator
import re


class RegisterRequest(BaseModel):
    email:     EmailStr
    password:  str
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain a digit")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password must contain a special character")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class UserResponse(BaseModel):
    id:         UUID
    email:      str
    full_name:  Optional[str]
    role:       str
    created_at: datetime

    class Config:
        from_attributes = True
