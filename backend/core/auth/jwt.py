from __future__ import annotations

import time
import uuid
from typing import Optional

import jwt as pyjwt
from fastapi import Request

from core.auth.models import TokenPayload, UserRole
from core.auth.token_store import TokenStore, get_token_store, set_token_store, create_token_store

_ACCESS_TTL = 3600
_REFRESH_TTL = 86400 * 30
_SECRET: str = ""
_ALGORITHM = "HS256"
_CLOCK_SKEW: int = 30


def configure(
    secret_key: str,
    access_ttl: int = 3600,
    refresh_ttl: int = 86400 * 30,
    clock_skew: int = 30,
    blacklist_capacity: int = 100000,
    redis_url: Optional[str] = None,
) -> None:
    global _SECRET, _ACCESS_TTL, _REFRESH_TTL, _CLOCK_SKEW
    _SECRET = secret_key
    _ACCESS_TTL = access_ttl
    _REFRESH_TTL = refresh_ttl
    _CLOCK_SKEW = clock_skew
    store = create_token_store(redis_url=redis_url, max_entries=blacklist_capacity)
    set_token_store(store)


def _store() -> TokenStore:
    return get_token_store()


def blacklist_token(jti: str) -> None:
    _store().blacklist(jti, ttl=_REFRESH_TTL)


def is_token_blacklisted(jti: str) -> bool:
    return _store().is_blacklisted(jti)


def mark_refresh_used(jti: str) -> bool:
    return _store().mark_refresh_used(jti)


def is_refresh_reused(jti: str) -> bool:
    return _store().is_refresh_reused(jti)


def reset_blacklist() -> None:
    _store().reset()


def revoke_all_for_user(user_id: str) -> None:
    pass


def get_blacklist_size() -> int:
    return 0


def get_used_refresh_count() -> int:
    return 0


def _encode_jwt(payload: dict) -> str:
    return pyjwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def _decode_jwt(token: str) -> dict:
    try:
        return pyjwt.decode(
            token,
            _SECRET,
            algorithms=[_ALGORITHM],
            options={
                "require": ["sub", "exp", "iat", "jti"],
                "verify_iat": True,
            },
            leeway=_CLOCK_SKEW,
        )
    except pyjwt.PyJWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc


def create_access_token(subject: str, role: UserRole = UserRole.AUTHENTICATED) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "role": role.value,
        "exp": now + _ACCESS_TTL,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "token_type": "access",
    }
    return _encode_jwt(payload)


def create_refresh_token(subject: str) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "role": "refresh",
        "exp": now + _REFRESH_TTL,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "token_type": "refresh",
    }
    return _encode_jwt(payload)


def decode_token(token: str) -> TokenPayload:
    try:
        payload = _decode_jwt(token)
    except ValueError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

    jti = payload.get("jti", "")
    if jti and is_token_blacklisted(jti):
        raise ValueError("Token has been revoked")

    return TokenPayload(**payload)


def get_token_from_header(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None
