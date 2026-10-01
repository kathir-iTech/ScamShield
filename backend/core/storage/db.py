from __future__ import annotations

import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from core.logger import logger

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id             TEXT PRIMARY KEY,
    email          TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    role           TEXT NOT NULL DEFAULT 'authenticated',
    display_name   TEXT NOT NULL DEFAULT '',
    status         TEXT NOT NULL DEFAULT 'active',
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until   REAL,
    created_at     REAL NOT NULL,
    updated_at     REAL NOT NULL,
    last_login_at  REAL
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS api_keys (
    key_id       TEXT PRIMARY KEY,
    key_hash     TEXT NOT NULL,
    salt         TEXT NOT NULL,
    prefix       TEXT NOT NULL,
    label        TEXT NOT NULL DEFAULT '',
    owner_id     TEXT NOT NULL DEFAULT '',
    role         TEXT NOT NULL DEFAULT 'authenticated',
    scopes       TEXT NOT NULL DEFAULT '[]',
    expires_at   REAL,
    revoked      INTEGER NOT NULL DEFAULT 0,
    usage_count  INTEGER NOT NULL DEFAULT 0,
    last_used_at REAL,
    created_at   REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(prefix);

CREATE TABLE IF NOT EXISTS analyses (
    id            TEXT PRIMARY KEY,
    request_id    TEXT NOT NULL DEFAULT '',
    user_id       TEXT NOT NULL DEFAULT '',
    source        TEXT NOT NULL DEFAULT 'api',
    input_hash    TEXT NOT NULL DEFAULT '',
    input_preview TEXT NOT NULL DEFAULT '',
    prediction    TEXT NOT NULL DEFAULT '',
    is_scam       INTEGER,
    confidence    REAL,
    risk_level    TEXT NOT NULL DEFAULT '',
    category      TEXT NOT NULL DEFAULT '',
    model_version TEXT NOT NULL DEFAULT '',
    duration_ms   REAL NOT NULL DEFAULT 0,
    payload       TEXT NOT NULL DEFAULT '{}',
    created_at    REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at);

CREATE TABLE IF NOT EXISTS audit_events (
    seq            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id       TEXT NOT NULL UNIQUE,
    event          TEXT NOT NULL,
    timestamp      REAL NOT NULL,
    level          TEXT NOT NULL DEFAULT 'INFO',
    request_id     TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    user_id        TEXT NOT NULL DEFAULT '',
    client_ip      TEXT NOT NULL DEFAULT '',
    resource       TEXT NOT NULL DEFAULT '',
    detail         TEXT NOT NULL DEFAULT '',
    metadata       TEXT NOT NULL DEFAULT '{}',
    prev_hash      TEXT NOT NULL DEFAULT '',
    hash           TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_events(event, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id, timestamp);

CREATE TABLE IF NOT EXISTS auth_tokens (
    jti        TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL DEFAULT '',
    kind       TEXT NOT NULL,
    role       TEXT NOT NULL DEFAULT '',
    status     TEXT NOT NULL DEFAULT 'active',
    expires_at REAL NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_expiry ON auth_tokens(expires_at);

CREATE TABLE IF NOT EXISTS feedback (
    id              TEXT PRIMARY KEY,
    analysis_id     TEXT NOT NULL DEFAULT '',
    user_id         TEXT NOT NULL DEFAULT '',
    verdict         TEXT NOT NULL,
    corrected_label TEXT NOT NULL DEFAULT '',
    note            TEXT NOT NULL DEFAULT '',
    context         TEXT NOT NULL DEFAULT '{}',
    resolved        INTEGER NOT NULL DEFAULT 0,
    created_at      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feedback_resolved ON feedback(resolved, created_at);

CREATE TABLE IF NOT EXISTS rate_limits (
    bucket        TEXT PRIMARY KEY,
    window_start  REAL NOT NULL,
    count         INTEGER NOT NULL DEFAULT 0,
    violations    INTEGER NOT NULL DEFAULT 0,
    blocked_until REAL NOT NULL DEFAULT 0,
    updated_at    REAL NOT NULL
);
"""


def _is_read(sql: str) -> bool:
    """True only for statements that cannot take SQLite's write lock.

    Deliberately conservative: CTEs may wrap INSERT/UPDATE, so ``WITH`` is
    treated as a write.
    """
    head = sql.lstrip().split(None, 1)[0].lower() if sql.strip() else ""
    return head in ("select", "pragma", "explain")


class Database:
    """Thread-local SQLite access with WAL, sane timeouts and a static schema.

    SQLite is deliberately used through the stdlib so the storage layer adds no
    runtime dependency; every statement in this package is parameterised.
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._local = threading.local()
        # Serialise writes only. Reads are left unlocked because WAL allows
        # concurrent readers; holding a lock across a BUSY wait would otherwise
        # serialise the stall across every thread.
        self._write_lock = threading.RLock()
        self._closed = False
        self._ensure_directory()
        self._configure()

    @property
    def path(self) -> str:
        return self._path

    def _ensure_directory(self) -> None:
        if self._path in (":memory:", "", ":memory:?cache=shared"):
            return
        parent = Path(self._path).expanduser().resolve().parent
        parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self._path,
            timeout=5.0,
            isolation_level=None,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA temp_store=MEMORY")
        return conn

    @property
    def conn(self) -> sqlite3.Connection:
        if self._closed:
            raise RuntimeError("Database is closed")
        existing = getattr(self._local, "conn", None)
        if existing is None:
            existing = self._connect()
            self._local.conn = existing
        return existing

    def _configure(self) -> None:
        with self._write_lock:
            self.conn.executescript(_SCHEMA)
            self.conn.execute(
                "INSERT OR IGNORE INTO schema_meta(key, value) VALUES(?, ?)",
                ("version", str(SCHEMA_VERSION)),
            )
        logger.debug("SQLite storage ready at %s", self._path)

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        if _is_read(sql):
            return self.conn.execute(sql, tuple(params))
        with self._write_lock:
            return self.conn.execute(sql, tuple(params))

    def executemany(self, sql: str, rows: Iterable[Iterable[Any]]) -> sqlite3.Cursor:
        with self._write_lock:
            return self.conn.executemany(sql, [tuple(r) for r in rows])

    def query(self, sql: str, params: Iterable[Any] = ()) -> List[sqlite3.Row]:
        return list(self.conn.execute(sql, tuple(params)).fetchall())

    def query_one(self, sql: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
        return self.conn.execute(sql, tuple(params)).fetchone()

    def transaction(self) -> "_Transaction":
        return _Transaction(self)

    def vacuum(self) -> None:
        with self._write_lock:
            self.conn.execute("VACUUM")

    def close(self) -> None:
        self._closed = True
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            try:
                conn.close()
            except sqlite3.Error:  # pragma: no cover - best effort teardown
                pass
            self._local.conn = None


class _Transaction:
    """Explicit BEGIN IMMEDIATE / COMMIT / ROLLBACK helper.

    The write lock is held for the whole transaction so concurrent writers queue
    on a cheap Python lock instead of contending for SQLite's write lock and
    burning their ``busy_timeout``.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    def __enter__(self) -> Database:
        self._db._write_lock.acquire()
        try:
            self._db.conn.execute("BEGIN IMMEDIATE")
        except BaseException:
            self._db._write_lock.release()
            raise
        return self._db

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            if exc_type is None:
                self._db.conn.execute("COMMIT")
            else:
                try:
                    self._db.conn.execute("ROLLBACK")
                except sqlite3.Error:  # pragma: no cover - rollback best effort
                    pass
        finally:
            self._db._write_lock.release()
        return False


_db: Optional[Database] = None
_db_lock = threading.Lock()


def default_db_path() -> str:
    """Resolve the storage path from the environment without importing settings.

    Importing `core.config` here would create an import cycle, so the variable
    is read directly with a portable default under ``backend/data``.
    """
    configured = os.environ.get("SCAMSHIELD_DB_PATH", "").strip()
    if configured:
        return configured
    return str(Path(__file__).resolve().parents[2] / "data" / "scamshield.db")


def init_db(path: Optional[str] = None) -> Database:
    global _db
    with _db_lock:
        if _db is not None:
            return _db
        _db = Database(path or default_db_path())
        return _db


def get_db() -> Database:
    if _db is None:
        return init_db()
    return _db


def set_db(db: Optional[Database]) -> None:
    global _db
    with _db_lock:
        _db = db


def close_db() -> None:
    global _db
    with _db_lock:
        if _db is not None:
            _db.close()
            _db = None


def db_status() -> Dict[str, Any]:
    if _db is None:
        return {"configured": False, "path": "", "healthy": False}
    try:
        row = _db.query_one("SELECT value FROM schema_meta WHERE key = 'version'")
        version = row["value"] if row else "unknown"
        return {
            "configured": True,
            "path": _db.path,
            "healthy": True,
            "schema_version": version,
            "checked_at": time.time(),
        }
    except sqlite3.Error as exc:
        return {"configured": True, "path": _db.path, "healthy": False, "error": str(exc)}
