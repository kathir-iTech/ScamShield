import pytest
from unittest.mock import patch, MagicMock

from connectors.base import BaseConnector
from connectors.manager import ConnectorManager, enrich_with_connectors
from connectors.models import LookupResult
from connectors.registry import ConnectorRegistry
from connectors.cache import ConnectorCache
from connectors.mock import MockThreatConnector
from connectors.exceptions import ConnectorError, ConnectorTimeoutError, ConnectorUnavailableError
from config.settings import CONNECTOR_TIMEOUT


def _make_mock_connector(name, supported_indicators=None, priority=100):
    conn = MagicMock()
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


class TestConnectorManager:
    def test_manager_initialization(self):
        manager = ConnectorManager()
        assert manager is not None

    def test_lookup_with_registered_connector(self):
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        manager = ConnectorManager()
        result = manager.lookup("test.com", "domain")
        assert isinstance(result, list)

    def test_lookup_unknown_returns_empty(self):
        manager = ConnectorManager()
        result = manager.lookup("test.com", "domain")
        assert result == []

    def test_lookup_all_with_data(self):
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        manager = ConnectorManager()
        result = manager.lookup_all({"email": ["test@example.com"]})
        assert isinstance(result, dict)

    def test_enrich_with_connectors(self):
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        analysis = {
            "entities": [{"type": "email", "value": "test@example.com"}],
            "detected_indicators": [],
        }
        result = enrich_with_connectors(analysis)
        assert isinstance(result, list)


class TestConnectorRegistry:
    def test_register_and_get(self):
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        assert ConnectorRegistry.get("mock_threat") is conn

    def test_get_nonexistent(self):
        assert ConnectorRegistry.get("nonexistent") is None

    def test_unregister(self):
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        ConnectorRegistry.unregister("mock_threat")
        assert ConnectorRegistry.get("mock_threat") is None

    def test_get_all(self):
        ConnectorRegistry.clear()
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        all_conn = ConnectorRegistry.get_all()
        assert "mock_threat" in all_conn

    def test_clear(self):
        conn = MockThreatConnector()
        ConnectorRegistry.register(conn)
        ConnectorRegistry.clear()
        assert ConnectorRegistry.get_all() == {}


class TestConnectorLookupResult:
    def test_lookup_result_creation(self):
        result = LookupResult(
            indicator="test.com",
            indicator_type="domain",
            matched=True,
            risk="HIGH",
            confidence=0.9,
            source="test",
        )
        assert result.matched is True
        assert result.risk == "HIGH"

    def test_lookup_result_to_dict(self):
        result = LookupResult(
            indicator="test.com",
            indicator_type="domain",
            matched=True,
            risk="HIGH",
            confidence=0.9,
            source="test",
        )
        d = result.to_dict()
        assert d["matched"] is True

    def test_lookup_result_defaults(self):
        result = LookupResult(
            indicator="test.com",
            indicator_type="domain",
            matched=False,
            risk="UNKNOWN",
            confidence=0.0,
            source="test",
        )
        assert result.error is None
        assert result.timestamp > 0
