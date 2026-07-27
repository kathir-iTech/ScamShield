import pytest
from unittest.mock import MagicMock, patch

from connectors.base import BaseConnector
from connectors.manager import ConnectorManager
from connectors.exceptions import ConnectorError, ConnectorTimeoutError, ConnectorUnavailableError
from connectors.models import LookupResult
from connectors.registry import ConnectorRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    ConnectorRegistry.clear()
    yield
    ConnectorRegistry.clear()


class TestConnectorNetworkFailures:
    def test_timeout_error_handled(self):
        mock_conn = MagicMock(spec=BaseConnector)
        type(mock_conn).name = "failing"
        mock_conn.supported_indicators.return_value = ["domain"]
        mock_conn.enabled = True
        mock_conn.priority = 100
        mock_conn.lookup.side_effect = ConnectorTimeoutError("timed out")

        ConnectorRegistry.register(mock_conn)
        manager = ConnectorManager()
        result = manager.lookup("test.com", "domain")
        assert isinstance(result, list)

    def test_connection_refused_handled(self):
        mock_conn = MagicMock(spec=BaseConnector)
        type(mock_conn).name = "refused"
        mock_conn.supported_indicators.return_value = ["domain"]
        mock_conn.enabled = True
        mock_conn.priority = 100
        mock_conn.lookup.side_effect = ConnectorError("Connection refused")

        ConnectorRegistry.register(mock_conn)
        manager = ConnectorManager()
        result = manager.lookup("test.com", "domain")
        assert isinstance(result, list)

    def test_malformed_response_handled(self):
        mock_conn = MagicMock(spec=BaseConnector)
        type(mock_conn).name = "malformed"
        mock_conn.supported_indicators.return_value = ["domain"]
        mock_conn.enabled = True
        mock_conn.priority = 100
        mock_conn.lookup.side_effect = ConnectorError("Invalid response format")

        ConnectorRegistry.register(mock_conn)
        manager = ConnectorManager()
        result = manager.lookup("test.com", "domain")
        assert isinstance(result, list)

    def test_empty_response_handled(self):
        mock_conn = MagicMock(spec=BaseConnector)
        type(mock_conn).name = "empty"
        mock_conn.supported_indicators.return_value = ["domain"]
        mock_conn.enabled = True
        mock_conn.priority = 100
        mock_conn.lookup.return_value = LookupResult(
            indicator="test.com", indicator_type="domain",
            matched=False, risk="UNKNOWN", confidence=0.0, source="empty",
        )

        ConnectorRegistry.register(mock_conn)
        manager = ConnectorManager()
        result = manager.lookup("test.com", "domain")
        assert isinstance(result, list)

    def test_unhealthy_connector_handled(self):
        mock_conn = MagicMock(spec=BaseConnector)
        type(mock_conn).name = "unhealthy"
        mock_conn.supported_indicators.return_value = ["domain"]
        mock_conn.enabled = True
        mock_conn.priority = 100
        mock_conn.health.return_value = {"status": "unhealthy"}
        mock_conn.lookup.return_value = LookupResult(
            indicator="test.com", indicator_type="domain",
            matched=False, risk="UNKNOWN", confidence=0.0, source="unhealthy",
        )

        ConnectorRegistry.register(mock_conn)
        manager = ConnectorManager()
        result = manager.lookup("test.com", "domain")
        assert isinstance(result, list)

    def test_all_connectors_fail_gracefully(self):
        for i in range(2):
            mock_conn = MagicMock(spec=BaseConnector)
            type(mock_conn).name = f"fail{i}"
            mock_conn.supported_indicators.return_value = ["domain"]
            mock_conn.enabled = True
            mock_conn.priority = 100
            mock_conn.health.return_value = {"status": "ok"}
            mock_conn.lookup.side_effect = ConnectorError("always fails")
            ConnectorRegistry.register(mock_conn)

        manager = ConnectorManager()
        result = manager.lookup("test.com", "domain")
        assert isinstance(result, list)


class TestConnectorErrorHierarchy:
    def test_connector_error_is_base(self):
        assert issubclass(ConnectorTimeoutError, ConnectorError)
        assert issubclass(ConnectorUnavailableError, ConnectorError)


class TestManagerWithNoConnectors:
    def test_lookup_empty_when_no_connectors(self):
        manager = ConnectorManager()
        result = manager.lookup("test.com", "domain")
        assert result == []
