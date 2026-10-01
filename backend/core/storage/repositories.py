from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import time
import uuid
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from core.logger import logger
from core.storage.db import Database, get_db

GENESIS_HASH: str = "0" * 64

_ANALYSIS_COLUMNS: Tuple[str, ...] = (
    "id",
    "request_id",
    "user_id",
    "source",
    "input_hash",
    "input_preview",
    "prediction",
    "is_scam",
    "confidence",
    "risk_level",
    "category",
    "model_version",
    "duration_ms",
    "payload",
    "created_at",
)

_AUDIT_COLUMNS: Tuple[str, ...] = (
    "event_id",
    "event",
    "timestamp",
    "level",
    "request_id",
    "correlation_id",
    "user_id",
    "client_ip",
    "resource",
    "detail",
    "metadata",
)

_FEEDBACK_COLUMNS: Tuple[str, ...] = (
    "id",
    "analysis_id",
    "user_id",
    "verdict",
    "corrected_label",
    "note",
    "context",
    "resolved",
    "created_at",
)


class StorageError(Exception):
    """Base error raised by the storage repositories."""


class DuplicateUserError(StorageError):
    """Raised when a unique constraint on a user record is violated."""


class NotFoundError(StorageError):
    """Raised when an expected record does not exist."""


class ConflictError(StorageError):
    """Raised when a write conflicts with the current state of a record."""


def _resolve(db: Optional[Database]) -> Database:
    return db if db is not None else get_db()


def _as_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def _as_dicts(rows: Iterable[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [_as_dict(row) for row in rows]  # type: ignore[misc]


def _loads_list(raw: Any) -> List[Any]:
    if isinstance(raw, list):
        return raw
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def _constraint_message(exc: sqlite3.Error) -> str:
    return str(exc).lower()


class UserRepo:
    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db

    @property
    def db(self) -> Database:
        return _resolve(self._db)

    def create(
        self,
        email: str,
        password_hash: str,
        role: str = "authenticated",
        display_name: str = "",
    ) -> Dict[str, Any]:
        now = time.time()
        user_id = f"usr_{secrets.token_hex(12)}"
        try:
            self.db.execute(
                "INSERT INTO users (id, email, password_hash, role, display_name, status,"
                " failed_attempts, locked_until, created_at, updated_at, last_login_at)"
                " VALUES (?, ?, ?, ?, ?, 'active', 0, NULL, ?, ?, NULL)",
                (user_id, email, password_hash, role, display_name, now, now),
            )
        except sqlite3.IntegrityError as exc:
            if "unique" in _constraint_message(exc) or "email" in _constraint_message(exc):
                raise DuplicateUserError(f"User already exists: {email}") from exc
            raise StorageError(str(exc)) from exc
        except sqlite3.Error as exc:
            raise StorageError(str(exc)) from exc
        created = self.get_by_id(user_id)
        if created is None:
            raise StorageError("User record could not be read back after insert")
        return created

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return _as_dict(self.db.query_one("SELECT * FROM users WHERE id = ?", (user_id,)))

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return _as_dict(self.db.query_one("SELECT * FROM users WHERE email = ?", (email,)))

    def list(self, limit: int = 100) -> List[Dict[str, Any]]:
        return _as_dicts(
            self.db.query(
                "SELECT * FROM users ORDER BY created_at DESC, id ASC LIMIT ?",
                (max(int(limit), 0),),
            )
        )

    def count(self) -> int:
        row = self.db.query_one("SELECT COUNT(*) AS total FROM users")
        return int(row["total"]) if row else 0

    def record_login_success(self, user_id: str) -> None:
        now = time.time()
        self.db.execute(
            "UPDATE users SET last_login_at = ?, failed_attempts = 0,"
            " locked_until = NULL, updated_at = ? WHERE id = ?",
            (now, now, user_id),
        )

    def record_login_failure(self, user_id: str, threshold: int, lock_seconds: int) -> bool:
        row = self.get_by_id(user_id)
        if row is None:
            return False
        now = time.time()
        attempts = int(row["failed_attempts"]) + 1
        locked_until: Optional[float] = row["locked_until"]
        if attempts >= max(int(threshold), 1):
            locked_until = now + max(int(lock_seconds), 0)
        self.db.execute(
            "UPDATE users SET failed_attempts = ?, locked_until = ?, updated_at = ?"
            " WHERE id = ?",
            (attempts, locked_until, now, user_id),
        )
        return locked_until is not None and float(locked_until) > now

    @staticmethod
    def is_locked(row: Optional[Dict[str, Any]], now: Optional[float] = None) -> bool:
        if not row:
            return False
        locked_until = row.get("locked_until")
        if locked_until in (None, "", 0, 0.0):
            return False
        return float(locked_until) > (now if now is not None else time.time())

    def set_role(self, user_id: str, role: str) -> bool:
        cursor = self.db.execute(
            "UPDATE users SET role = ?, updated_at = ? WHERE id = ?",
            (role, time.time(), user_id),
        )
        return cursor.rowcount > 0

    def set_status(self, user_id: str, status: str) -> bool:
        cursor = self.db.execute(
            "UPDATE users SET status = ?, updated_at = ? WHERE id = ?",
            (status, time.time(), user_id),
        )
        return cursor.rowcount > 0

    def update_password(self, user_id: str, password_hash: str) -> bool:
        now = time.time()
        cursor = self.db.execute(
            "UPDATE users SET password_hash = ?, failed_attempts = 0,"
            " locked_until = NULL, updated_at = ? WHERE id = ?",
            (password_hash, now, user_id),
        )
        return cursor.rowcount > 0


class ApiKeyRepo:
    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db

    @property
    def db(self) -> Database:
        return _resolve(self._db)

    @staticmethod
    def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        data = _as_dict(row)
        if data is None:
            return None
        data["scopes"] = _loads_list(data.get("scopes"))
        data["revoked"] = bool(data.get("revoked"))
        return data

    def create(
        self,
        key_id: str,
        key_hash: str,
        salt: str,
        prefix: str,
        label: str = "",
        owner_id: str = "",
        role: str = "authenticated",
        scopes: Optional[Sequence[str]] = None,
        expires_at: Optional[float] = None,
    ) -> Dict[str, Any]:
        now = time.time()
        try:
            self.db.execute(
                "INSERT INTO api_keys (key_id, key_hash, salt, prefix, label, owner_id,"
                " role, scopes, expires_at, revoked, usage_count, last_used_at, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, NULL, ?)",
                (
                    key_id,
                    key_hash,
                    salt,
                    prefix,
                    label,
                    owner_id,
                    role,
                    json.dumps(list(scopes or [])),
                    expires_at,
                    now,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ConflictError(f"API key already exists: {key_id}") from exc
        except sqlite3.Error as exc:
            raise StorageError(str(exc)) from exc
        created = self.get_by_id(key_id)
        if created is None:
            raise StorageError("API key record could not be read back after insert")
        return created

    def get_by_id(self, key_id: str) -> Optional[Dict[str, Any]]:
        return self._row_to_dict(
            self.db.query_one("SELECT * FROM api_keys WHERE key_id = ?", (key_id,))
        )

    def list_by_prefix(self, prefix: str) -> List[Dict[str, Any]]:
        rows = self.db.query(
            "SELECT * FROM api_keys WHERE prefix = ? ORDER BY created_at ASC", (prefix,)
        )
        return [self._row_to_dict(row) for row in rows]  # type: ignore[misc]

    def list_all(self, limit: int = 200) -> List[Dict[str, Any]]:
        rows = self.db.query(
            "SELECT * FROM api_keys ORDER BY created_at DESC LIMIT ?", (max(int(limit), 0),)
        )
        return [self._row_to_dict(row) for row in rows]  # type: ignore[misc]

    def revoke(self, key_id: str) -> bool:
        cursor = self.db.execute(
            "UPDATE api_keys SET revoked = 1 WHERE key_id = ?", (key_id,)
        )
        return cursor.rowcount > 0

    def rotate(self, key_id: str, new_hash: str, new_salt: str, new_prefix: str) -> bool:
        cursor = self.db.execute(
            "UPDATE api_keys SET key_hash = ?, salt = ?, prefix = ? WHERE key_id = ?",
            (new_hash, new_salt, new_prefix, key_id),
        )
        return cursor.rowcount > 0

    def touch_usage(self, key_id: str) -> None:
        self.db.execute(
            "UPDATE api_keys SET usage_count = usage_count + 1, last_used_at = ?"
            " WHERE key_id = ?",
            (time.time(), key_id),
        )


class AnalysisRepo:
    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db

    @property
    def db(self) -> Database:
        return _resolve(self._db)

    def insert(self, record: Dict[str, Any]) -> str:
        payload = dict(record)
        analysis_id = str(payload.get("id") or uuid.uuid4().hex)
        payload["id"] = analysis_id
        columns = [c for c in _ANALYSIS_COLUMNS if c in payload and payload[c] is not None]
        if "created_at" not in payload:
            payload["created_at"] = time.time()
            columns = [c for c in _ANALYSIS_COLUMNS if c in payload and payload[c] is not None]
        placeholders = ", ".join("?" for _ in columns)
        values = tuple(payload[c] for c in columns)
        try:
            self.db.execute(
                f"INSERT INTO analyses ({', '.join(columns)}) VALUES ({placeholders})",
                values,
            )
        except sqlite3.Error as exc:
            raise StorageError(str(exc)) from exc
        return analysis_id

    def get(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        return _as_dict(
            self.db.query_one("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
        )

    def list_for_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return _as_dicts(
            self.db.query(
                "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, max(int(limit), 0),),
            )
        )

    def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return _as_dicts(
            self.db.query(
                "SELECT * FROM analyses ORDER BY created_at DESC LIMIT ?",
                (max(int(limit), 0),),
            )
        )

    def count(self) -> int:
        row = self.db.query_one("SELECT COUNT(*) AS total FROM analyses")
        return int(row["total"]) if row else 0


class AuditRepo:
    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db

    @property
    def db(self) -> Database:
        return _resolve(self._db)

    @staticmethod
    def _canonical(payload: Dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)

    @staticmethod
    def _build_payload(record: Dict[str, Any]) -> Dict[str, Any]:
        metadata = record.get("metadata", "{}")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata) if metadata else {}
            except ValueError:
                metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
        return {
            "event_id": record.get("event_id", ""),
            "event": record.get("event", ""),
            "timestamp": record.get("timestamp", 0.0),
            "level": record.get("level", "INFO"),
            "request_id": record.get("request_id", ""),
            "correlation_id": record.get("correlation_id", ""),
            "user_id": record.get("user_id", ""),
            "client_ip": record.get("client_ip", ""),
            "resource": record.get("resource", ""),
            "detail": record.get("detail", ""),
            "metadata": metadata,
        }

    def append(self, record: Dict[str, Any]) -> str:
        payload = dict(record)
        payload.setdefault("event_id", uuid.uuid4().hex)
        payload.setdefault("timestamp", time.time())
        payload.setdefault("level", "INFO")
        payload.setdefault("metadata", {})

        columns = [c for c in _AUDIT_COLUMNS if c in payload]
        missing = [c for c in _AUDIT_COLUMNS if c not in payload]
        for column in missing:
            payload[column] = "{}" if column == "metadata" else (0.0 if column == "timestamp" else "")

        payload["metadata"] = json.dumps(payload["metadata"], default=str)

        try:
            with self.db.transaction() as conn:
                row = conn.query_one(
                    "SELECT hash FROM audit_events ORDER BY seq DESC LIMIT 1"
                )
                prev_hash = row["hash"] if row and row["hash"] else GENESIS_HASH
                canonical = self._canonical(self._build_payload(payload))
                digest = hashlib.sha256((prev_hash + canonical).encode("utf-8")).hexdigest()
                placeholders = ", ".join("?" for _ in columns)
                conn.execute(
                    f"INSERT INTO audit_events ({', '.join(columns)}, prev_hash, hash)"
                    f" VALUES ({placeholders}, ?, ?)",
                    tuple(payload[c] for c in columns) + (prev_hash, digest),
                )
        except sqlite3.Error as exc:
            raise StorageError(str(exc)) from exc
        return digest

    def verify_chain(self) -> Tuple[bool, str]:
        rows = self.db.query("SELECT * FROM audit_events ORDER BY seq ASC")
        previous = GENESIS_HASH
        for row in rows:
            stored_prev = row["prev_hash"] or GENESIS_HASH
            if stored_prev != previous:
                return False, f"broken chain at seq {row['seq']}: prev_hash mismatch"
            record = {c: row[c] for c in _AUDIT_COLUMNS}
            canonical = self._canonical(self._build_payload(record))
            expected = hashlib.sha256((stored_prev + canonical).encode("utf-8")).hexdigest()
            if expected != row["hash"]:
                return False, f"tampered payload at seq {row['seq']}"
            previous = row["hash"]
        return True, "ok"

    def list(self, limit: int = 100, event: Optional[str] = None) -> List[Dict[str, Any]]:
        if event:
            rows = self.db.query(
                "SELECT * FROM audit_events WHERE event = ? ORDER BY seq DESC LIMIT ?",
                (event, max(int(limit), 0),),
            )
        else:
            rows = self.db.query(
                "SELECT * FROM audit_events ORDER BY seq DESC LIMIT ?", (max(int(limit), 0),)
            )
        return _as_dicts(rows)

    def count(self) -> int:
        row = self.db.query_one("SELECT COUNT(*) AS total FROM audit_events")
        return int(row["total"]) if row else 0


class AuthTokenRepo:
    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db

    @property
    def db(self) -> Database:
        return _resolve(self._db)

    def store(
        self,
        jti: str,
        user_id: str,
        kind: str,
        role: str,
        expires_at: float,
    ) -> None:
        try:
            self.db.execute(
                "INSERT OR REPLACE INTO auth_tokens"
                " (jti, user_id, kind, role, status, expires_at, created_at)"
                " VALUES (?, ?, ?, ?, 'active', ?, ?)",
                (jti, user_id, kind, role, float(expires_at), time.time()),
            )
        except sqlite3.Error as exc:
            raise StorageError(str(exc)) from exc

    def is_revoked(self, jti: str) -> bool:
        row = self.db.query_one("SELECT status FROM auth_tokens WHERE jti = ?", (jti,))
        if row is None:
            return False
        return row["status"] in ("revoked", "used")

    def is_blacklisted(self, jti: str) -> bool:
        return self.is_revoked(jti)

    def is_refresh_reused(self, jti: str) -> bool:
        row = self.db.query_one("SELECT status FROM auth_tokens WHERE jti = ?", (jti,))
        return row is not None and row["status"] == "used"

    def blacklist(self, jti: str, ttl_seconds: float = 0.0) -> None:
        try:
            cursor = self.db.execute(
                "UPDATE auth_tokens SET status = 'revoked' WHERE jti = ?", (jti,)
            )
            if cursor.rowcount == 0:
                expires_at = time.time() + (ttl_seconds if ttl_seconds > 0 else 86400 * 30)
                self.db.execute(
                    "INSERT OR REPLACE INTO auth_tokens"
                    " (jti, user_id, kind, role, status, expires_at, created_at)"
                    " VALUES (?, '', 'access', '', 'revoked', ?, ?)",
                    (jti, expires_at, time.time()),
                )
        except sqlite3.Error as exc:
            raise StorageError(str(exc)) from exc

    def revoke(self, jti: str) -> bool:
        cursor = self.db.execute(
            "UPDATE auth_tokens SET status = 'revoked' WHERE jti = ?", (jti,)
        )
        return cursor.rowcount > 0

    def revoke_all_for_user(self, user_id: str, kind: str = "refresh") -> int:
        cursor = self.db.execute(
            "UPDATE auth_tokens SET status = 'revoked'"
            " WHERE user_id = ? AND kind = ? AND status <> 'revoked'",
            (user_id, kind),
        )
        return int(cursor.rowcount)

    def count(self, status: str) -> int:
        row = self.db.query_one(
            "SELECT COUNT(*) AS total FROM auth_tokens WHERE status = ?", (status,)
        )
        return int(row["total"]) if row else 0

    def list_jtis_for_user(
        self,
        user_id: str,
        kind: Optional[str] = None,
        statuses: Sequence[str] = ("active",),
    ) -> List[str]:
        statuses = tuple(statuses)
        placeholders = ", ".join("?" for _ in statuses)
        sql = f"SELECT jti FROM auth_tokens WHERE user_id = ? AND status IN ({placeholders})"
        params: List[Any] = [user_id, *statuses]
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        sql += " ORDER BY created_at ASC"
        return [row["jti"] for row in self.db.query(sql, tuple(params))]

    def mark_refresh_used(self, jti: str) -> bool:
        cursor = self.db.execute(
            "UPDATE auth_tokens SET status = 'used' WHERE jti = ? AND status = 'active'",
            (jti,),
        )
        if cursor.rowcount == 1:
            return True
        row = self.db.query_one("SELECT status FROM auth_tokens WHERE jti = ?", (jti,))
        if row is None:
            self.db.execute(
                "INSERT OR REPLACE INTO auth_tokens"
                " (jti, user_id, kind, role, status, expires_at, created_at)"
                " VALUES (?, '', 'refresh', '', 'used', ?, ?)",
                (jti, time.time() + 86400, time.time()),
            )
            return True
        if row["status"] == "active":
            self.db.execute(
                "UPDATE auth_tokens SET status = 'used' WHERE jti = ?", (jti,)
            )
            return True
        return False

    def clear_revoked(self) -> int:
        cursor = self.db.execute(
            "DELETE FROM auth_tokens WHERE status IN ('revoked', 'used')"
        )
        return int(cursor.rowcount)

    def purge_expired(self, now: Optional[float] = None) -> int:
        cursor = self.db.execute(
            "DELETE FROM auth_tokens WHERE expires_at < ?", (now if now is not None else time.time(),)
        )
        return int(cursor.rowcount)


class FeedbackRepo:
    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db

    @property
    def db(self) -> Database:
        return _resolve(self._db)

    def insert(
        self, record: Optional[Dict[str, Any]] = None, **fields: Any
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = dict(record) if record else {}
        payload.update(fields)
        feedback_id = str(payload.get("id") or uuid.uuid4().hex)
        payload["id"] = feedback_id
        payload.setdefault("created_at", time.time())
        payload.setdefault("resolved", 0)
        for column in _FEEDBACK_COLUMNS:
            payload.setdefault(column, "" if column != "resolved" else 0)
        if isinstance(payload.get("context"), (dict, list)):
            payload["context"] = json.dumps(payload["context"], default=str)
        columns = [c for c in _FEEDBACK_COLUMNS if c in payload]
        placeholders = ", ".join("?" for _ in columns)
        try:
            self.db.execute(
                f"INSERT INTO feedback ({', '.join(columns)}) VALUES ({placeholders})",
                tuple(payload[c] for c in columns),
            )
        except sqlite3.IntegrityError as exc:
            raise ConflictError(f"Feedback already exists: {feedback_id}") from exc
        except sqlite3.Error as exc:
            raise StorageError(str(exc)) from exc
        return self.get(feedback_id) or payload

    def get(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        return _as_dict(
            self.db.query_one("SELECT * FROM feedback WHERE id = ?", (feedback_id,))
        )

    def list_unresolved(self, limit: int = 50) -> List[Dict[str, Any]]:
        return _as_dicts(
            self.db.query(
                "SELECT * FROM feedback WHERE resolved = 0 ORDER BY created_at ASC LIMIT ?",
                (max(int(limit), 0),),
            )
        )

    def resolve(self, feedback_id: str) -> bool:
        cursor = self.db.execute(
            "UPDATE feedback SET resolved = 1 WHERE id = ?", (feedback_id,)
        )
        return cursor.rowcount > 0

    def count_unresolved(self) -> int:
        row = self.db.query_one("SELECT COUNT(*) AS total FROM feedback WHERE resolved = 0")
        return int(row["total"]) if row else 0


class RateLimitRepo:
    VIOLATION_THRESHOLD: int = 3

    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db

    @property
    def db(self) -> Database:
        return _resolve(self._db)

    @staticmethod
    def _empty(bucket: str, now: float) -> Dict[str, Any]:
        return {
            "bucket": bucket,
            "window_start": now,
            "count": 0,
            "violations": 0,
            "blocked_until": 0.0,
            "updated_at": now,
        }

    def hit(
        self,
        bucket: str,
        window_seconds: int,
        limit: int,
        block_seconds: int,
    ) -> Dict[str, Any]:
        now = time.time()
        window_seconds = max(int(window_seconds), 1)
        limit = max(int(limit), 0)
        block_seconds = max(int(block_seconds), 0)

        with self.db.transaction() as conn:
            row = conn.query_one(
                "SELECT bucket, window_start, count, violations, blocked_until"
                " FROM rate_limits WHERE bucket = ?",
                (bucket,),
            )
            state = self._empty(bucket, now)
            if row is not None:
                state = {
                    "bucket": bucket,
                    "window_start": float(row["window_start"]),
                    "count": int(row["count"]),
                    "violations": int(row["violations"]),
                    "blocked_until": float(row["blocked_until"]),
                    "updated_at": now,
                }

            if state["blocked_until"] > now:
                result = self._result(state, limit, window_seconds, allowed=False)
                conn.execute(
                    "UPDATE rate_limits SET updated_at = ? WHERE bucket = ?",
                    (now, bucket),
                )
                return result

            if state["blocked_until"] > 0:
                state["blocked_until"] = 0.0
                state["violations"] = 0

            if now - state["window_start"] >= window_seconds:
                state["window_start"] = now
                state["count"] = 0
                state["violations"] = 0

            if state["count"] >= limit:
                state["violations"] += 1
                if state["violations"] >= self.VIOLATION_THRESHOLD and block_seconds > 0:
                    state["blocked_until"] = now + block_seconds
                    logger.warning(
                        "Rate limit bucket %s blocked for %d seconds after %d violations",
                        bucket,
                        block_seconds,
                        state["violations"],
                        extra={
                            "structured": {
                                "event": "rate_limit_blocked",
                                "bucket": bucket,
                                "duration": block_seconds,
                            }
                        },
                    )
                allowed = False
            else:
                state["count"] += 1
                allowed = True

            state["updated_at"] = now
            conn.execute(
                "INSERT INTO rate_limits (bucket, window_start, count, violations,"
                " blocked_until, updated_at) VALUES (?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(bucket) DO UPDATE SET window_start = excluded.window_start,"
                " count = excluded.count, violations = excluded.violations,"
                " blocked_until = excluded.blocked_until, updated_at = excluded.updated_at",
                (
                    bucket,
                    state["window_start"],
                    state["count"],
                    state["violations"],
                    state["blocked_until"],
                    now,
                ),
            )

        return self._result(state, limit, window_seconds, allowed=allowed)

    @staticmethod
    def _result(
        state: Dict[str, Any], limit: int, window_seconds: int, allowed: bool
    ) -> Dict[str, Any]:
        return {
            "allowed": allowed,
            "limit": limit,
            "remaining": max(0, limit - int(state["count"])),
            "reset": float(state["window_start"]) + float(window_seconds),
            "blocked_until": float(state["blocked_until"]),
            "violations": int(state["violations"]),
            "count": int(state["count"]),
        }

    def reset(self, bucket: str) -> None:
        self.db.execute("DELETE FROM rate_limits WHERE bucket = ?", (bucket,))


def verify_audit_chain(db: Optional[Database] = None) -> Tuple[bool, str]:
    return AuditRepo(db).verify_chain()
