import os
import time

import pytest
from fastapi.testclient import TestClient

os.environ["SCAMSHIELD_ENVIRONMENT"] = "testing"
os.environ["SCAMSHIELD_AUTH_ENABLED"] = "false"


@pytest.fixture(scope="module")
def client():
    from main import app
    with TestClient(app) as c:
        yield c


class TestSecurityOverhead:
    def test_rate_limit_middleware_overhead(self, client):
        times = []
        for _ in range(10):
            start = time.perf_counter()
            resp = client.get("/health")
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            assert resp.status_code == 200
        avg = sum(times) / len(times)
        assert avg < 500

    def test_health_endpoint_latency(self, client):
        times = []
        for _ in range(10):
            start = time.perf_counter()
            resp = client.get("/health")
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            assert resp.status_code == 200
        avg = sum(times) / len(times)
        assert avg < 500

    def test_live_endpoint_latency(self, client):
        times = []
        for _ in range(10):
            start = time.perf_counter()
            resp = client.get("/live")
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            assert resp.status_code == 200
        avg = sum(times) / len(times)
        assert avg < 200

    def test_version_endpoint_latency(self, client):
        times = []
        for _ in range(10):
            start = time.perf_counter()
            resp = client.get("/version")
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            assert resp.status_code == 200
        avg = sum(times) / len(times)
        assert avg < 200

    def test_security_headers_overhead(self, client):
        start = time.perf_counter()
        resp = client.get("/health")
        elapsed = (time.perf_counter() - start) * 1000
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert elapsed < 500

    def test_metrics_endpoint_latency(self, client):
        start = time.perf_counter()
        resp = client.get("/metrics")
        elapsed = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        assert elapsed < 500

    def test_jwt_decode_overhead(self):
        from core.auth import configure_auth, create_access_token, decode_token
        configure_auth(secret_key="benchmark-secret-key")
        token = create_access_token(subject="benchmark_user")
        times = []
        for _ in range(100):
            start = time.perf_counter()
            decode_token(token)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        avg = sum(times) / len(times)
        assert avg < 5

    def test_security_middleware_stack_complete(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-Request-ID") is not None
        assert resp.headers.get("X-Correlation-ID") is not None
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
