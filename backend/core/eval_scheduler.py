from __future__ import annotations

import csv
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.evaluation_v2 import evaluate_classification, compare_evaluations
from core.logger import logger
from config.settings import DATASET_PATH, MODEL_PATH, VECTORIZER_PATH

EVALS_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
    "evaluations",
)


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
            })
    return samples


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
    try:
        baseline = get_latest_evaluation()
        comparison = compare_with_baseline(result, baseline.metrics if baseline else None)
        regressions = comparison.get("regressions", [])
        improvements = comparison.get("improvements", [])
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
