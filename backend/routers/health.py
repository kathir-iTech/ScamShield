import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from core.constants import SERVICE_NAME, API_VERSION
from core.diagnostics import get_diagnostics
from core.metrics import metrics
from core.prediction_logger import get_prediction_logger
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


def _get_model_info() -> Dict[str, Any]:
    try:
        from predict import get_model_info as _gmi
        return _gmi()
    except Exception:
        return {"version": "unknown", "model_type": "unknown", "status": "unknown"}


def _get_prediction_stats() -> Dict[str, Any]:
    try:
        pl = get_prediction_logger()
        stats = pl.get_stats()
        daily = pl.get_daily_stats()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_count = daily.get(today, {}).get("total", 0) if isinstance(daily, dict) else 0
        return {
            "total_predictions": stats.get("total", 0),
            "today_predictions": today_count,
            "avg_confidence": stats.get("avg_confidence", 0.0),
        }
    except Exception:
        return {"total_predictions": 0, "today_predictions": 0, "avg_confidence": 0.0}


@router.get("/health")
def health() -> Dict:
    diag = get_diagnostics()
    model_ok = diag["model_status"]
    model_info = _get_model_info()
    pred_stats = _get_prediction_stats()
    return {
        "status": "pass",
        "service": SERVICE_NAME,
        "version": API_VERSION,
        "build_version": _BUILD_VERSION,
        "environment": settings.ENVIRONMENT,
        "startup_timestamp": _startup_time,
        "uptime_seconds": int(time.time() - _startup_time),
        "release_id": _BUILD_VERSION,
        "model_version": model_info.get("version", "unknown"),
        "model_status": model_info.get("status", "unknown"),
        "total_predictions": pred_stats.get("total_predictions", 0),
        "today_predictions": pred_stats.get("today_predictions", 0),
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


@router.get("/model/info")
def model_info() -> Dict[str, Any]:
    try:
        from predict import get_model_info as _gmi
        info = _gmi()
    except Exception:
        info = {"version": "unknown", "model_type": "unknown", "status": "unknown"}

    pred_stats = _get_prediction_stats()

    try:
        from core.model_registry import get_registry
        reg = get_registry()
        registered_count = reg.model_count()
        active_version = reg.get_active_model()
        active_ver = active_version.version if active_version else "none"
    except Exception:
        registered_count = 0
        active_ver = "unknown"

    return {
        "model": info,
        "registry": {
            "registered_models": registered_count,
            "active_version": active_ver,
        },
        "predictions": pred_stats,
    }
