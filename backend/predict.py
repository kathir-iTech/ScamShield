import threading
from typing import Dict, List, Optional, Tuple

import joblib

from config.settings import MODEL_PATH, VECTORIZER_PATH
from core.exceptions import ModelLoadError
from core.logger import logger
from core.model_registry import get_registry
from utils.text import clean_text

_model: Optional[object] = None
_vectorizer: Optional[object] = None
_lock = threading.Lock()
_loaded: bool = False
MODEL_VERSION: str = ""


def _populate_model_version() -> None:
    global MODEL_VERSION
    try:
        reg = get_registry()
        active = reg.get_active_model()
        if active:
            MODEL_VERSION = active.version
        else:
            MODEL_VERSION = "unknown"
    except Exception:
        MODEL_VERSION = "unknown"


def _lazy_load() -> None:
    global _model, _vectorizer, _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        try:
            _model = joblib.load(MODEL_PATH)
            _vectorizer = joblib.load(VECTORIZER_PATH)
            _loaded = True
            _populate_model_version()
            logger.info("ML model loaded from %s (version %s)", MODEL_PATH, MODEL_VERSION)
        except Exception as exc:
            _model = None
            _vectorizer = None
            raise ModelLoadError(f"Failed to load ML model: {exc}") from exc


def _reload_model(model_path: str, vectorizer_path: str) -> None:
    global _model, _vectorizer, _loaded
    _model = joblib.load(model_path)
    _vectorizer = joblib.load(vectorizer_path)
    _loaded = True


def predict(text: str) -> Tuple[str, float]:
    _lazy_load()
    cleaned = clean_text(text)
    vec = _vectorizer.transform([cleaned])
    proba = _model.predict_proba(vec)[0]
    label_idx = _model.predict(vec)[0]
    label = "scam" if label_idx == 1 else "safe"
    confidence = float(max(proba))
    return label, confidence


def predict_versioned(text: str) -> Tuple[str, float, str]:
    _lazy_load()
    label, confidence = predict(text)
    return label, confidence, MODEL_VERSION


def get_model_info() -> Dict:
    _lazy_load()
    try:
        reg = get_registry()
        active = reg.get_active_model()
        if active:
            return {
                "version": active.version,
                "model_type": active.model_type,
                "trained_at": active.trained_at,
                "status": active.status,
                "dataset_samples": active.dataset_samples,
                "test_metrics": {
                    "f1": active.test_metrics.get("f1"),
                    "roc_auc": active.test_metrics.get("roc_auc"),
                    "accuracy": active.test_metrics.get("accuracy"),
                    "precision": active.test_metrics.get("precision"),
                    "recall": active.test_metrics.get("recall"),
                },
                "cv_metrics": active.cv_metrics.copy() if active.cv_metrics else {},
                "top_features": {
                    "scam": active.top_features.get("scam", [])[:10],
                    "safe": active.top_features.get("safe", [])[:10],
                },
            }
    except Exception:
        pass
    return {
        "version": MODEL_VERSION or "unknown",
        "model_type": "unknown",
        "trained_at": "",
        "status": "unknown",
    }


def rollback_model(version: Optional[str] = None) -> str:
    from core.audit import record_audit_event
    reg = get_registry()
    target_version = reg.rollback(version)
    meta = reg.get_model(target_version)
    if meta is None:
        raise ModelLoadError(f"Model {target_version} not found after rollback")
    global MODEL_VERSION
    with _lock:
        _reload_model(meta.file_path, meta.vectorizer_path)
        MODEL_VERSION = target_version
    from core.audit import record_audit_event
    record_audit_event(
        event="model:rollback",
        level="INFO",
        detail=f"Rolled back to model version {target_version}",
    )
    logger.info("Rolled back to model %s", target_version)
    return target_version


def get_model_history(n: int = 5) -> List[Dict]:
    reg = get_registry()
    models = reg.list_models()
    sorted_models = sorted(models, key=lambda m: m.trained_at, reverse=True)[:n]
    return [
        {
            "version": m.version,
            "model_type": m.model_type,
            "trained_at": m.trained_at,
            "status": m.status,
            "dataset_samples": m.dataset_samples,
            "test_f1": m.test_metrics.get("f1"),
        }
        for m in sorted_models
    ]
