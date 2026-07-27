import os
import time
from typing import Dict, List

from fastapi import APIRouter

from core.constants import SERVICE_NAME, API_VERSION
from core.diagnostics import get_diagnostics
from core.metrics import metrics
from config import settings

router = APIRouter(tags=["Health"])

_startup_time: float = time.time()


def _read_version_file() -> str:
    try:
        version_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "VERSION")
        if os.path.isfile(version_path):
            with open(version_path) as f:
                return f.read().strip()
    except Exception:
        pass
    return API_VERSION


_BUILD_VERSION: str = _read_version_file()


def _get_dependency_status() -> Dict:
    diag = get_diagnostics()
    return {
        "model": "loaded" if diag["model_status"] else "missing",
        "vectorizer": "loaded" if os.path.isfile(settings.VECTORIZER_PATH) else "missing",
        "config": "valid",
    }


def _get_checks() -> List[Dict]:
    checks = []
    model_ok = os.path.isfile(settings.MODEL_PATH) and os.path.isfile(settings.VECTORIZER_PATH)
    checks.append({"name": "ml_model", "status": "pass" if model_ok else "fail"})
    if settings.AUTH_ENABLED and not settings.AUTH_JWT_SECRET:
        checks.append({"name": "jwt_secret", "status": "fail"})
    else:
        checks.append({"name": "jwt_secret", "status": "pass"})
    return checks


@router.get("/health")
def health() -> Dict:
    diag = get_diagnostics()
    model_ok = diag["model_status"]
    return {
        "status": "pass",
        "service": SERVICE_NAME,
        "version": API_VERSION,
        "build_version": _BUILD_VERSION,
        "environment": settings.ENVIRONMENT,
        "startup_timestamp": _startup_time,
        "uptime_seconds": int(time.time() - _startup_time),
        "release_id": _BUILD_VERSION,
        "checks": _get_checks(),
        "dependencies": _get_dependency_status(),
        "config_summary": diag.get("config_summary"),
        "service_availability": "all_services_available" if model_ok else "degraded",
        "active_requests": metrics.active_requests,
        "test_mode": os.getenv("SCAMSHIELD_TEST_MODE", "false").lower() == "true",
    }


@router.get("/ready")
def ready() -> Dict:
    diag = get_diagnostics()
    errors = []
    if not diag["model_status"]:
        errors.append("ML model not loaded")
    if not diag.get("config_valid", True):
        errors.append("Configuration is invalid")
    services_ok = all(
        diag.get("services", {}).get(s, {}).get("loaded", True)
        for s in ["ml_service"]
    )
    if not services_ok:
        errors.append("Required services not initialised")

    if errors:
        return {"status": "NOT READY", "errors": errors}
    return {"status": "READY"}


@router.get("/live")
def live() -> Dict:
    return {"status": "alive"}
