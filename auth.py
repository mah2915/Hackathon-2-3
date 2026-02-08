"""
Authentication request/response schemas for the Todo Web App
"""

from pydantic import BaseModel, EmailStr
from pydantic.functional_validators import field_validator
from typing import Optional
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user creation requests."""
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """Schema for user login requests."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response data."""
    id: UUID
    email: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for JWT token data."""
    user_id: Optional[str] = None
    email: Optional[str] = None


class AuthResponse(BaseModel):
    """Schema for authentication responses."""
    success: bool
    data: Optional[dict] = None
    message: str


class AuthErrorResponse(BaseModel):
    """Schema for authentication error responses."""
    success: bool = False
    error: dict


class SignUpRequest(UserCreate):
    """Schema for signup request - extends UserCreate."""
    pass


class SignUpResponse(BaseModel):
    """Schema for signup response."""
    success: bool
    data: Optional[dict] = None
    message: str


class SignInRequest(UserLogin):
    """Schema for signin request - extends UserLogin."""
    pass


class SignInResponse(BaseModel):
    """Schema for signin response."""
    success: bool
    data: Optional[dict] = None
    message: str