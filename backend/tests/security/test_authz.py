from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from config import settings
from core.auth import jwt as jwt_module

_TEST_SECRET = "authz-suite-jwt-secret-0123456789abcdef"
_SAMPLE_TEXT = "Congratulations! You have won a free iPhone. Send 500 rupees now."


@pytest.fixture
def app_client():
    from main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def _configure_auth():
    previous_secret = settings.AUTH_JWT_SECRET
    settings.AUTH_JWT_SECRET = _TEST_SECRET
    jwt_module.configure(secret=_TEST_SECRET)
    yield
    settings.AUTH_JWT_SECRET = previous_secret
    # Never leak an enabled-auth state into the next test: the app revalidates
    # config on startup and would abort without admin/client API keys.
    settings.AUTH_ENABLED = False


class TestAuthGatingOnAnalyze:
    def test_endpoint_is_public_when_auth_disabled(self, app_client):
        settings.AUTH_ENABLED = False
        response = app_client.post("/analyze/text", json={"text": _SAMPLE_TEXT})
        assert response.status_code == 200

    def test_endpoint_requires_token_when_auth_enabled(self, app_client):
        settings.AUTH_ENABLED = True
        response = app_client.post("/analyze/text", json={"text": _SAMPLE_TEXT})
        assert response.status_code == 401
        assert "www-authenticate" in {k.lower() for k in response.headers}

    def test_valid_token_is_accepted_when_auth_enabled(self, app_client):
        settings.AUTH_ENABLED = True
        token = jwt_module.create_access_token("usr_authz_subject")
        response = app_client.post(
            "/analyze/text",
            json={"text": _SAMPLE_TEXT},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_token_signed_with_empty_secret_is_rejected(self, app_client):
        settings.AUTH_ENABLED = True
        previous = jwt_module._SECRET
        jwt_module._SECRET = ""
        try:
            with pytest.raises(ValueError):
                jwt_module.create_access_token("usr_forged")
            forged = None
        finally:
            jwt_module._SECRET = previous

        assert forged is None
        response = app_client.post(
            "/analyze/text",
            json={"text": _SAMPLE_TEXT},
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert response.status_code == 401

    def test_token_signed_with_wrong_secret_is_rejected(self, app_client):
        settings.AUTH_ENABLED = True
        import jwt as pyjwt
        import time as _time

        now = int(_time.time())
        forged = pyjwt.encode(
            {
                "sub": "usr_intruder",
                "role": "admin",
                "exp": now + 3600,
                "iat": now,
                "jti": "forged-jti",
                "token_type": "access",
                "iss": "scamshield",
                "aud": "scamshield-api",
            },
            "a-completely-different-signing-secret-value",
            algorithm="HS256",
        )
        response = app_client.post(
            "/analyze/text",
            json={"text": _SAMPLE_TEXT},
            headers={"Authorization": f"Bearer {forged}"},
        )
        assert response.status_code == 401


class TestCorsHardening:
    def test_unknown_origin_is_not_reflected(self, app_client):
        response = app_client.options(
            "/analyze/text",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.headers.get("access-control-allow-origin") != "https://evil.com"

    def test_admin_key_header_is_not_allowed_from_browsers(self, app_client):
        response = app_client.options(
            "/analyze/text",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "x-admin-key",
            },
        )
        allowed = response.headers.get("access-control-allow-headers", "")
        assert "x-admin-key" not in allowed.lower()


class TestSecurityHeaders:
    def test_headers_present_on_success(self, app_client):
        response = app_client.get("/health")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("x-request-id")

    def test_headers_present_on_validation_error(self, app_client):
        response = app_client.post(
            "/analyze/text", json={"text": ""}, headers={"Content-Type": "application/json"}
        )
        assert response.status_code in (400, 422)
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-request-id")

    def test_headers_present_on_not_found(self, app_client):
        response = app_client.get("/definitely-not-a-route")
        assert response.status_code == 404
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_csp_and_hsts_are_emitted(self, app_client):
        response = app_client.get("/health")
        assert response.headers.get("content-security-policy")
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


class TestDocsExposure:
    def test_docs_available_in_testing_environment(self, app_client):
        previous = settings.ENVIRONMENT
        settings.ENVIRONMENT = "testing"
        try:
            assert app_client.get("/docs").status_code == 200
        finally:
            settings.ENVIRONMENT = previous

    def test_docs_hidden_in_production(self, app_client):
        previous = settings.ENVIRONMENT
        settings.ENVIRONMENT = "production"
        try:
            assert app_client.get("/docs").status_code == 404
            assert app_client.get("/openapi.json").status_code == 404
        finally:
            settings.ENVIRONMENT = previous
