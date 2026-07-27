import os

import pytest
from fastapi.testclient import TestClient

os.environ["SCAMSHIELD_ENVIRONMENT"] = "testing"
os.environ["SCAMSHIELD_AUTH_ENABLED"] = "false"
os.environ["SCAMSHIELD_RATE_LIMIT_MAX"] = "200"


@pytest.fixture
def client():
    from main import app
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health_returns_status(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "environment" in data
        assert "checks" in data
        assert "dependencies" in data

    def test_health_checks_list(self, client):
        resp = client.get("/health")
        data = resp.json()
        checks = data.get("checks", [])
        assert isinstance(checks, list)
        assert len(checks) > 0
        for check in checks:
            assert "name" in check
            assert "status" in check

    def test_health_dependencies(self, client):
        resp = client.get("/health")
        data = resp.json()
        deps = data.get("dependencies", {})
        assert "model" in deps
        assert "vectorizer" in deps
        assert "config" in deps


class TestReadyEndpoint:
    def test_ready_returns_status(self, client):
        resp = client.get("/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data


class TestLiveEndpoint:
    def test_live_returns_alive(self, client):
        resp = client.get("/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "alive"}


class TestVersionEndpoint:
    def test_version_returns_info(self, client):
        resp = client.get("/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "service" in data
        assert "version" in data
        assert "environment" in data


class TestMetricsEndpoint:
    def test_metrics_snapshot_structure(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "successful_requests" in data
        assert "failed_requests" in data
        assert "active_requests" in data
        assert "auth_failures" in data
        assert "rate_limit_events" in data
        assert "pipeline_failures" in data
        assert "average_latency_ms" in data
        assert "p50_latency_ms" in data
        assert "p95_latency_ms" in data
        assert "uptime_seconds" in data

    def test_metrics_records_requests(self, client):
        resp = client.get("/metrics")
        data = resp.json()
        assert isinstance(data["total_requests"], int)
        assert isinstance(data["auth_failures"], int)
        assert isinstance(data["rate_limit_events"], int)
        assert isinstance(data["pipeline_failures"], int)


class TestCorrelationID:
    def test_correlation_id_in_response(self, client):
        resp = client.get("/health", headers={"X-Correlation-ID": "my-correlation-id"})
        assert resp.headers.get("X-Correlation-ID") == "my-correlation-id"

    def test_correlation_id_fallback_to_request_id(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-Correlation-ID") is not None


class TestConfigProfiles:
    def test_profile_defaults(self):
        from core.config.profiles import get_profile, DEVELOPMENT, PRODUCTION
        dev = get_profile("development")
        assert dev.debug is True
        assert dev.auth_enabled is False
        prod = get_profile("production")
        assert prod.debug is False
        assert prod.auth_enabled is True
        assert prod.fail_fast is True
