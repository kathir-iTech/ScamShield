from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings
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


def _attach(request: Optional[Request], user: AuthenticatedUser) -> AuthenticatedUser:
    if request is not None:
        request.state.user_id = user.id
        request.state.role = user.role.value
        request.state.token_id = user.token_id
    return user


async def get_current_user(
    request: Request,
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
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _attach(request, _build_user(payload))


async def optional_auth(
    request: Request,
) -> AuthenticatedUser:
    token_str = get_token_from_header(request)
    if token_str is None or not settings.AUTH_ENABLED:
        return _attach(request, AuthenticatedUser(id="anonymous", role=UserRole.GUEST, token_id=""))
    try:
        payload = decode_token(token_str)
    except ValueError:
        return _attach(request, AuthenticatedUser(id="anonymous", role=UserRole.GUEST, token_id=""))
    return _attach(request, _build_user(payload))


async def require_auth(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if not user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user


async def require_auth_if_enabled(
    user: AuthenticatedUser = Depends(optional_auth),
) -> AuthenticatedUser:
    """Require a valid bearer token, but only while auth is switched on."""
    if not settings.AUTH_ENABLED:
        return user
    if not user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
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
