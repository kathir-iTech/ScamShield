import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from connectors.base import BaseConnector
from connectors.manager import ConnectorManager, get_manager
from connectors.mock import MockThreatConnector
from connectors.cache import ConnectorCache
from connectors.exceptions import ConnectorError, ConnectorTimeoutError, ConnectorUnavailableError
from connectors.models import LookupResult
from config.settings import CONNECTOR_TIMEOUT


class TestMockThreatConnector:
    def test_name(self):
        conn = MockThreatConnector()
        assert conn.name == "mock_threat"

    def test_version(self):
        conn = MockThreatConnector()
        assert conn.version == "1.0.0"

    def test_supported_indicators(self):
        conn = MockThreatConnector()
        types = conn.supported_indicators()
        assert "url" in types
        assert "domain" in types
        assert "phone" in types
        assert "email" in types

    def test_health_returns_dict(self):
        conn = MockThreatConnector()
        h = conn.health()
        assert isinstance(h, dict)
        assert "status" in h

    def test_lookup_returns_lookup_result(self):
        conn = MockThreatConnector()
        result = conn.lookup("test@example.com", "email")
        assert isinstance(result, LookupResult)
        assert result.indicator == "test@example.com"

    def test_lookup_unknown_indicator(self):
        conn = MockThreatConnector()
        result = conn.lookup("zzzzzzzzzzzzzzzzz", "domain")
        assert isinstance(result, LookupResult)

    def test_metadata_includes_name(self):
        conn = MockThreatConnector()
        meta = conn.metadata()
        assert meta["name"] == "mock_threat"
        assert meta["version"] == "1.0.0"
        assert meta["enabled"] is True

    def test_normalize_strips_and_lowers(self):
        conn = MockThreatConnector()
        assert conn.normalize("  TEST@Example.COM  ", "email") == "test@example.com"


class TestConnectorManager:
    def test_manager_initialised(self):
        mgr = ConnectorManager()
        assert mgr is not None

    def test_cache_is_connector_cache(self):
        mgr = ConnectorManager()
        assert isinstance(mgr.cache, ConnectorCache)

    def test_lookup_empty_without_connectors(self):
        from connectors.registry import ConnectorRegistry
        ConnectorRegistry.clear()
        mgr = ConnectorManager()
        result = mgr.lookup("test@example.com", "email")
        assert isinstance(result, list)

    def test_lookup_with_mock_connector(self):
        from connectors.registry import ConnectorRegistry
        ConnectorRegistry.clear()
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        mgr = ConnectorManager()
        result = mgr.lookup("test@example.com", "email")
        assert isinstance(result, list)

    def test_lookup_all_returns_dict(self):
        from connectors.registry import ConnectorRegistry
        ConnectorRegistry.clear()
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        mgr = ConnectorManager()
        result = mgr.lookup_all({"email": ["test@example.com"]})
        assert isinstance(result, dict)

    def test_health_summary_returns_dict(self):
        from connectors.registry import ConnectorRegistry
        ConnectorRegistry.clear()
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        mgr = ConnectorManager()
        summary = mgr.health_summary()
        assert isinstance(summary, dict)

    def test_get_manager_singleton(self):
        from connectors.manager import _manager
        _manager = None
        m1 = get_manager()
        m2 = get_manager()
        assert m1 is m2


class TestConnectorCache:
    def test_cache_starts_empty(self):
        cache = ConnectorCache()
        assert cache.get("conn", "key", "type") is None

    def test_cache_can_store_and_retrieve(self):
        cache = ConnectorCache()
        cache.set("conn", "key", "type", {"result": "test"})
        result = cache.get("conn", "key", "type")
        assert result == {"result": "test"}

    def test_cache_default_ttl(self):
        cache = ConnectorCache(default_ttl=0)
        import time
        cache.set("conn", "key", "type", "value")
        time.sleep(0.01)
        assert cache.get("conn", "key", "type") is None

    def test_cache_evict(self):
        cache = ConnectorCache()
        cache.set("conn", "key", "type", "value")
        cache.evict("conn", "key", "type")
        assert cache.get("conn", "key", "type") is None

    def test_cache_clear(self):
        cache = ConnectorCache()
        cache.set("c1", "k1", "t1", "v1")
        cache.set("c2", "k2", "t2", "v2")
        cache.clear()
        assert cache.size == 0

    def test_cache_purge_expired(self):
        cache = ConnectorCache(default_ttl=-1)
        cache.set("c", "k", "t", "v")
        count = cache.purge_expired()
        assert count >= 0

    def test_cache_size_property(self):
        cache = ConnectorCache()
        assert cache.size == 0
        cache.set("c", "k", "t", "v")
        assert cache.size == 1


class TestConnectorExceptions:
    def test_connector_error_base(self):
        err = ConnectorError("something went wrong")
        assert "something went wrong" in str(err)

    def test_timeout_error(self):
        err = ConnectorTimeoutError("timed out")
        assert isinstance(err, ConnectorError)

    def test_unavailable_error(self):
        err = ConnectorUnavailableError("unavailable")
        assert isinstance(err, ConnectorError)


class TestLookupResult:
    def test_creation(self):
        result = LookupResult(
            indicator="test.com",
            indicator_type="domain",
            matched=True,
            risk="HIGH",
            confidence=0.9,
            source="test",
        )
        assert result.indicator == "test.com"
        assert result.matched is True
        assert result.risk == "HIGH"

    def test_to_dict(self):
        result = LookupResult(
            indicator="test.com",
            indicator_type="domain",
            matched=False,
            risk="UNKNOWN",
            confidence=0.0,
            source="test",
            latency=1.5,
        )
        d = result.to_dict()
        assert d["indicator"] == "test.com"
        assert d["latency"] == 1.5

    def test_timestamp_set_auto(self):
        result = LookupResult(
            indicator="test.com",
            indicator_type="domain",
            matched=False,
            risk="UNKNOWN",
            confidence=0.0,
            source="test",
        )
        assert result.timestamp > 0

    def test_error_field_optional(self):
        result = LookupResult(
            indicator="test.com",
            indicator_type="domain",
            matched=False,
            risk="UNKNOWN",
            confidence=0.0,
            source="test",
            error="test error",
        )
        assert result.error == "test error"
