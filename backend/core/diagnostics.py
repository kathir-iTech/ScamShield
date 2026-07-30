import os
import shutil
import time
from typing import Dict, Optional

from core.constants import (
    SERVICE_NAME,
    API_VERSION,
    CATEGORY_KEYWORDS,
    CATEGORY_THREATS,
    CATEGORY_RECOMMENDATIONS,
    ASSESSMENT_IMMEDIATE_ACTION,
    ASSESSMENT_INVESTIGATION,
    ASSESSMENT_REVIEW,
    ASSESSMENT_NORMAL,
    ENTITY_RISK_MAP,
    INDICATOR_PATTERNS,
    EVIDENCE_CORRELATIONS,
)
from config import settings

_prometheus_available: bool = False
_redis_available: bool = False
_model_version: str = API_VERSION


def set_prometheus_available(available: bool) -> None:
    global _prometheus_available
    _prometheus_available = available


def set_redis_available(available: bool) -> None:
    global _redis_available
    _redis_available = available


def set_model_version(version: str) -> None:
    global _model_version
    _model_version = version

_startup_time: float = time.time()


def _model_exists() -> bool:
    return os.path.isfile(settings.MODEL_PATH) and os.path.isfile(settings.VECTORIZER_PATH)


def _get_disk_usage() -> Optional[Dict]:
    try:
        usage = shutil.disk_usage(settings.BASE_DIR)
        return {
            "total_gb": round(usage.total / (1024**3), 1),
            "used_gb": round(usage.used / (1024**3), 1),
            "free_gb": round(usage.free / (1024**3), 1),
            "percent_free": round(usage.free / usage.total * 100, 1),
        }
    except Exception:
        return None


def _get_memory_usage() -> Optional[Dict]:
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 1),
            "available_gb": round(mem.available / (1024**3), 1),
            "percent_used": mem.percent,
        }
    except ImportError:
        return None
    except Exception:
        return None


def _get_config_summary() -> Dict:
    return {
        "max_text_length": settings.MAX_TEXT_LENGTH,
        "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
        "model_path": settings.MODEL_PATH,
        "vectorizer_path": settings.VECTORIZER_PATH,
        "supported_image_types": settings.SUPPORTED_IMAGE_TYPES,
        "log_level": os.getenv("SCAMSHIELD_LOG_LEVEL", "INFO"),
        "log_format": os.getenv("SCAMSHIELD_LOG_FORMAT", "text"),
    }


def get_diagnostics() -> Dict:
    return {
        "service": SERVICE_NAME,
        "version": API_VERSION,
        "model_status": _model_exists(),
        "config_valid": True,
        "startup_time": _startup_time,
        "uptime_seconds": round(time.time() - _startup_time, 1),
        "config_summary": _get_config_summary(),
        "disk_usage": _get_disk_usage(),
        "memory_usage": _get_memory_usage(),
        "services": {
            "ml_service": {"loaded": _model_exists()},
            "rules_service": {"loaded": True},
            "intel_service": {"loaded": True},
            "evidence_service": {"loaded": True},
            "assessment_service": {"loaded": True},
            "report_service": {"loaded": True},
            "explanation_service": {"loaded": True},
        },
        "pipeline_summary": {
            "stages": [
                "ML Prediction",
                "Rule Engine",
                "Explanation",
                "Threat Intelligence",
                "Evidence",
                "Assessment",
                "Report",
            ],
            "total_stages": 7,
        },
        "registered_services": [
            "ml_service",
            "rules_service",
            "intel_service",
            "explanation_service",
            "evidence_service",
            "assessment_service",
            "report_service",
        ],
        "configuration_summary": {
            "max_text_length": settings.MAX_TEXT_LENGTH,
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "model_path": settings.MODEL_PATH,
            "vectorizer_path": settings.VECTORIZER_PATH,
            "supported_image_types": settings.SUPPORTED_IMAGE_TYPES,
        },
        "entity_extractor_count": len(ENTITY_RISK_MAP),
        "evidence_correlation_count": len(EVIDENCE_CORRELATIONS),
        "supported_scam_categories": list(CATEGORY_KEYWORDS.keys()),
        "supported_assessment_bands": [
            ASSESSMENT_IMMEDIATE_ACTION,
            ASSESSMENT_INVESTIGATION,
            ASSESSMENT_REVIEW,
            ASSESSMENT_NORMAL,
        ],
        "registered_routes": [
            "/health",
            "/ready",
            "/live",
            "/version",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/analyze/text",
            "/analyze/image",
            "/metrics",
        ],
        "observability": {
            "prometheus": "available" if _prometheus_available else "unavailable",
            "redis": "available" if _redis_available else "unavailable",
        },
        "model_version": _model_version,
    }
