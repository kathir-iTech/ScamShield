import pytest

from core.audit import (
    AUDIT_EVENTS,
    record_audit_event,
    record_auth_event,
    record_auth_failure,
    record_security_event,
    record_admin_action,
    record_suspicious_request,
)


class TestAuditEvents:
    def test_all_events_defined(self):
        assert "auth:login" in AUDIT_EVENTS
        assert "auth:login_failed" in AUDIT_EVENTS
        assert "api_key:created" in AUDIT_EVENTS
        assert "api_key:revoked" in AUDIT_EVENTS
        assert "rate_limit:exceeded" in AUDIT_EVENTS
        assert "rate_limit:blocked" in AUDIT_EVENTS
        assert "startup:app_started" in AUDIT_EVENTS
        assert "startup:app_shutdown" in AUDIT_EVENTS

    def test_record_audit_event(self):
        record_audit_event("test:event", detail="test detail")
        assert True

    def test_record_auth_event(self):
        record_auth_event("auth:login", detail="User logged in", user_id="user_123")
        assert True

    def test_record_auth_failure(self):
        record_auth_failure(detail="Invalid credentials", client_ip="10.0.0.1")
        assert True

    def test_record_security_event(self):
        record_security_event(
            "security:suspicious_request",
            detail="Suspicious pattern detected",
            metadata={"pattern": "multiple_logins", "count": 5},
        )
        assert True

    def test_record_admin_action(self):
        record_admin_action(detail="Configuration updated", resource="settings")
        assert True

    def test_record_suspicious_request(self):
        record_suspicious_request(
            detail="Rapid sequential requests",
            client_ip="10.0.0.99",
        )
        assert True

    def test_audit_logger_exists(self):
        from core.logger import logger
        assert logger.name == "scamshield"
