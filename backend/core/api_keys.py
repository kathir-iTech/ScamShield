from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from core.logger import logger

PBKDF2_ITERATIONS: int = 210_000
_KEY_SALT_BYTES: int = 16
_KEY_RAW_BYTES: int = 24
_KEY_PREFIX_LENGTH: int = 8


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
    salt: str = ""


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
        self._loaded = False

    def create_key(
        self,
        name: str,
        scopes: Optional[List[str]] = None,
        role: str = "authenticated",
        expires_in_seconds: float = 0.0,
    ) -> tuple[str, str]:
        key_id = f"scm_{secrets.token_hex(8)}"
        raw_key = secrets.token_hex(_KEY_RAW_BYTES)
        prefix = raw_key[:_KEY_PREFIX_LENGTH]
        salt = secrets.token_hex(_KEY_SALT_BYTES)
        key_hash = self._hash_key(raw_key, salt)
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
            salt=salt,
        )
        self._keys[key_id] = api_key

        self._persist(
            "create",
            key_id=key_id,
            key_hash=key_hash,
            salt=salt,
            prefix=prefix,
            label=name,
            owner_id="",
            role=role,
            scopes=sorted(api_key.scopes),
            expires_at=api_key.expires_at or None,
        )

        logger.info(
            "API key created: %s (%s)",
            name, key_id,
            extra={"structured": {"event": "api_key_created", "key_id": key_id, "name": name}},
        )
        return key_id, raw_key

    def validate_key(self, raw_key: str) -> Optional[APIKey]:
        if not raw_key:
            return None
        return self.validate_key_by_prefix(raw_key[:_KEY_PREFIX_LENGTH], raw_key)

    def validate_key_by_prefix(self, prefix: str, raw_key: str) -> Optional[APIKey]:
        api_key = self.find_by_prefix(prefix)
        if api_key is None:
            return None
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
        if not hmac.compare_digest(api_key.key_hash, self._hash_key(raw_key, api_key.salt)):
            return None
        api_key.usage_count += 1
        api_key.last_used_at = time.time()
        self._persist("touch_usage", key_id=api_key.key_id)
        return api_key

    def find_by_prefix(self, prefix: str) -> Optional[APIKey]:
        for api_key in self._keys.values():
            if api_key.prefix == prefix:
                return api_key
        return None

    def revoke_key(self, key_id: str) -> bool:
        api_key = self._keys.get(key_id)
        if api_key is None:
            return False
        api_key.revoked = True
        self._persist("revoke", key_id=key_id)
        logger.info(
            "API key revoked: %s", key_id,
            extra={"structured": {"event": "api_key_revoked", "key_id": key_id}},
        )
        return True

    def rotate_key(self, key_id: str) -> Optional[tuple[str, str]]:
        api_key = self._keys.get(key_id)
        if api_key is None:
            return None
        new_raw = secrets.token_hex(_KEY_RAW_BYTES)
        new_prefix = new_raw[:_KEY_PREFIX_LENGTH]
        new_salt = secrets.token_hex(_KEY_SALT_BYTES)
        api_key.key_hash = self._hash_key(new_raw, new_salt)
        api_key.prefix = new_prefix
        api_key.salt = new_salt
        self._persist(
            "rotate",
            key_id=key_id,
            new_hash=api_key.key_hash,
            new_salt=new_salt,
            new_prefix=new_prefix,
        )
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

    def ensure_loaded(self) -> None:
        if self._loaded:
            return
        from core.storage.repositories import ApiKeyRepo

        try:
            rows = ApiKeyRepo().list_all(limit=1000)
        except Exception as exc:
            logger.warning("API key store unavailable, using in-memory index: %s", exc)
            return
        self._loaded = True
        for row in rows:
            key_id = row.get("key_id", "")
            if not key_id or key_id in self._keys:
                continue
            self._keys[key_id] = APIKey(
                key_id=key_id,
                key_hash=row.get("key_hash", ""),
                prefix=row.get("prefix", ""),
                name=row.get("label", ""),
                scopes=set(row.get("scopes") or []),
                role=row.get("role", "authenticated"),
                expires_at=float(row.get("expires_at") or 0.0),
                created_at=float(row.get("created_at") or 0.0),
                revoked=bool(row.get("revoked")),
                usage_count=int(row.get("usage_count") or 0),
                last_used_at=float(row.get("last_used_at") or 0.0),
                salt=row.get("salt", "") or "",
            )

    def _persist(self, operation: str, **params) -> None:
        from core.storage.repositories import ApiKeyRepo, StorageError

        repo = ApiKeyRepo()
        try:
            if operation == "create":
                repo.create(
                    key_id=params["key_id"],
                    key_hash=params["key_hash"],
                    salt=params["salt"],
                    prefix=params["prefix"],
                    label=params["label"],
                    owner_id=params["owner_id"],
                    role=params["role"],
                    scopes=params["scopes"],
                    expires_at=params["expires_at"],
                )
            elif operation == "revoke":
                repo.revoke(params["key_id"])
            elif operation == "rotate":
                repo.rotate(
                    params["key_id"],
                    params["new_hash"],
                    params["new_salt"],
                    params["new_prefix"],
                )
            elif operation == "touch_usage":
                repo.touch_usage(params["key_id"])
        except StorageError as exc:
            logger.error("API key persistence failed (%s): %s", operation, exc)
        except Exception as exc:  # pragma: no cover - storage layer never breaks a request
            logger.error("API key persistence failed (%s): %s", operation, exc)

    def _hash_key(self, raw_key: str, salt: str = "") -> str:
        salt_bytes = bytes.fromhex(salt) if salt else b""
        return hashlib.pbkdf2_hmac(
            "sha256",
            raw_key.encode("utf-8"),
            salt_bytes,
            PBKDF2_ITERATIONS,
        ).hex()


_manager = APIKeyManager()


def get_api_key_manager() -> APIKeyManager:
    _manager.ensure_loaded()
    return _manager
