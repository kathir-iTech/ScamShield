import time
import threading
from typing import Any, Dict, Optional, Tuple

from config.settings import CONNECTOR_CACHE_TTL


class ConnectorCache:
    def __init__(self, default_ttl: float = CONNECTOR_CACHE_TTL) -> None:
        self._default_ttl = default_ttl
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def _make_key(self, connector_name: str, indicator: str, indicator_type: str) -> str:
        norm = indicator.strip().lower()
        return f"{connector_name}:{indicator_type}:{norm}"

    def get(self, connector_name: str, indicator: str, indicator_type: str) -> Optional[Any]:
        key = self._make_key(connector_name, indicator, indicator_type)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expiry = entry
            if time.time() > expiry:
                del self._store[key]
                return None
            return value

    def set(
        self,
        connector_name: str,
        indicator: str,
        indicator_type: str,
        value: Any,
        ttl: Optional[float] = None,
    ) -> None:
        key = self._make_key(connector_name, indicator, indicator_type)
        expiry = time.time() + (ttl if ttl is not None else self._default_ttl)
        with self._lock:
            self._store[key] = (value, expiry)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def evict(self, connector_name: str, indicator: str, indicator_type: str) -> None:
        key = self._make_key(connector_name, indicator, indicator_type)
        with self._lock:
            self._store.pop(key, None)

    def purge_expired(self) -> int:
        now = time.time()
        count = 0
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]
                count += 1
        return count

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)
