from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from typing import Optional

from fastapi import Request

from core.auth.models import TokenPayload, UserRole

_ACCESS_TTL = 3600
_REFRESH_TTL = 86400 * 30
_SECRET: str = ""
_ALGORITHM = "HS256"
_CLOCK_SKEW: int = 30

_blacklisted_jti: set[str] = set()
_used_refresh_jti: set[str] = set()
_MAX_BLACKLIST = 100000


def configure(
    secret_key: str,
    access_ttl: int = 3600,
    refresh_ttl: int = 86400 * 30,
    clock_skew: int = 30,
    blacklist_capacity: int = 100000,
) -> None:
    global _SECRET, _ACCESS_TTL, _REFRESH_TTL, _CLOCK_SKEW, _MAX_BLACKLIST
    _SECRET = secret_key
    _ACCESS_TTL = access_ttl
    _REFRESH_TTL = refresh_ttl
    _CLOCK_SKEW = clock_skew
    _MAX_BLACKLIST = blacklist_capacity


def blacklist_token(jti: str) -> None:
    _blacklisted_jti.add(jti)
    if len(_blacklisted_jti) > _MAX_BLACKLIST:
        _blacklisted_jti.clear()


def is_token_blacklisted(jti: str) -> bool:
    return jti in _blacklisted_jti


def mark_refresh_used(jti: str) -> bool:
    if jti in _used_refresh_jti:
        _blacklisted_jti.add(jti)
        return False
    _used_refresh_jti.add(jti)
    if len(_used_refresh_jti) > _MAX_BLACKLIST:
        _used_refresh_jti.clear()
    return True


def is_refresh_reused(jti: str) -> bool:
    return jti in _used_refresh_jti


def revoke_all_for_user(user_id: str) -> None:
    pass


def get_blacklist_size() -> int:
    return len(_blacklisted_jti)


def get_used_refresh_count() -> int:
    return len(_used_refresh_jti)


def reset_blacklist() -> None:
    _blacklisted_jti.clear()
    _used_refresh_jti.clear()


def _sign(payload: str) -> str:
    return hmac.new(_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _encode_jwt(payload: dict) -> str:
    header = {"alg": _ALGORITHM, "typ": "JWT"}
    segments = []
    for part in (header, payload):
        encoded = json.dumps(part, separators=(",", ":"), sort_keys=True)
        segments.append(_base64url(encoded.encode("utf-8")))
    signing_input = ".".join(segments)
    signature = _sign(signing_input)
    segments.append(signature)
    return ".".join(segments)


def _decode_jwt(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")
    signing_input = ".".join(parts[:2])
    expected_sig = _sign(signing_input)
    actual_sig = parts[2]
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature")
    decoded = json.loads(_base64url_decode(parts[1]))
    return decoded


def _base64url(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(s: str) -> bytes:
    import base64
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _base64url_encode_str(s: str) -> str:
    return _base64url(s.encode("utf-8"))


def _base64url_decode_str(s: str) -> str:
    return _base64url_decode(s).decode("utf-8")


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
    except (ValueError, KeyError) as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

    jti = payload.get("jti", "")
    if jti and is_token_blacklisted(jti):
        raise ValueError("Token has been revoked")

    exp = payload.get("exp", 0)
    if exp + _CLOCK_SKEW < int(time.time()):
        raise ValueError("Token has expired")

    iat = payload.get("iat", 0)
    if iat > int(time.time()) + _CLOCK_SKEW:
        raise ValueError("Token issued in the future")

    return TokenPayload(**payload)


def get_token_from_header(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None
