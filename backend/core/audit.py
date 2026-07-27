from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from core.context import get_correlation_id, get_request_id, get_user_id
from core.logger import logger


AUDIT_EVENTS = {
    "auth:login": "User login / token issued",
    "auth:login_failed": "Failed login attempt",
    "auth:token_refresh": "Token refreshed",
    "auth:token_verify": "Token verified",
    "auth:admin_token_issued": "Admin token issued",
    "api_key:created": "API key created",
    "api_key:revoked": "API key revoked",
    "api_key:rotated": "API key rotated",
    "api_key:used": "API key used",
    "api_key:expired_used": "Expired API key attempted",
    "api_key:revoked_used": "Revoked API key attempted",
    "rate_limit:exceeded": "Rate limit exceeded",
    "rate_limit:blocked": "IP temporarily blocked",
    "admin:metrics_viewed": "Metrics viewed by admin",
    "security:config_change": "Configuration change detected",
    "security:suspicious_request": "Suspicious request pattern detected",
    "pipeline:stage_failure": "Pipeline stage failure",
    "startup:app_started": "Application started",
    "startup:app_shutdown": "Application shut down",
    "startup:config_error": "Configuration error at startup",
}


@dataclass
class AuditEvent:
    event: str
    timestamp: float
    level: str = "INFO"
    request_id: str = ""
    correlation_id: str = ""
    user_id: str = ""
    client_ip: str = ""
    resource: str = ""
    detail: str = ""
    metadata: Dict = field(default_factory=dict)


def _get_context() -> Dict:
    return {
        "request_id": get_request_id(),
        "correlation_id": get_correlation_id(),
        "user_id": get_user_id(),
    }


def _log_audit(event: AuditEvent) -> None:
    ctx = _get_context()
    log_data = {
        "audit_event": event.event,
        "timestamp": event.timestamp,
        "request_id": event.request_id or ctx["request_id"],
        "correlation_id": event.correlation_id or ctx["correlation_id"],
    }
    if event.user_id or ctx["user_id"]:
        log_data["user_id"] = event.user_id or ctx["user_id"]
    if event.client_ip:
        log_data["client_ip"] = event.client_ip
    if event.resource:
        log_data["resource"] = event.resource
    if event.detail:
        log_data["detail"] = event.detail
    if event.metadata:
        log_data["metadata"] = event.metadata

    level_map = {"INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
    level_num = level_map.get(event.level.upper(), 20)

    logger.log(
        level_num,
        "AUDIT: %s — %s",
        event.event,
        event.detail or "",
        extra={"structured": log_data},
    )


def record_audit_event(
    event: str,
    level: str = "INFO",
    detail: str = "",
    resource: str = "",
    client_ip: str = "",
    metadata: Optional[Dict] = None,
) -> None:
    audit_event = AuditEvent(
        event=event,
        timestamp=time.time(),
        level=level,
        detail=detail,
        resource=resource,
        client_ip=client_ip,
        metadata=metadata or {},
    )
    _log_audit(audit_event)


def record_auth_event(event: str, detail: str = "", user_id: str = "") -> None:
    record_audit_event(event=event, level="INFO", detail=detail)


def record_auth_failure(detail: str = "", client_ip: str = "") -> None:
    record_audit_event(
        event="auth:login_failed",
        level="WARNING",
        detail=detail,
        client_ip=client_ip,
    )


def record_security_event(
    event: str, detail: str = "", level: str = "WARNING", metadata: Optional[Dict] = None
) -> None:
    record_audit_event(event=event, level=level, detail=detail, metadata=metadata)


def record_admin_action(detail: str = "", resource: str = "") -> None:
    record_audit_event(
        event="security:config_change",
        level="INFO",
        detail=detail,
        resource=resource,
    )


def record_suspicious_request(detail: str = "", client_ip: str = "") -> None:
    record_audit_event(
        event="security:suspicious_request",
        level="WARNING",
        detail=detail,
        client_ip=client_ip,
    )
