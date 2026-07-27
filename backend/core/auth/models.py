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
