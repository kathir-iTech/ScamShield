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

    def test_metrics_prometheus_format(self, client):
        resp = client.get("/metrics", headers={"Accept": "text/plain"})
        assert resp.status_code == 200
        text = resp.text
        assert "scamshield_requests_total" in text
        assert "scamshield_request_duration_seconds" in text
        assert "scamshield_active_requests" in text
        assert "scamshield_validation_failures_total" in text
        assert "scamshield_auth_failures_total" in text
        assert "scamshield_rate_limit_events_total" in text
        assert "scamshield_pipeline_failures_total" in text
        assert "scamshield_ocr_requests_total" in text
        assert "scamshield_text_requests_total" in text
        assert "scamshield_memory_usage_bytes" in text
        assert "scamshield_cpu_percent" in text
        assert "scamshield_process_memory_bytes" in text
        assert "scamshield_process_cpu_percent" in text
        assert "scamshield_process_threads" in text
        assert "scamshield_process_fds" in text
        assert "# TYPE" in text
        assert "# HELP" in text

    def test_metrics_prometheus_content_type(self, client):
        resp = client.get("/metrics", headers={"Accept": "text/plain"})
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("text/plain") or "openmetrics" in resp.headers.get("content-type", "")

    def test_metrics_json_still_works(self, client):
        resp = client.get("/metrics", headers={"Accept": "application/json"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data

    def test_record_prometheus_request_increments(self, client):
        from prometheus_client import REGISTRY
        def get_total():
            for metric in REGISTRY.collect():
                if metric.name == "scamshield_requests":
                    return sum(s.value for s in metric.samples if not s.name.endswith("_created"))
            return 0.0
        before = get_total()
        from core.prometheus_metrics import record_prometheus_request
        record_prometheus_request("GET", "/test", 200, 0.1)
        after = get_total()
        assert after == before + 1.0

    def test_system_metrics_non_negative(self):
        import core.prometheus_metrics as pm
        pm.init_prometheus_metrics()
        pm.update_prometheus_metrics()
        assert pm.scamshield_process_threads._value.get() >= 0
        assert pm.scamshield_process_fds._value.get() >= 0


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
