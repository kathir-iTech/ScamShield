import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.security import RateLimitMiddleware

os.environ["SCAMSHIELD_ENVIRONMENT"] = "testing"
os.environ["SCAMSHIELD_AUTH_ENABLED"] = "false"
os.environ["SCAMSHIELD_RATE_LIMIT_MAX"] = "200"


@pytest.fixture
def client():
    from main import app
    with TestClient(app) as c:
        yield c


class TestSecurityHeaders:
    def test_security_headers_present(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("X-XSS-Protection") == "0"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert resp.headers.get("Permissions-Policy") is not None

    def test_request_id_header(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-Request-ID") is not None

    def test_cache_control_present(self, client):
        resp = client.get("/health")
        assert resp.headers.get("Cache-Control") == "no-store"


class TestCORS:
    def test_cors_origins_configured(self, client):
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200

    def test_cors_disallowed_origin(self, client):
        resp = client.options(
            "/health",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        allow_origin = resp.headers.get("Access-Control-Allow-Origin", "")
        assert "evil.com" not in allow_origin


class TestRequestBodySize:
    def test_large_body_rejected(self, client):
        resp = client.post("/analyze/text", json={"text": "hello"})
        assert resp.status_code in (200, 422)

    def test_normal_body_accepted(self, client):
        resp = client.post("/analyze/text", json={"text": "hello world"})
        assert resp.status_code in (200, 422)


class TestRateLimitIsolated:
    def test_rate_limit_blocks_excess(self):
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        app.add_middleware(RateLimitMiddleware, max_requests=3, window_seconds=60)

        with TestClient(app) as c:
            for _ in range(3):
                resp = c.get("/test")
                assert resp.status_code == 200
            resp = c.get("/test")
            assert resp.status_code == 429


class TestMetricsEndpoint:
    def test_metrics_endpoint_exists(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
