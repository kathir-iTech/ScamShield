from __future__ import annotations

import secrets
import time
import uuid
from typing import Optional

import jwt as pyjwt
from fastapi import Request

from core.auth.models import TokenPayload, UserRole
from core.auth.token_store import (
    TokenStore,
    create_token_store,
    get_token_store,
    set_token_store,
)
from core.logger import logger

_ACCESS_TTL = 3600
_REFRESH_TTL = 86400 * 30
_SECRET: str = secrets.token_urlsafe(32)
_ALGORITHM = "HS256"
_CLOCK_SKEW: int = 30
_ISSUER: str = "scamshield"
_AUDIENCE: str = "scamshield-api"


def configure(
    secret_key: Optional[str] = None,
    access_ttl: int = 3600,
    refresh_ttl: int = 86400 * 30,
    clock_skew: int = 30,
    blacklist_capacity: int = 100000,
    redis_url: Optional[str] = None,
    secret: Optional[str] = None,
    db_path: Optional[str] = None,
) -> None:
    global _SECRET, _ACCESS_TTL, _REFRESH_TTL, _CLOCK_SKEW
    if secret is not None:
        secret_key = secret
    if secret_key is not None:
        _SECRET = secret_key
    _ACCESS_TTL = access_ttl
    _REFRESH_TTL = refresh_ttl
    _CLOCK_SKEW = clock_skew
    store = create_token_store(
        redis_url=redis_url,
        max_entries=blacklist_capacity,
        db_path=db_path,
    )
    set_token_store(store)


def _store() -> TokenStore:
    return get_token_store()


def _repo():
    from core.storage.repositories import AuthTokenRepo

    return AuthTokenRepo()


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


def revoke_all_for_user(user_id: str, kind: str = "refresh") -> int:
    if not user_id:
        return 0
    try:
        jtis = _repo().list_jtis_for_user(
            user_id, kind=kind, statuses=("active", "used")
        )
        _repo().revoke_all_for_user(user_id, kind=kind)
    except Exception as exc:
        logger.warning("Could not persist token revocation for %s: %s", user_id, exc)
        jtis = []
    for jti in jtis:
        blacklist_token(jti)
    return len(jtis)


def get_blacklist_size() -> int:
    try:
        return _repo().count("revoked")
    except Exception:
        return 0


def get_used_refresh_count() -> int:
    try:
        return _repo().count("used")
    except Exception:
        return 0


def _encode_jwt(payload: dict) -> str:
    if not _SECRET:
        raise ValueError("Invalid token: JWT signing secret is not configured")
    claims = dict(payload)
    claims.setdefault("iss", _ISSUER)
    claims.setdefault("aud", _AUDIENCE)
    return pyjwt.encode(claims, _SECRET, algorithm=_ALGORITHM)


def _decode_jwt(token: str) -> dict:
    if not _SECRET:
        raise ValueError("Invalid token: JWT signing secret is not configured")
    try:
        return pyjwt.decode(
            token,
            _SECRET,
            algorithms=[_ALGORITHM],
            audience=_AUDIENCE,
            issuer=_ISSUER,
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


def create_refresh_token(subject: str, role: Optional[str] = None) -> str:
    now = int(time.time())
    original_role = role or ""
    payload = {
        "sub": subject,
        "role": "refresh",
        "original_role": original_role,
        "exp": now + _REFRESH_TTL,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "token_type": "refresh",
    }
    token = _encode_jwt(payload)
    try:
        _repo().store(
            payload["jti"],
            subject,
            "refresh",
            original_role or UserRole.AUTHENTICATED.value,
            float(payload["exp"]),
        )
    except Exception as exc:
        logger.warning("Could not persist refresh token: %s", exc)
    return token


def encode_token(
    subject: str,
    role: UserRole = UserRole.AUTHENTICATED,
) -> str:
    return create_access_token(subject, role=role)


def encode_access_token(
    subject: str,
    role: UserRole = UserRole.AUTHENTICATED,
) -> str:
    return create_access_token(subject, role=role)


def encode_refresh_token(subject: str, role: Optional[str] = None) -> str:
    return create_refresh_token(subject, role=role)


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
