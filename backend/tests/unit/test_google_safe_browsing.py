import json
import time
from unittest.mock import patch, MagicMock
from typing import Dict, List
from urllib.error import HTTPError, URLError

from connectors.models import LookupResult
from connectors.registry import ConnectorRegistry


def _make_mock_response(data: Dict, status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.__enter__.return_value.read.return_value = json.dumps(data).encode("utf-8")
    mock.__exit__.return_value = None
    if status != 200:
        mock.getcode.return_value = status
    return mock


def _make_http_error(code: int) -> HTTPError:
    return HTTPError(
        url="https://safebrowsing.googleapis.com/v4/threatMatches:find",
        code=code,
        msg="Error",
        hdrs={},
        fp=None,
    )


class TestGoogleSafeBrowsingConnector:

    def _get_connector(self):
        from connectors.google_safe_browsing import GoogleSafeBrowsingConnector
        return GoogleSafeBrowsingConnector()

    def test_connector_disabled_no_api_key(self):
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", ""):
            with patch("connectors.google_safe_browsing.SAFE_BROWSING_ENABLED", True):
                c = self._get_connector()
                assert not c.enabled
                result = c.lookup("https://evil.com", "url")
                assert not result.matched
                assert "disabled" in result.summary.lower()

    def test_connector_disabled_by_flag(self):
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_ENABLED", False):
            with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
                c = self._get_connector()
                assert not c.enabled

    def test_supported_indicators(self):
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            assert "url" in c.supported_indicators()
            assert "domain" in c.supported_indicators()

    @patch("urllib.request.urlopen")
    def test_lookup_safe_url(self, mock_urlopen):
        mock_urlopen.return_value = _make_mock_response({})
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("https://safe.example.com", "url")
            assert not result.matched
            assert result.risk == "UNKNOWN"
            assert result.confidence == 0.0
            assert result.source == "google_safe_browsing"
            assert result.error is None

    @patch("urllib.request.urlopen")
    def test_lookup_malicious_url(self, mock_urlopen):
        response_data = {
            "matches": [
                {
                    "threatType": "SOCIAL_ENGINEERING",
                    "platformType": "ANY_PLATFORM",
                    "threatEntryType": "URL",
                    "threat": {"url": "https://phishing.example.com"},
                    "cacheDuration": "300s",
                }
            ]
        }
        mock_urlopen.return_value = _make_mock_response(response_data)
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("https://phishing.example.com", "url")
            assert result.matched
            assert result.risk == "HIGH"
            assert result.confidence >= 0.8
            assert "SOCIAL_ENGINEERING" in result.summary
            assert len(result.evidence) >= 1
            assert result.evidence[0]["threat_type"] == "SOCIAL_ENGINEERING"

    @patch("urllib.request.urlopen")
    def test_lookup_malware_url(self, mock_urlopen):
        response_data = {
            "matches": [
                {
                    "threatType": "MALWARE",
                    "platformType": "ANY_PLATFORM",
                    "threatEntryType": "URL",
                    "threat": {"url": "https://malware.example.com"},
                    "cacheDuration": "300s",
                }
            ]
        }
        mock_urlopen.return_value = _make_mock_response(response_data)
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("https://malware.example.com", "url")
            assert result.matched
            assert result.risk == "HIGH"
            assert result.confidence >= 0.85

    @patch("urllib.request.urlopen")
    def test_lookup_multiple_threat_types(self, mock_urlopen):
        response_data = {
            "matches": [
                {
                    "threatType": "MALWARE",
                    "platformType": "ANY_PLATFORM",
                    "threatEntryType": "URL",
                    "threat": {"url": "https://bad.example.com"},
                },
                {
                    "threatType": "SOCIAL_ENGINEERING",
                    "platformType": "ANY_PLATFORM",
                    "threatEntryType": "URL",
                    "threat": {"url": "https://bad.example.com"},
                },
            ]
        }
        mock_urlopen.return_value = _make_mock_response(response_data)
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("https://bad.example.com", "url")
            assert result.matched
            assert result.risk == "HIGH"
            assert len(result.evidence) == 2

    @patch("urllib.request.urlopen")
    def test_lookup_domain(self, mock_urlopen):
        response_data = {
            "matches": [
                {
                    "threatType": "SOCIAL_ENGINEERING",
                    "platformType": "ANY_PLATFORM",
                    "threatEntryType": "URL",
                    "threat": {"url": "http://evil-phishing.com"},
                }
            ]
        }
        mock_urlopen.return_value = _make_mock_response(response_data)
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("evil-phishing.com", "domain")
            assert result.matched

    @patch("urllib.request.urlopen")
    def test_api_timeout(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = URLError("timed out")
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("https://example.com", "url")
            assert not result.matched
            assert result.error is not None
            assert "timed out" in result.error.lower()

    @patch("urllib.request.urlopen")
    def test_invalid_api_key(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(403)
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "invalid_key"):
            c = self._get_connector()
            result = c.lookup("https://example.com", "url")
            assert not result.matched
            assert result.error is not None
            assert "403" in result.error

    @patch("urllib.request.urlopen")
    def test_http_500_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(500)
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("https://example.com", "url")
            assert not result.matched
            assert result.error is not None

    @patch("urllib.request.urlopen")
    def test_empty_response(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = b""
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("https://example.com", "url")
            assert not result.matched

    @patch("urllib.request.urlopen")
    def test_malformed_json_response(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = b"not json"
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("https://example.com", "url")
            assert not result.matched

    @patch("urllib.request.urlopen")
    def test_retry_on_429(self, mock_urlopen):
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise _make_http_error(429)
            return _make_mock_response({})
        mock_urlopen.side_effect = side_effect
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("https://example.com", "url")
            assert call_count[0] == 3
            assert not result.matched

    @patch("urllib.request.urlopen")
    def test_retry_on_urlerror(self, mock_urlopen):
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise URLError("temporary failure")
            return _make_mock_response({})
        mock_urlopen.side_effect = side_effect
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("https://example.com", "url")
            assert call_count[0] == 3
            assert not result.matched

    def test_health_disabled(self):
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", ""):
            c = self._get_connector()
            health = c.health()
            assert health["status"] == "disabled"

    @patch("urllib.request.urlopen")
    def test_health_ok(self, mock_urlopen):
        mock_urlopen.return_value = _make_mock_response({})
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            health = c.health()
            assert health["status"] == "ok"

    @patch("urllib.request.urlopen")
    def test_health_unhealthy(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("connection failed")
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            health = c.health()
            assert health["status"] == "unhealthy"

    def test_metadata(self):
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            meta = c.metadata()
            assert meta["name"] == "google_safe_browsing"
            assert meta["enabled"] is True
            assert "url" in meta["supported_indicators"]

    @patch("urllib.request.urlopen")
    def test_lookup_batch(self, mock_urlopen):
        response_data = {
            "matches": [
                {
                    "threatType": "MALWARE",
                    "platformType": "ANY_PLATFORM",
                    "threatEntryType": "URL",
                    "threat": {"url": "http://evil1.com"},
                },
            ]
        }
        mock_urlopen.return_value = _make_mock_response(response_data)
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            results = c.lookup_batch(["evil1.com", "safe.com"], "domain")
            assert len(results) == 2
            matched = [r for r in results if r.matched]
            assert len(matched) == 1

    @patch("urllib.request.urlopen")
    def test_lookup_batch_disabled(self, mock_urlopen):
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", ""):
            c = self._get_connector()
            results = c.lookup_batch(["evil.com"], "url")
            assert results == []

    @patch("urllib.request.urlopen")
    def test_rate_limit_exhaustion(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(429)
        with patch("connectors.google_safe_browsing.SAFE_BROWSING_API_KEY", "test_key"):
            c = self._get_connector()
            result = c.lookup("https://example.com", "url")
            assert not result.matched
            assert result.error is not None

    def test_discovery(self):
        ConnectorRegistry.clear()
        discovered = ConnectorRegistry.discover("connectors")
        assert "google_safe_browsing" in discovered

    def test_normalize_url(self):
        from connectors.google_safe_browsing import _normalise_url
        assert _normalise_url("ExAmPlE.Com/Path") == "http://example.com/path"
        assert _normalise_url("https://Example.com") == "https://example.com"

    def test_normalize_url_no_scheme(self):
        from connectors.google_safe_browsing import _normalise_url
        result = _normalise_url("evil.com")
        assert result == "http://evil.com"

    def test_domain_from_url(self):
        from connectors.google_safe_browsing import _domain_from_url
        assert _domain_from_url("https://sub.example.com/path?a=1") == "sub.example.com"
        assert _domain_from_url("example.com") == "example.com"

    def test_risk_rank(self):
        from connectors.google_safe_browsing import _risk_rank
        assert _risk_rank("HIGH") > _risk_rank("MEDIUM")
        assert _risk_rank("UNKNOWN") == 1

    def test_build_request_body(self):
        from connectors.google_safe_browsing import _build_request_body
        body = _build_request_body(["https://test.com"])
        assert b"test.com" in body
        assert b"scamshield" in body

    def test_confidence_map_coverage(self):
        from connectors.google_safe_browsing import _CONFIDENCE_MAP, _THREAT_TYPES
        for t in _THREAT_TYPES:
            if t == "THREAT_TYPE_UNSPECIFIED":
                continue
            assert t in _CONFIDENCE_MAP, f"Missing confidence mapping for {t}"

    def test_risk_map_coverage(self):
        from connectors.google_safe_browsing import _RISK_MAP, _THREAT_TYPES
        for t in _THREAT_TYPES:
            if t == "THREAT_TYPE_UNSPECIFIED":
                continue
            assert t in _RISK_MAP, f"Missing risk mapping for {t}"
