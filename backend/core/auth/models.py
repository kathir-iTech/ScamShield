from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, enum.Enum):
    GUEST = "guest"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int
    iat: int
    jti: str
    token_type: str = "access"
    original_role: str = ""
    iss: str = ""
    aud: str = ""


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, description="Email address of the new account")
    password: str = Field(..., min_length=1, description="Initial password")
    display_name: str = Field(default="", max_length=120, description="Optional display name")


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, description="Email address")
    password: str = Field(..., min_length=1, description="Account password")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=1, description="Replacement password")


class UserResponse(BaseModel):
    id: str
    email: str
    role: str = UserRole.AUTHENTICATED.value
    display_name: str = ""
    created_at: float = 0.0
    last_login_at: Optional[float] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminAuthRequest(BaseModel):
    admin_key: str = Field(..., min_length=1, description="Server-controlled admin API key")


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="Refresh token to revoke")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="Refresh token to exchange")


class AuthConfig:
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 86400 * 30
    ISSUER: str = "scamshield"


@dataclass
class AuthenticatedUser:
    id: str
    role: UserRole
    token_id: str
    permissions: set[str] = field(default_factory=set)

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_authenticated(self) -> bool:
        return self.role != UserRole.GUEST
