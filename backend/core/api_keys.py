from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from core.logger import logger


@dataclass
class APIKey:
    key_id: str
    key_hash: str
    prefix: str
    name: str
    scopes: Set[str] = field(default_factory=set)
    role: str = "authenticated"
    expires_at: float = 0.0
    created_at: float = 0.0
    revoked: bool = False
    usage_count: int = 0
    last_used_at: float = 0.0


SCOPES = {
    "analyze:text": "Submit text for analysis",
    "analyze:image": "Submit images for analysis",
    "analyze:investigation": "Run investigations",
    "health:read": "Read health endpoints",
    "metrics:read": "Read metrics",
    "admin:all": "Full admin access",
}


class APIKeyManager:
    def __init__(self):
        self._keys: Dict[str, APIKey] = {}

    def create_key(
        self,
        name: str,
        scopes: Optional[List[str]] = None,
        role: str = "authenticated",
        expires_in_seconds: float = 0.0,
    ) -> tuple[str, str]:
        key_id = f"scm_{secrets.token_hex(8)}"
        raw_key = secrets.token_hex(24)
        prefix = raw_key[:8]
        key_hash = self._hash_key(raw_key)
        now = time.time()
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            prefix=prefix,
            name=name,
            scopes=set(scopes or []),
            role=role,
            expires_at=now + expires_in_seconds if expires_in_seconds > 0 else 0.0,
            created_at=now,
        )
        self._keys[key_id] = api_key

        logger.info(
            "API key created: %s (%s)",
            name, key_id,
            extra={"structured": {"event": "api_key_created", "key_id": key_id, "name": name}},
        )
        return key_id, raw_key

    def validate_key(self, raw_key: str) -> Optional[APIKey]:
        key_hash = self._hash_key(raw_key)
        for api_key in self._keys.values():
            if hmac.compare_digest(api_key.key_hash, key_hash):
                if api_key.revoked:
                    logger.warning(
                        "Attempted use of revoked API key: %s", api_key.key_id,
                        extra={"structured": {"event": "revoked_key_used", "key_id": api_key.key_id}},
                    )
                    return None
                if api_key.expires_at > 0 and time.time() > api_key.expires_at:
                    logger.warning(
                        "Attempted use of expired API key: %s", api_key.key_id,
                        extra={"structured": {"event": "expired_key_used", "key_id": api_key.key_id}},
                    )
                    return None
                api_key.usage_count += 1
                api_key.last_used_at = time.time()
                return api_key
        return None

    def validate_key_by_prefix(self, prefix: str, raw_key: str) -> Optional[APIKey]:
        for api_key in self._keys.values():
            if api_key.prefix == prefix and not api_key.revoked:
                if hmac.compare_digest(api_key.key_hash, self._hash_key(raw_key)):
                    if api_key.expires_at > 0 and time.time() > api_key.expires_at:
                        return None
                    api_key.usage_count += 1
                    api_key.last_used_at = time.time()
                    return api_key
        return None

    def revoke_key(self, key_id: str) -> bool:
        api_key = self._keys.get(key_id)
        if api_key is None:
            return False
        api_key.revoked = True
        logger.info(
            "API key revoked: %s", key_id,
            extra={"structured": {"event": "api_key_revoked", "key_id": key_id}},
        )
        return True

    def rotate_key(self, key_id: str) -> Optional[tuple[str, str]]:
        api_key = self._keys.get(key_id)
        if api_key is None:
            return None
        new_raw = secrets.token_hex(24)
        new_prefix = new_raw[:8]
        api_key.key_hash = self._hash_key(new_raw)
        api_key.prefix = new_prefix
        logger.info(
            "API key rotated: %s", key_id,
            extra={"structured": {"event": "api_key_rotated", "key_id": key_id}},
        )
        return key_id, new_raw

    def get_key_info(self, key_id: str) -> Optional[Dict]:
        api_key = self._keys.get(key_id)
        if api_key is None:
            return None
        return {
            "key_id": api_key.key_id,
            "prefix": api_key.prefix,
            "name": api_key.name,
            "scopes": list(api_key.scopes),
            "role": api_key.role,
            "expires_at": api_key.expires_at,
            "created_at": api_key.created_at,
            "revoked": api_key.revoked,
            "usage_count": api_key.usage_count,
            "last_used_at": api_key.last_used_at,
        }

    def list_keys(self) -> List[Dict]:
        return [self.get_key_info(k.key_id) for k in self._keys.values() if k is not None]

    def check_scope(self, key: APIKey, required_scope: str) -> bool:
        if "admin:all" in key.scopes:
            return True
        if not key.scopes:
            return False
        return required_scope in key.scopes

    def _hash_key(self, raw_key: str) -> str:
        salt = "scamshield-apikey-v1"
        return hashlib.sha256(f"{salt}:{raw_key}".encode("utf-8")).hexdigest()


_manager = APIKeyManager()


def get_api_key_manager() -> APIKeyManager:
    return _manager
