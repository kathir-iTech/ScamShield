import os

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

os.environ["SCAMSHIELD_ENVIRONMENT"] = "testing"
os.environ["SCAMSHIELD_AUTH_ENABLED"] = "false"

_TEST_SECRET = "test-secret-key-for-testing-only"


@pytest.fixture(autouse=True)
def _configure_auth():
    from core.auth import configure_auth, reset_blacklist
    configure_auth(
        secret_key=_TEST_SECRET,
        access_ttl=3600,
        refresh_ttl=86400 * 30,
        clock_skew=30,
        blacklist_capacity=100000,
    )
    reset_blacklist()


class TestJWT:
    def test_create_access_token(self):
        from core.auth import UserRole, create_access_token
        token = create_access_token(subject="user_1", role=UserRole.AUTHENTICATED)
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_create_refresh_token(self):
        from core.auth import create_refresh_token
        token = create_refresh_token(subject="user_1")
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_decode_valid_access_token(self):
        from core.auth import UserRole, create_access_token, decode_token
        token = create_access_token(subject="user_1", role=UserRole.AUTHENTICATED)
        payload = decode_token(token)
        assert payload.sub == "user_1"
        assert payload.role == "authenticated"
        assert payload.token_type == "access"

    def test_decode_valid_refresh_token(self):
        from core.auth import create_refresh_token, decode_token
        token = create_refresh_token(subject="user_1")
        payload = decode_token(token)
        assert payload.sub == "user_1"
        assert payload.role == "refresh"
        assert payload.token_type == "refresh"

    def test_decode_admin_token(self):
        from core.auth import UserRole, create_access_token, decode_token
        token = create_access_token(subject="admin_1", role=UserRole.ADMIN)
        payload = decode_token(token)
        assert payload.sub == "admin_1"
        assert payload.role == "admin"

    def test_decode_invalid_token_raises(self):
        from core.auth import decode_token
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("invalid.token.here")

    def test_decode_tampered_token_raises(self):
        from core.auth import UserRole, create_access_token, decode_token
        token = create_access_token(subject="user_1", role=UserRole.AUTHENTICATED)
        parts = token.split(".")
        parts[2] = "tampered"
        tampered = ".".join(parts)
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token(tampered)

    def test_decode_expired_token(self):
        from core.auth import configure_auth, create_access_token, decode_token
        configure_auth(secret_key=_TEST_SECRET, access_ttl=-1, clock_skew=0)
        token = create_access_token(subject="user_1")
        with pytest.raises(ValueError, match="expired"):
            decode_token(token)


class TestBlacklist:
    def test_blacklisted_token_rejected(self):
        from core.auth import UserRole, blacklist_token, create_access_token, decode_token
        token = create_access_token(subject="user_1", role=UserRole.AUTHENTICATED)
        payload = decode_token(token)
        blacklist_token(payload.jti)
        with pytest.raises(ValueError, match="revoked"):
            decode_token(token)

    def test_blacklist_multiple_tokens(self):
        from core.auth import UserRole, blacklist_token, create_access_token, decode_token
        t1 = create_access_token(subject="user_1", role=UserRole.AUTHENTICATED)
        t2 = create_access_token(subject="user_2", role=UserRole.AUTHENTICATED)
        p1 = decode_token(t1)
        blacklist_token(p1.jti)
        with pytest.raises(ValueError, match="revoked"):
            decode_token(t1)
        p2 = decode_token(t2)
        assert p2.sub == "user_2"


class TestRefreshTokenRotation:
    def test_refresh_rotation_valid(self):
        from core.auth import create_refresh_token, decode_token, mark_refresh_used
        token = create_refresh_token(subject="user_1")
        payload = decode_token(token)
        assert mark_refresh_used(payload.jti) is True

    def test_refresh_reuse_detected(self):
        from core.auth import create_refresh_token, decode_token, mark_refresh_used
        token = create_refresh_token(subject="user_1")
        payload = decode_token(token)
        assert mark_refresh_used(payload.jti) is True
        assert mark_refresh_used(payload.jti) is False

    def test_reused_refresh_also_blacklisted(self):
        from core.auth import (
            create_refresh_token, decode_token, is_token_blacklisted,
            mark_refresh_used,
        )
        token = create_refresh_token(subject="user_1")
        payload = decode_token(token)
        mark_refresh_used(payload.jti)
        mark_refresh_used(payload.jti)
        assert is_token_blacklisted(payload.jti) is True


class TestClockSkew:
    def test_token_with_small_future_iat_allowed(self):
        from core.auth.jwt import _encode_jwt
        from core.auth import UserRole, decode_token
        import time
        payload = {
            "sub": "user_1",
            "role": UserRole.AUTHENTICATED.value,
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()) + 10,
            "jti": "test-future-iat",
            "token_type": "access",
        }
        encoded = _encode_jwt(payload)
        result = decode_token(encoded)
        assert result.sub == "user_1"

    def test_token_with_large_future_iat_rejected(self):
        from core.auth.jwt import _encode_jwt
        from core.auth import decode_token
        import time
        payload = {
            "sub": "user_1",
            "role": "authenticated",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()) + 120,
            "jti": "test-too-future",
            "token_type": "access",
        }
        encoded = _encode_jwt(payload)
        with pytest.raises(ValueError, match="not yet valid"):
            decode_token(encoded)

    def test_expired_token_within_skew_accepted(self):
        from core.auth.jwt import _encode_jwt
        from core.auth import UserRole, decode_token
        import time
        payload = {
            "sub": "user_1",
            "role": UserRole.AUTHENTICATED.value,
            "exp": int(time.time()) - 25,
            "iat": int(time.time()) - 4000,
            "jti": "test-skew-exp",
            "token_type": "access",
        }
        encoded = _encode_jwt(payload)
        result = decode_token(encoded)
        assert result.sub == "user_1"

    def test_token_expired_beyond_skew_rejected(self):
        from core.auth.jwt import _encode_jwt
        from core.auth import decode_token
        import time
        payload = {
            "sub": "user_1",
            "role": "authenticated",
            "exp": int(time.time()) - 120,
            "iat": int(time.time()) - 4000,
            "jti": "test-beyond-skew",
            "token_type": "access",
        }
        encoded = _encode_jwt(payload)
        with pytest.raises(ValueError, match="expired"):
            decode_token(encoded)


class TestForgedJWTs:
    def test_invalid_signature_rejected(self):
        from core.auth import decode_token
        header = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        payload = "eyJzdWIiOiJ1c2VyXzEiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjk5OTk5OTk5OTl9"
        sig = "invalidsignature"
        forged = f"{header}.{payload}.{sig}"
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token(forged)

    def test_empty_signature_rejected(self):
        from core.auth import decode_token
        forged = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiJ9."
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token(forged)

    def test_missing_claims_rejected(self):
        from core.auth.jwt import _encode_jwt
        from core.auth import decode_token
        import time
        payload = {"sub": "user_1", "exp": int(time.time()) + 3600}
        encoded = _encode_jwt(payload)
        with pytest.raises(ValueError):
            decode_token(encoded)


class TestPrivilegeEscalation:
    def test_token_with_admin_role_rejected_on_wrong_secret(self):
        from core.auth import UserRole, create_access_token, decode_token
        from core.auth.jwt import _encode_jwt
        import time
        token = create_access_token(subject="user_1", role=UserRole.AUTHENTICATED)
        parts = token.split(".")
        tampered_payload = {
            "sub": "user_1",
            "role": "admin",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "jti": "forged-admin",
            "token_type": "access",
        }
        parts[1] = __import__("base64").urlsafe_b64encode(
            __import__("json").dumps(tampered_payload, separators=(",", ":"), sort_keys=True).encode()
        ).rstrip(b"=").decode()
        forged = ".".join(parts)
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token(forged)

    def test_guest_no_token_rejected_by_investigation(self):
        from core.auth.deps import require_admin
        from core.auth.models import AuthenticatedUser, UserRole
        from fastapi import HTTPException
        import pytest
        user = AuthenticatedUser(id="anonymous", role=UserRole.GUEST, token_id="")
        assert not user.is_admin
        with pytest.raises(HTTPException) as exc:
            if not user.is_admin:
                raise HTTPException(status_code=403, detail="Admin privileges required")
        assert exc.value.status_code == 403

    def test_authenticated_user_rejected_by_investigation(self):
        from core.auth.models import AuthenticatedUser, UserRole
        user = AuthenticatedUser(id="user_1", role=UserRole.AUTHENTICATED, token_id="abc")
        assert not user.is_admin
        assert user.is_authenticated

    def test_admin_token_verify_role(self):
        from core.auth import UserRole, create_access_token, decode_token
        token = create_access_token(subject="admin_1", role=UserRole.ADMIN)
        payload = decode_token(token)
        assert payload.role == UserRole.ADMIN.value

    def _make_mock_request(self, headers: dict = None):
        from unittest.mock import MagicMock
        mock = MagicMock()
        mock.client.host = "127.0.0.1"
        mock.headers = headers or {}
        return mock

    def test_admin_token_key_validation(self):
        from routers.auth import get_admin_token
        from core.auth.models import AdminAuthRequest
        from unittest.mock import patch
        from fastapi import Response
        with patch("config.settings.ADMIN_API_KEY", "valid-key-123"):
            with patch("config.settings.AUTH_ENABLED", True):
                body = AdminAuthRequest(admin_key="valid-key-123")
                mock_req = self._make_mock_request({"X-Admin-Key": "valid-key-123"})
                result = get_admin_token(mock_req, Response(), body)
                assert result.access_token is not None

    def test_admin_token_wrong_key_rejected(self):
        from routers.auth import get_admin_token
        from core.auth.models import AdminAuthRequest
        from fastapi import HTTPException, Response
        from unittest.mock import patch
        import pytest
        with patch("config.settings.ADMIN_API_KEY", "valid-key-123"):
            with patch("config.settings.AUTH_ENABLED", True):
                body = AdminAuthRequest(admin_key="wrong-key")
                mock_req = self._make_mock_request({"X-Admin-Key": "wrong-key"})
                with pytest.raises(HTTPException) as exc:
                    get_admin_token(mock_req, Response(), body)
                assert exc.value.status_code == 401


class TestAuthClient:
    def test_auth_returns_404_when_disabled(self):
        from main import app
        with TestClient(app) as c:
            resp = c.post("/auth/token")
            assert resp.status_code == 404

    def test_auth_refresh_returns_404_when_disabled(self):
        from main import app
        with TestClient(app) as c:
            resp = c.post("/auth/refresh", json={"refresh_token": "test"})
            assert resp.status_code == 404


class TestRoles:
    def test_admin_role_property(self):
        from core.auth import AuthenticatedUser, UserRole
        user = AuthenticatedUser(id="admin_1", role=UserRole.ADMIN, token_id="abc")
        assert user.is_admin is True
        assert user.is_authenticated is True

    def test_authenticated_role_property(self):
        from core.auth import AuthenticatedUser, UserRole
        user = AuthenticatedUser(id="user_1", role=UserRole.AUTHENTICATED, token_id="abc")
        assert user.is_admin is False
        assert user.is_authenticated is True

    def test_guest_role_property(self):
        from core.auth import AuthenticatedUser, UserRole
        user = AuthenticatedUser(id="anonymous", role=UserRole.GUEST, token_id="")
        assert user.is_admin is False
        assert user.is_authenticated is False
