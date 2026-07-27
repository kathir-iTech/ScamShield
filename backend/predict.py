import threading
from typing import Tuple, Optional

import joblib

from config.settings import MODEL_PATH, VECTORIZER_PATH
from core.exceptions import ModelLoadError
from core.logger import logger
from utils.text import clean_text

_model: Optional[object] = None
_vectorizer: Optional[object] = None
_lock = threading.Lock()
_loaded: bool = False


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
            logger.info("ML model loaded from %s", MODEL_PATH)
        except Exception as exc:
            _model = None
            _vectorizer = None
            raise ModelLoadError(f"Failed to load ML model: {exc}") from exc


def predict(text: str) -> Tuple[str, float]:
    _lazy_load()
    cleaned = clean_text(text)
    vec = _vectorizer.transform([cleaned])
    proba = _model.predict_proba(vec)[0]
    label_idx = _model.predict(vec)[0]
    label = "scam" if label_idx == 1 else "safe"
    confidence = float(max(proba))
    return label, confidence
