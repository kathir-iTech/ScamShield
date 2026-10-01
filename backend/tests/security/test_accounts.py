from __future__ import annotations

import uuid

import pytest

from config import settings

_TEST_SECRET = "accounts-suite-jwt-secret-0123456789abcdef"
_STRONG_PASSWORD = "ScamShield99Pass"


def _unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture(autouse=True)
def _configure_auth():
    from core.auth import jwt as jwt_module

    previous_secret = settings.AUTH_JWT_SECRET
    settings.AUTH_JWT_SECRET = _TEST_SECRET
    jwt_module.configure(secret=_TEST_SECRET)
    yield
    settings.AUTH_JWT_SECRET = previous_secret
    # The suite contract (see conftest) is auth-disabled; never let a test
    # leave this flipped or every later app startup fails config validation.
    settings.AUTH_ENABLED = False


@pytest.fixture(autouse=True)
def _clean_state(storage):
    return storage


def _register(client, email: str, password: str = _STRONG_PASSWORD):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )


def _login(client, email: str, password: str = _STRONG_PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})


def _bearer(response) -> dict:
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


class TestRegistration:
    def test_register_returns_created_profile(self, client):
        email = _unique_email()
        response = _register(client, email)
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == email
        assert body["role"] == "authenticated"
        assert body["id"].startswith("usr_")

    def test_register_rejects_duplicate_email(self, client):
        email = _unique_email()
        assert _register(client, email).status_code == 201
        assert _register(client, email).status_code == 409

    @pytest.mark.parametrize(
        "password",
        [
            "short1",
            "alllettersonly",
            "1234567890",
            "Password1",  # too short
            "  Spaced9Pass  ",
        ],
    )
    def test_register_rejects_weak_password(self, client, password):
        response = _register(client, _unique_email(), password)
        assert response.status_code == 400

    def test_register_normalises_email_case(self, client):
        email = _unique_email().upper()
        assert _register(client, email).status_code == 201
        assert _register(client, email.lower()).status_code == 409


class TestLogin:
    def test_login_issues_token_pair(self, client):
        email = _unique_email()
        _register(client, email)
        response = _login(client, email)
        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"].count(".") == 2
        assert body["refresh_token"].count(".") == 2
        assert body["expires_in"] > 0

    def test_login_wrong_password_rejected(self, client):
        email = _unique_email()
        _register(client, email)
        response = _login(client, email, "WrongPassword99")
        assert response.status_code in (401, 403)
        assert "access_token" not in response.json()

    def test_login_unknown_account_rejected(self, client):
        response = _login(client, _unique_email())
        assert response.status_code in (401, 403)

    def test_login_locks_after_repeated_failures(self, client, storage):
        email = _unique_email()
        _register(client, email)
        for _ in range(settings.LOCKOUT_THRESHOLD):
            assert _login(client, email, "WrongPassword99").status_code in (401, 403)
        locked = _login(client, email, _STRONG_PASSWORD)
        assert locked.status_code in (401, 403, 429)
        assert storage.query_one(
            "SELECT locked_until FROM users WHERE email = ?", (email,)
        )["locked_until"]


class TestCurrentSession:
    def test_me_requires_token(self, client):
        assert client.get("/auth/me").status_code == 401

    def test_me_rejects_garbage_token(self, client):
        response = client.get("/auth/me", headers={"Authorization": "Bearer nonsense"})
        assert response.status_code == 401

    def test_me_returns_profile(self, client):
        email = _unique_email()
        _register(client, email)
        token = _bearer(_login(client, email))
        response = client.get("/auth/me", headers=token)
        assert response.status_code == 200
        assert response.json()["email"] == email

    def test_me_rejects_token_signed_with_empty_secret(self, client):
        from core.auth import jwt as jwt_module

        email = _unique_email()
        _register(client, email)
        previous = jwt_module._SECRET
        jwt_module._SECRET = ""
        try:
            with pytest.raises(ValueError):
                jwt_module.create_access_token("usr_victim")
            forged = None
        finally:
            jwt_module._SECRET = previous
        assert forged is None
        assert client.get("/auth/me", headers={"Authorization": "Bearer x"}).status_code == 401


class TestPasswordChange:
    def test_change_password_updates_credentials(self, client):
        email = _unique_email()
        _register(client, email)
        token = _bearer(_login(client, email))

        bad = client.post(
            "/auth/password/change",
            headers=token,
            json={"old_password": "NotTheOld1Pass", "new_password": "BrandNew9Pass"},
        )
        assert bad.status_code in (400, 401)
        assert "access_token" not in bad.json()

        good = client.post(
            "/auth/password/change",
            headers=token,
            json={"old_password": _STRONG_PASSWORD, "new_password": "BrandNew9Pass"},
        )
        assert good.status_code == 200

        assert _login(client, email, _STRONG_PASSWORD).status_code in (401, 403)
        assert _login(client, email, "BrandNew9Pass").status_code == 200

    def test_change_password_requires_auth(self, client):
        response = client.post(
            "/auth/password/change",
            json={"old_password": _STRONG_PASSWORD, "new_password": "BrandNew9Pass"},
        )
        assert response.status_code == 401


class TestLogoutEverywhere:
    def test_logout_all_revokes_refresh_tokens(self, client):
        settings.AUTH_ENABLED = True
        email = _unique_email()
        _register(client, email)
        login = _login(client, email).json()
        token = {"Authorization": f"Bearer {login['access_token']}"}

        response = client.post("/auth/logout/all", headers=token)
        assert response.status_code == 200
        assert response.json()["revoked"] >= 1

        refresh = client.post(
            "/auth/refresh", json={"refresh_token": login["refresh_token"]}
        )
        assert refresh.status_code == 401

    def test_logout_all_requires_auth(self, client):
        assert client.post("/auth/logout/all").status_code == 401


class TestRateLimitHeaders:
    def test_register_responses_carry_rate_limit_headers(self, client):
        response = _register(client, _unique_email())
        assert response.status_code == 201
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_repeated_registers_are_eventually_throttled(self, client, storage):
        storage.execute("DELETE FROM rate_limits")
        response = None
        for _ in range(settings.LOCKOUT_THRESHOLD + 12):
            response = _register(client, _unique_email())
            if response.status_code == 429:
                break
        assert response is not None
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert int(response.headers["X-RateLimit-Limit"]) == 10
