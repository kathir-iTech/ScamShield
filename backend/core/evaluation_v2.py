import json
import math
import os
import time
from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple


class EvaluationMetrics:
    def __init__(self, y_true: List[int], y_pred: List[int], y_scores: Optional[List[float]] = None):
        self.y_true = y_true
        self.y_pred = y_pred
        self.y_scores = y_scores or [float(p) for p in y_pred]
        self.n = len(y_true)
        self._compute()

    def _compute(self):
        tp = fp = fn = tn = 0
        for t, p in zip(self.y_true, self.y_pred):
            if t == 1 and p == 1:
                tp += 1
            elif t == 0 and p == 1:
                fp += 1
            elif t == 1 and p == 0:
                fn += 1
            else:
                tn += 1

        self.tp = tp
        self.fp = fp
        self.fn = fn
        self.tn = tn

        self.accuracy = (tp + tn) / self.n if self.n > 0 else 0.0
        self.precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        self.recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        self.f1 = 2 * self.precision * self.recall / (self.precision + self.recall) if (self.precision + self.recall) > 0 else 0.0
        self.fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        self.fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        self.balanced_accuracy = (self.recall + tn / (tn + fp) if (tn + fp) > 0 else 0.0) / 2.0
        mcc_num = (tp * tn) - (fp * fn)
        mcc_den = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) if (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn) > 0 else 1.0
        self.mcc = mcc_num / mcc_den

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "tp": self.tp, "fp": self.fp, "fn": self.fn, "tn": self.tn,
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "fpr": round(self.fpr, 4),
            "fnr": round(self.fnr, 4),
            "balanced_accuracy": round(self.balanced_accuracy, 4),
            "mcc": round(self.mcc, 4),
        }

    def summary(self) -> str:
        d = self.to_dict()
        return (
            f"n={d['n']}  acc={d['accuracy']:.1%}  prec={d['precision']:.1%}  rec={d['recall']:.1%}  "
            f"f1={d['f1']:.1%}  fpr={d['fpr']:.1%}  fnr={d['fnr']:.1%}  mcc={d['mcc']:.3f}"
        )


def evaluate_classification(
    classifier_fn: Callable[[str], Dict[str, Any]],
    samples: List[Dict[str, Any]],
    text_key: str = "text",
    label_key: str = "expected_prediction",
    verbose: bool = False,
) -> Dict[str, Any]:
    y_true: List[int] = []
    y_pred: List[int] = []
    y_scores: List[float] = []
    predictions: List[Dict] = []
    inference_times: List[float] = []
    errors: List[Dict] = []

    scam_label = "scam"
    safe_label = "safe"

    for i, sample in enumerate(samples):
        text = sample[text_key]
        expected = sample[label_key]
        true_label = 1 if expected == scam_label else 0

        start = time.perf_counter()
        try:
            result = classifier_fn(text)
        except Exception as e:
            errors.append({"id": sample.get("id", str(i)), "error": str(e)})
            y_true.append(true_label)
            y_pred.append(0)
            y_scores.append(0.0)
            continue

        elapsed = (time.perf_counter() - start) * 1000
        inference_times.append(elapsed)

        actual = result.get("prediction", safe_label)
        confidence = result.get("confidence", 0.0)
        pred_label = 1 if actual == scam_label else 0

        y_true.append(true_label)
        y_pred.append(pred_label)
        y_scores.append(confidence)

        predictions.append({
            "id": sample.get("id", str(i)),
            "text": text[:200],
            "expected": expected,
            "actual": actual,
            "confidence": confidence,
            "category": {
                "expected": sample.get("expected_category", ""),
                "actual": result.get("scam_category", ""),
            },
            "risk_level": {
                "expected": sample.get("expected_risk_level", ""),
                "actual": result.get("risk_level", ""),
            },
            "assessment": {
                "expected": sample.get("expected_assessment_band", ""),
                "actual": result.get("assessment_band", ""),
            },
            "inference_ms": round(elapsed, 1),
            "correct": true_label == pred_label,
        })

        if verbose and i % 10 == 0:
            print(f"  [{i+1}/{len(samples)}] processed")

    metrics = EvaluationMetrics(y_true, y_pred, y_scores)
    cat_stats = _category_stats(samples, predictions)
    lang_stats = _language_stats(samples, predictions)

    sorted_times = sorted(inference_times)
    avg_latency = sum(inference_times) / len(inference_times) if inference_times else 0.0
    p95_idx = int(len(sorted_times) * 0.95)
    p95_latency = sorted_times[p95_idx] if p95_idx < len(sorted_times) else (sorted_times[-1] if sorted_times else 0.0)

    result = {
        "metrics": metrics.to_dict(),
        "summary": metrics.summary(),
        "predictions": predictions,
        "errors": errors,
        "category_breakdown": cat_stats,
        "language_breakdown": lang_stats,
        "latency": {
            "average_ms": round(avg_latency, 1),
            "p95_ms": round(p95_latency, 1),
            "count": len(inference_times),
        },
        "samples": {
            "total": len(samples),
            "scam": sum(1 for s in samples if s.get(label_key) == scam_label),
            "safe": sum(1 for s in samples if s.get(label_key) == safe_label),
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    return result


def _category_stats(
    samples: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    stats: Dict[str, Dict] = defaultdict(lambda: {"total": 0, "correct": 0, "risk_correct": 0, "assessment_correct": 0})
    for sample, pred in zip(samples, predictions):
        cat = sample.get("expected_category", "Unknown")
        stats[cat]["total"] += 1
        if pred.get("correct"):
            stats[cat]["correct"] += 1
        if pred.get("risk_level", {}).get("expected") == pred.get("risk_level", {}).get("actual"):
            stats[cat]["risk_correct"] += 1
        if pred.get("assessment", {}).get("expected") == pred.get("assessment", {}).get("actual"):
            stats[cat]["assessment_correct"] += 1

    result = []
    for cat, s in sorted(stats.items()):
        result.append({
            "category": cat,
            "total": s["total"],
            "accuracy": round(s["correct"] / s["total"], 4) if s["total"] > 0 else 0.0,
            "risk_accuracy": round(s["risk_correct"] / s["total"], 4) if s["total"] > 0 else 0.0,
            "assessment_accuracy": round(s["assessment_correct"] / s["total"], 4) if s["total"] > 0 else 0.0,
        })
    return result


def _language_stats(
    samples: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    stats: Dict[str, Dict] = defaultdict(lambda: {"total": 0, "correct": 0})
    for sample, pred in zip(samples, predictions):
        lang = sample.get("language", "en")
        stats[lang]["total"] += 1
        if pred.get("correct"):
            stats[lang]["correct"] += 1

    result = []
    for lang, s in sorted(stats.items()):
        result.append({
            "language": lang,
            "total": s["total"],
            "accuracy": round(s["correct"] / s["total"], 4) if s["total"] > 0 else 0.0,
        })
    return result


def regression_check(
    baseline_metrics: Dict[str, Any],
    current_metrics: Dict[str, Any],
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    default_thresholds = {
        "accuracy_drop": 0.02,
        "precision_drop": 0.02,
        "recall_drop": 0.02,
        "f1_drop": 0.02,
        "fpr_increase": 0.02,
        "fnr_increase": 0.02,
    }
    thresholds = thresholds or default_thresholds

    issues = []
    for metric, max_drop in thresholds.items():
        if metric.endswith("_drop"):
            base_key = metric.replace("_drop", "")
            base = baseline_metrics.get(base_key, 0.0)
            curr = current_metrics.get(base_key, 0.0)
            if base - curr > max_drop:
                issues.append(f"{base_key}: {curr:.1%} vs baseline {base:.1%} (drop > {max_drop:.1%})")
        elif metric.endswith("_increase"):
            base_key = metric.replace("_increase", "")
            base = baseline_metrics.get(base_key, 0.0)
            curr = current_metrics.get(base_key, 0.0)
            if curr - base > max_drop:
                issues.append(f"{base_key}: {curr:.1%} vs baseline {base:.1%} (increase > {max_drop:.1%})")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "compared_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def save_evaluation_result(result: Dict[str, Any], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"eval_{timestamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    return path


def evaluate_pipeline(
    pipeline_fn: Callable[[str], Dict[str, Any]],
    texts: List[str],
    expected_labels: List[int],
    verbose: bool = False,
) -> Dict[str, Any]:
    y_pred: List[int] = []
    y_scores: List[float] = []
    errors: List[Dict] = []
    inference_times: List[float] = []

    for i, (text, expected) in enumerate(zip(texts, expected_labels)):
        start = time.perf_counter()
        try:
            result = pipeline_fn(text)
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
            y_pred.append(0)
            y_scores.append(0.0)
            continue
        elapsed = (time.perf_counter() - start) * 1000
        inference_times.append(elapsed)

        actual = result.get("prediction", "safe")
        confidence = result.get("confidence", 0.0)
        y_pred.append(1 if actual == "scam" else 0)
        y_scores.append(confidence)

    metrics = EvaluationMetrics(expected_labels, y_pred, y_scores)
    sorted_times = sorted(inference_times)
    p95_idx = int(len(sorted_times) * 0.95)

    return {
        "metrics": metrics.to_dict(),
        "summary": metrics.summary(),
        "latency": {
            "average_ms": round(sum(inference_times) / len(inference_times), 1) if inference_times else 0.0,
            "p95_ms": round(sorted_times[p95_idx], 1) if sorted_times else 0.0,
            "count": len(inference_times),
        },
        "errors": errors,
        "samples": {"total": len(texts), "scam": sum(expected_labels), "safe": len(expected_labels) - sum(expected_labels)},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def compare_evaluations(
    results: List[Dict[str, Any]],
    labels: List[str],
) -> Dict[str, Any]:
    comparison = {
        "comparisons": [],
        "regressions": [],
        "improvements": [],
    }
    for i, result in enumerate(results):
        comparison["comparisons"].append({
            "label": labels[i] if i < len(labels) else f"run_{i}",
            "metrics": result["metrics"],
            "latency": result.get("latency", {}),
        })

    if len(results) >= 2:
        first = results[0]["metrics"]
        for i in range(1, len(results)):
            curr = results[i]["metrics"]
            regs = []
            imprs = []
            for key in ("accuracy", "precision", "recall", "f1"):
                diff = curr.get(key, 0) - first.get(key, 0)
                if diff < -0.01:
                    regs.append({"metric": key, "change": round(diff, 4)})
                elif diff > 0.01:
                    imprs.append({"metric": key, "change": round(diff, 4)})
            for key in ("fpr", "fnr"):
                diff = curr.get(key, 0) - first.get(key, 0)
                if diff > 0.01:
                    regs.append({"metric": key, "change": round(diff, 4)})
                elif diff < -0.01:
                    imprs.append({"metric": key, "change": round(diff, 4)})
            comparison["regressions"].extend(regs)
            comparison["improvements"].extend(imprs)

    return comparison


def generate_trend_report(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not history:
        return {"runs": 0, "trends": {}}
    trends: Dict[str, list] = {}
    for entry in history:
        ts = entry.get("timestamp", "")
        m = entry.get("metrics", {})
        for key in ("accuracy", "precision", "recall", "f1", "fpr", "fnr"):
            if key not in trends:
                trends[key] = []
            trends[key].append({"timestamp": ts, "value": m.get(key, 0)})
    latest = history[-1].get("metrics", {})
    first = history[0].get("metrics", {})
    directions = {}
    for key in ("accuracy", "precision", "recall", "f1"):
        directions[key] = "up" if latest.get(key, 0) > first.get(key, 0) else "down"
    for key in ("fpr", "fnr"):
        directions[key] = "down" if latest.get(key, 0) < first.get(key, 0) else "up"
    return {
        "runs": len(history),
        "trends": trends,
        "direction": directions,
        "latest": latest,
        "first": first,
    }


def format_report(result: Dict[str, Any]) -> str:
    m = result["metrics"]
    lines = [
        "=" * 60,
        "  EVALUATION REPORT",
        "=" * 60,
        f"  Samples:      {result['samples']['total']} ({result['samples']['scam']} scam / {result['samples']['safe']} safe)",
        f"  Accuracy:     {m['accuracy']:.1%}",
        f"  Precision:    {m['precision']:.1%}",
        f"  Recall:       {m['recall']:.1%}",
        f"  F1 Score:     {m['f1']:.1%}",
        f"  FPR:          {m['fpr']:.1%}",
        f"  FNR:          {m['fnr']:.1%}",
        f"  MCC:          {m['mcc']:.3f}",
        f"  Bal. Acc:     {m['balanced_accuracy']:.1%}",
        f"  Confusion:    TP={m['tp']} FP={m['fp']} FN={m['fn']} TN={m['tn']}",
        f"  Avg Latency:  {result['latency']['average_ms']:.1f}ms",
        f"  P95 Latency:  {result['latency']['p95_ms']:.1f}ms",
    ]
    if result.get("category_breakdown"):
        lines.append("")
        lines.append("  Category Breakdown:")
        for c in result["category_breakdown"]:
            lines.append(f"    {c['category']:30s} acc={c['accuracy']:.1%}  risk={c['risk_accuracy']:.1%}  assess={c['assessment_accuracy']:.1%}  n={c['total']}")
    if result.get("language_breakdown"):
        lines.append("")
        lines.append("  Language Breakdown:")
        for l in result["language_breakdown"]:
            lines.append(f"    {l['language']:10s} acc={l['accuracy']:.1%}  n={l['total']}")
    lines.append("=" * 60)
    return "\n".join(lines)
