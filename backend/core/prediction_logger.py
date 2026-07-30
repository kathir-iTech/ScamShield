from __future__ import annotations

import json
import os
import threading
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from core.logger import logger

LOGS_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "predictions"
)


@dataclass
class PredictionRecord:
    request_id: str
    timestamp: str
    text_hash: str
    text_preview: str
    prediction: str
    confidence: float
    model_version: str
    pipeline_steps: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    category: Optional[str] = None
    user_feedback: Optional[str] = None


class PredictionLogger:
    def __init__(self, log_dir: str = LOGS_DIR) -> None:
        self._log_dir = log_dir
        self._lock = threading.Lock()
        self._recent: deque = deque(maxlen=1000)

    def _today_path(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return os.path.join(self._log_dir, f"{date_str}.jsonl")

    def log_prediction(self, record: PredictionRecord) -> None:
        with self._lock:
            os.makedirs(self._log_dir, exist_ok=True)
            line = json.dumps(asdict(record), default=str)
            file_path = self._today_path()
            try:
                with open(file_path, "a") as f:
                    f.write(line + "\n")
                self._recent.append(record)
            except Exception as exc:
                logger.error("Failed to log prediction: %s", exc)

    def get_recent_predictions(self, n: int = 100) -> List[PredictionRecord]:
        with self._lock:
            all_records = list(self._recent)
            return all_records[-n:]

    def get_stats(self, since: Optional[datetime] = None) -> Dict:
        with self._lock:
            records = list(self._recent)
        if since:
            records = [r for r in records if r.timestamp >= since.isoformat()]
        total = len(records)
        if total == 0:
            return {"total": 0, "scam": 0, "safe": 0, "avg_confidence": 0.0}

        scam_count = sum(1 for r in records if r.prediction == "scam")
        safe_count = total - scam_count
        avg_conf = sum(r.confidence for r in records) / total

        conf_distribution = {"0_0.5": 0, "0.5_0.7": 0, "0.7_0.9": 0, "0.9_1.0": 0}
        for r in records:
            if r.confidence < 0.5:
                conf_distribution["0_0.5"] += 1
            elif r.confidence < 0.7:
                conf_distribution["0.5_0.7"] += 1
            elif r.confidence < 0.9:
                conf_distribution["0.7_0.9"] += 1
            else:
                conf_distribution["0.9_1.0"] += 1

        return {
            "total": total,
            "scam": scam_count,
            "safe": safe_count,
            "scam_ratio": round(scam_count / total, 4) if total else 0,
            "avg_confidence": round(avg_conf, 4),
            "confidence_distribution": conf_distribution,
        }

    def get_daily_stats(self) -> Dict:
        with self._lock:
            records = list(self._recent)
        daily: Dict[str, Dict] = {}
        for r in records:
            day = r.timestamp[:10]
            if day not in daily:
                daily[day] = {"total": 0, "scam": 0, "safe": 0}
            daily[day]["total"] += 1
            if r.prediction == "scam":
                daily[day]["scam"] += 1
            else:
                daily[day]["safe"] += 1
        return daily

    def recent(self, n: int = 100) -> List[PredictionRecord]:
        return self.get_recent_predictions(n)


_logger_instance: Optional[PredictionLogger] = None
_logger_lock = threading.Lock()


def get_prediction_logger() -> PredictionLogger:
    global _logger_instance
    if _logger_instance is None:
        with _logger_lock:
            if _logger_instance is None:
                _logger_instance = PredictionLogger()
    return _logger_instance


def log_prediction(
    request_id: str,
    text: str,
    prediction: str,
    confidence: float,
    model_version: str,
    pipeline_steps: Optional[List[str]] = None,
    latency_ms: float = 0.0,
    category: Optional[str] = None,
) -> None:
    import hashlib
    pl = get_prediction_logger()
    record = PredictionRecord(
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        text_hash=hashlib.md5(text.encode()).hexdigest(),
        text_preview=text[:100],
        prediction=prediction,
        confidence=confidence,
        model_version=model_version,
        pipeline_steps=pipeline_steps or [],
        latency_ms=latency_ms,
        category=category,
    )
    pl.log_prediction(record)
