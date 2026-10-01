from __future__ import annotations

import csv
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.evaluation_v2 import evaluate_classification, compare_evaluations, regression_check
from core.logger import logger
from core.multilingual import detect_language
from config.settings import DATASET_PATH, MODEL_PATH, VECTORIZER_PATH

EVALS_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
    "evaluations",
)

DEFAULT_THRESHOLDS: Dict[str, float] = {
    "accuracy": 0.01,
    "precision": 0.01,
    "recall": 0.01,
    "f1": 0.01,
    "fpr": 0.01,
    "fnr": 0.01,
}


@dataclass
class EvaluationResult:
    timestamp: str
    metrics: Dict[str, Any]
    dataset: str
    model_version: str
    duration: float
    regressions: List[Dict] = field(default_factory=list)
    improvements: List[Dict] = field(default_factory=list)
    latency: Dict[str, Any] = field(default_factory=dict)
    samples: Dict[str, Any] = field(default_factory=dict)
    file_path: str = ""
    language_breakdown: List[Dict[str, Any]] = field(default_factory=list)
    threshold_check: Dict[str, Any] = field(default_factory=dict)


def _classifier_fn(text: str) -> Dict[str, Any]:
    import joblib
    from utils.text import clean_text
    try:
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
    except Exception as exc:
        raise RuntimeError(f"Failed to load model for evaluation: {exc}") from exc
    cleaned = clean_text(text)
    vec = vectorizer.transform([cleaned])
    proba = model.predict_proba(vec)[0]
    label_idx = model.predict(vec)[0]
    label = "scam" if label_idx == 1 else "safe"
    confidence = float(max(proba))
    return {"prediction": label, "confidence": confidence}


def _load_dataset_samples(dataset_path: str) -> List[Dict[str, Any]]:
    samples: List[Dict[str, Any]] = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("text", "").strip()
            if not text:
                continue
            expected = row.get("is_scam", row.get("label", "")).strip().lower()
            if expected in ("1", "true", "scam", "yes"):
                expected_label = "scam"
            elif expected in ("0", "false", "safe", "no", "legitimate", "legit"):
                expected_label = "safe"
            else:
                continue
            samples.append({
                "id": row.get("id", str(len(samples))),
                "text": text,
                "expected_prediction": expected_label,
                "expected_category": row.get("category", ""),
                "language": row.get("language", "").strip() or detect_language(text),
            })
    return samples


def load_thresholds(path: Optional[str] = None) -> Dict[str, float]:
    thresholds = dict(DEFAULT_THRESHOLDS)
    candidate = path or os.getenv("SCAMSHIELD_EVAL_THRESHOLDS", "")
    if candidate and os.path.isfile(candidate):
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            for key, value in loaded.items():
                if key in thresholds and isinstance(value, (int, float)):
                    thresholds[key] = float(value)
        except Exception as exc:
            logger.warning("Could not load eval thresholds from %s: %s", candidate, exc)
    return thresholds


def _to_regression_thresholds(thresholds: Dict[str, float]) -> Dict[str, float]:
    regression: Dict[str, float] = {}
    for key, value in thresholds.items():
        if key in ("fpr", "fnr"):
            regression[f"{key}_increase"] = value
        else:
            regression[f"{key}_drop"] = value
    return regression


def _get_model_version() -> str:
    try:
        from core.model_registry import get_registry
        reg = get_registry()
        active = reg.get_active_model()
        if active:
            return active.version
    except Exception:
        pass
    return "unknown"


def run_scheduled_evaluation(
    dataset_path: Optional[str] = None,
) -> EvaluationResult:
    path = dataset_path or DATASET_PATH
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Evaluation dataset not found: {path}")

    model_version = _get_model_version()
    samples = _load_dataset_samples(path)

    start = time.perf_counter()
    result = evaluate_classification(_classifier_fn, samples)
    duration = time.perf_counter() - start

    os.makedirs(EVALS_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    file_name = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    file_path = os.path.join(EVALS_DIR, f"{file_name}.json")

    regressions = []
    improvements = []
    thresholds = load_thresholds()
    threshold_check: Dict[str, Any] = {"passed": True, "issues": [], "thresholds": thresholds}
    try:
        baseline = get_latest_evaluation()
        comparison = compare_with_baseline(result, baseline.metrics if baseline else None)
        regressions = comparison.get("regressions", [])
        improvements = comparison.get("improvements", [])
        if baseline is not None:
            threshold_check = regression_check(
                baseline.metrics,
                result.get("metrics", {}),
                _to_regression_thresholds(thresholds),
            )
            threshold_check["thresholds"] = thresholds
    except Exception as exc:
        logger.warning("Could not compare with baseline: %s", exc)

    eval_result = EvaluationResult(
        timestamp=timestamp,
        metrics=result.get("metrics", {}),
        dataset=path,
        model_version=model_version,
        duration=round(duration, 2),
        regressions=regressions,
        improvements=improvements,
        latency=result.get("latency", {}),
        samples=result.get("samples", {}),
        file_path=file_path,
        language_breakdown=result.get("language_breakdown", []),
        threshold_check=threshold_check,
    )

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(asdict(eval_result), f, indent=2, default=str)

    logger.info(
        "Evaluation complete: acc=%.1f%% f1=%.1f%% (%d samples, %.1fs)",
        eval_result.metrics.get("accuracy", 0) * 100,
        eval_result.metrics.get("f1", 0) * 100,
        eval_result.samples.get("total", 0),
        duration,
    )
    for entry in eval_result.language_breakdown:
        logger.info(
            "  language=%s n=%d acc=%.1f%%",
            entry.get("language", "?"),
            entry.get("total", 0),
            entry.get("accuracy", 0) * 100,
        )
    if not threshold_check.get("passed", True):
        logger.warning("Threshold check failed: %s", threshold_check.get("issues", []))

    return eval_result


def get_latest_evaluation() -> Optional[EvaluationResult]:
    if not os.path.isdir(EVALS_DIR):
        return None
    files = sorted(
        [f for f in os.listdir(EVALS_DIR) if f.endswith(".json")],
        reverse=True,
    )
    if not files:
        return None
    latest = files[0]
    path = os.path.join(EVALS_DIR, latest)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return EvaluationResult(**data)


def get_evaluation_history(n: int = 10) -> List[EvaluationResult]:
    if not os.path.isdir(EVALS_DIR):
        return []
    files = sorted(
        [f for f in os.listdir(EVALS_DIR) if f.endswith(".json")],
        reverse=True,
    )[:n]
    results: List[EvaluationResult] = []
    for fname in files:
        path = os.path.join(EVALS_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            results.append(EvaluationResult(**data))
        except Exception:
            continue
    return results


def compare_with_baseline(
    current: Dict[str, Any],
    baseline: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if baseline is None:
        return {"regressions": [], "improvements": []}
    return compare_evaluations([baseline, current], ["baseline", "current"])
