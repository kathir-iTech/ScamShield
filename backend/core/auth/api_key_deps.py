from __future__ import annotations

import time
from typing import Iterable, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from core.api_keys import APIKey, get_api_key_manager
from core.context import set_user_id

_UNAUTHENTICATED = {
    "WWW-Authenticate": 'ApiKey realm="scamshield", Bearer realm="scamshield"'
}


def scope_in_scopes(required: str, granted: Iterable[str]) -> bool:
    granted_set = set(granted or ())
    if "admin:all" in granted_set:
        return True
    if not granted_set:
        return False
    return required in granted_set


async def require_api_key(
    request: Request,
    x_api_key: str = Header(default=""),
) -> APIKey:
    raw_key = (x_api_key or "").strip()
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers=_UNAUTHENTICATED,
        )

    manager = get_api_key_manager()
    prefix = raw_key[:8]
    candidate: Optional[APIKey] = manager.find_by_prefix(prefix)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers=_UNAUTHENTICATED,
        )
    if candidate.revoked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key has been revoked",
        )
    if candidate.expires_at > 0 and candidate.expires_at < __import__("time").time():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key has expired",
        )

    api_key = manager.validate_key_by_prefix(prefix, raw_key)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers=_UNAUTHENTICATED,
        )

    user_id = api_key.owner_id or api_key.key_id
    request.state.user_id = user_id
    request.state.role = api_key.role
    request.state.api_key_prefix = prefix
    request.state.scopes = sorted(api_key.scopes)
    set_user_id(user_id)
    return api_key


def require_scope(scope: str):
    async def _scope_checker(
        request: Request,
        api_key: APIKey = Depends(require_api_key),
    ) -> APIKey:
        if not scope_in_scopes(scope, api_key.scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{scope}' is required for this operation",
            )
        return api_key

    return _scope_checker


__all__ = [
    "require_api_key",
    "require_scope",
    "scope_in_scopes",
]
