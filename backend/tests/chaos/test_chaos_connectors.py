import pytest
from unittest.mock import patch, MagicMock

from connectors.base import BaseConnector
from connectors.manager import ConnectorManager
from connectors.exceptions import ConnectorError, ConnectorTimeoutError
from connectors.models import LookupResult
from connectors.registry import ConnectorRegistry
from connectors.mock import MockThreatConnector


def _make_mock_connector(name, supported_indicators=None, priority=100):
    conn = MagicMock(spec=BaseConnector)
    conn.name = name
    conn.version = "1.0.0"
    conn.priority = priority
    conn.enabled = True
    conn.supported_indicators.return_value = supported_indicators or ["domain"]
    conn.health.return_value = {"status": "ok"}
    return conn


@pytest.fixture(autouse=True)
def clear_registry():
    ConnectorRegistry.clear()
    yield
    ConnectorRegistry.clear()


class TestChaosConnectors:
    def test_connector_timeout_degrades_gracefully(self):
        mock_conn = _make_mock_connector("slow_connector")
        mock_conn.lookup.side_effect = ConnectorTimeoutError("timed out")

        ConnectorRegistry.register(mock_conn)
        manager = ConnectorManager()

        result = manager.lookup("example.com", "domain")
        assert isinstance(result, list)

    def test_connector_all_fail_still_produces_results(self):
        for i in range(3):
            conn = _make_mock_connector(f"fail_conn_{i}", priority=100 + i)
            conn.lookup.side_effect = ConnectorError(f"connector {i} failed")
            ConnectorRegistry.register(conn)

        manager = ConnectorManager()
        result = manager.lookup("example.com", "domain")
        assert isinstance(result, list)

    def test_connector_with_empty_indicators(self):
        mock_conn = _make_mock_connector("empty")
        mock_conn.lookup.return_value = LookupResult(
            indicator="example.com", indicator_type="domain",
            matched=False, risk="UNKNOWN", confidence=0.0, source="empty",
        )

        ConnectorRegistry.register(mock_conn)
        manager = ConnectorManager()
        result = manager.lookup("example.com", "domain")
        assert isinstance(result, list)

    def test_connector_with_empty_indicator_string(self):
        ConnectorRegistry.clear()
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        manager = ConnectorManager()
        result = manager.lookup("", "domain")
        assert result == []


class TestChaosCache:
    def test_cache_handles_corrupted_data(self):
        from connectors.cache import ConnectorCache
        cache = ConnectorCache()
        cache.set("conn", "key", "type", None)
        assert cache.get("conn", "key", "type") is None

    def test_cache_purge_empty(self):
        from connectors.cache import ConnectorCache
        cache = ConnectorCache()
        count = cache.purge_expired()
        assert count == 0

    def test_cache_evict_nonexistent(self):
        from connectors.cache import ConnectorCache
        cache = ConnectorCache()
        cache.evict("nonexistent", "key", "type")
        assert cache.get("nonexistent", "key", "type") is None


class TestChaosManager:
    def test_manager_health_summary_empty(self):
        manager = ConnectorManager()
        summary = manager.health_summary()
        assert isinstance(summary, dict)

    def test_manager_lookup_all_empty(self):
        manager = ConnectorManager()
        result = manager.lookup_all({})
        assert result == {}

    def test_manager_lookup_unregistered_type(self):
        ConnectorRegistry.clear()
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        manager = ConnectorManager()
        result = manager.lookup("test", "nonexistent_type")
        assert result == []
