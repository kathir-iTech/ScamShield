import pytest
from fastapi.testclient import TestClient


class TestSecurityPosture:
    def test_security_headers_present(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert resp.headers.get("Cache-Control") == "no-store"

    def test_cors_headers(self, client):
        resp = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        assert "access-control-allow-origin" in {k.lower(): v for k, v in resp.headers.items()}

    def test_rate_limit_headers_on_normal_request(self, client):
        resp = client.get("/health")
        headers = {k.lower(): v for k, v in resp.headers.items()}
        assert "x-ratelimit-limit" in headers
        assert "x-ratelimit-remaining" in headers
        assert "x-ratelimit-reset" in headers


class TestInputValidation:
    def test_empty_text_rejected(self, client):
        resp = client.post("/analyze/text", json={"text": ""})
        assert resp.status_code == 422

    def test_missing_text_field_rejected(self, client):
        resp = client.post("/analyze/text", json={})
        assert resp.status_code == 422

    def test_extra_large_payload_rejected(self, client):
        resp = client.post("/analyze/text", json={"text": "x" * 100001})
        assert resp.status_code == 422

    def test_invalid_json_body_rejected(self, client):
        resp = client.post("/analyze/text", data="not json", headers={"Content-Type": "application/json"})
        assert resp.status_code in (400, 422)

    def test_method_not_allowed(self, client):
        resp = client.put("/analyze/text", json={"text": "test"})
        assert resp.status_code == 405

    def test_unknown_endpoint_returns_404(self, client):
        resp = client.get("/nonexistent-endpoint")
        assert resp.status_code == 404


class TestErrorResponseFormat:
    def test_error_response_has_detail(self, client):
        resp = client.post("/analyze/text", json={"text": "x" * 100001})
        data = resp.json()
        assert "detail" in data

    def test_validation_error_structured(self, client):
        resp = client.post("/analyze/text", json={"text": ""})
        data = resp.json()
        assert "detail" in data


class TestGracefulDegradation:
    def test_health_endpoint_always_available(self, client):
        for _ in range(5):
            resp = client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "pass"

    def test_version_endpoint(self, client):
        resp = client.get("/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "service" in data
        assert "version" in data
        assert "environment" in data

    def test_error_does_not_expose_internals(self, client):
        resp = client.post("/analyze/text", json={"text": ""})
        data = resp.json()
        detail = str(data.get("detail", ""))
        assert "traceback" not in detail.lower()
        assert "file" not in detail.lower()
        assert "line" not in detail.lower()
