from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.auth.jwt import decode_token, get_token_from_header
from core.auth.models import AuthenticatedUser, TokenPayload, UserRole

_security_scheme = HTTPBearer(auto_error=False)

_ROLE_RANK = {UserRole.GUEST: 0, UserRole.AUTHENTICATED: 1, UserRole.ADMIN: 2}


def _build_user(payload: TokenPayload) -> AuthenticatedUser:
    role_rank = {r.value: r for r in UserRole}
    role = role_rank.get(payload.role, UserRole.AUTHENTICATED)
    return AuthenticatedUser(
        id=payload.sub,
        role=role,
        token_id=payload.jti,
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security_scheme),
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials)
        return _build_user(payload)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def optional_auth(
    request: Request,
) -> AuthenticatedUser:
    token_str = get_token_from_header(request)
    if token_str is None:
        return AuthenticatedUser(id="anonymous", role=UserRole.GUEST, token_id="")
    try:
        payload = decode_token(token_str)
        return _build_user(payload)
    except ValueError:
        return AuthenticatedUser(id="anonymous", role=UserRole.GUEST, token_id="")


async def require_auth(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if not user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user


async def require_role(required_role: UserRole):
    async def _role_checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if user.role not in _ROLE_RANK:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid role",
            )
        if _ROLE_RANK[user.role] < _ROLE_RANK[required_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' required",
            )
        return user
    return _role_checker


async def require_admin(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
