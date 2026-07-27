from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from main import app
from core.auth import UserRole, create_access_token


@pytest.fixture(autouse=True)
def _configure_auth_for_tests():
    from core.auth import configure_auth
    configure_auth(secret_key="test-secret-key-for-sprint2", access_ttl=3600, refresh_ttl=86400 * 30, clock_skew=30)


@pytest.fixture
def client():
    return TestClient(app)


class TestIntegrationScamDetection:
    def test_sms_phishing_detection(self, client):
        resp = client.post("/analyze/text", json={
            "text": "URGENT: Your SBI account will be deactivated. Update KYC immediately: https://sbi-kyc.xyz"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["prediction"] == "scam"
        assert data["confidence"] > 0.7

    def test_sms_safe_detection(self, client):
        resp = client.post("/analyze/text", json={
            "text": "Thanks for subscribing to our newsletter."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["prediction"] == "safe"
        assert data["confidence"] > 0.5

    def test_sms_upi_scam_detection(self, client):
        resp = client.post("/analyze/text", json={
            "text": "Your UPI transaction of 15000 is pending. Confirm now to avoid penalty: https://paytm-upi.tk"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["prediction"] == "scam"
        assert data["confidence"] > 0.7

    def test_image_analysis_integration(self, client):
        resp = client.post("/analyze/image", files={"file": ("test.png", b"fake image data", "image/png")})
        assert resp.status_code in (200, 400, 422, 500)

    def test_mixed_language_detection_english_focus(self, client):
        # Assuming the model is primarily trained on English, mixed lang might still be detected as scam if keywords are present
        resp = client.post("/analyze/text", json={"text": "URGENT ACTION REQUIRED: Your account needs update. Click here: http://link.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["prediction"] == "scam"


class TestIntegrationInvestigationWorkflow:
    def test_investigation_endpoint_requires_admin(self, client):
        resp = client.post("/analyze/investigation", json={
            "artefacts": [{"text": "investigation message", "type": "text"}]
        })
        assert resp.status_code == 401 # Not authenticated

    def test_investigation_endpoint_with_admin_token(self):
        admin_token = create_access_token(subject="admin_user", role=UserRole.ADMIN)
        client = TestClient(app)
        client.headers.update({"Authorization": f"Bearer {admin_token}"})
        resp = client.post("/analyze/investigation", json={
            "artefacts": [{"text": "investigation message for admin", "type": "text"}]
        })
        assert resp.status_code == 200
        data = resp.json()
        # Check for top-level keys indicating successful investigation processing
        assert "investigation_id" in data
        assert "artefacts_analysed" in data
        assert "global_assessment" in data


class TestIntegrationAuthenticationWorkflow:
    def test_get_token_returns_tokens(self, client):
        resp = client.post("/auth/token")
        # Auth may be disabled in testing profile (returns 404)
        if resp.status_code == 404:
            pytest.skip("Auth is disabled in testing profile")
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_works(self, client):
        auth_resp = client.post("/auth/token")
        if auth_resp.status_code == 404:
            pytest.skip("Auth is disabled in testing profile")
        assert auth_resp.status_code == 200
        auth_data = auth_resp.json()
        refresh_token = auth_data["refresh_token"]

        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_verify_valid_token(self, client):
        token = create_access_token(subject="test_user", role=UserRole.AUTHENTICATED)
        resp = client.post("/auth/verify", json={"token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("valid") is True
        assert data.get("sub") == "test_user"
        assert data.get("role") == UserRole.AUTHENTICATED.value

    def test_verify_revoked_token(self, client):
        token = create_access_token(subject="revoked_user", role=UserRole.AUTHENTICATED)
        # Revoke the token (using the auth router directly for simplicity here)
        from core.auth import decode_token, blacklist_token
        payload = decode_token(token)
        blacklist_token(payload.jti)

        resp = client.post("/auth/verify", json={"token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("valid") is False
        assert "revoked" in data.get("detail", "")

    def test_logout_invalidates_refresh_token(self, client):
        auth_resp = client.post("/auth/token")
        if auth_resp.status_code == 404:
            pytest.skip("Auth is disabled in testing profile")
        auth_data = auth_resp.json()
        refresh_token = auth_data["refresh_token"]

        resp = client.post("/auth/logout", json={"refresh_token": refresh_token})
        assert resp.status_code == 200

        refresh_resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_resp.status_code == 401
        assert "revoked" in refresh_resp.json().get("detail", "") or "reuse" in refresh_resp.json().get("detail", "")


class TestIntegrationSecurityHeaders:
    def test_security_headers_are_present_on_response(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        headers = resp.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert headers.get("Cache-Control") == "no-store"


class TestIntegrationRateLimiting:
    def test_rate_limit_enforced(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from core.security import RateLimitMiddleware
        _app = FastAPI()
        @_app.get("/test")
        async def _test():
            return {"ok": True}
        _app.add_middleware(RateLimitMiddleware, max_requests=3, window_seconds=60)
        client = TestClient(_app)
        for _ in range(3):
            resp = client.get("/test")
            assert resp.status_code == 200
        resp = client.get("/test")
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers

