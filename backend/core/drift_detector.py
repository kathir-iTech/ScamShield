from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DriftResult:
    has_drift: bool
    metric_name: str
    current_value: float
    baseline_value: float
    threshold: float
    severity: str = "none"
    timestamp: str = ""
    details: str = ""


class DriftDetector:

    @staticmethod
    def check_accuracy_drift(
        current_accuracy: float,
        baseline_accuracy: float,
        threshold: float = 0.05,
    ) -> DriftResult:
        drop = baseline_accuracy - current_accuracy
        has_drift = drop > threshold
        severity: str = "none"
        if has_drift:
            if drop > threshold * 2:
                severity = "critical"
            else:
                severity = "warning"
        return DriftResult(
            has_drift=has_drift,
            metric_name="accuracy",
            current_value=round(current_accuracy, 4),
            baseline_value=round(baseline_accuracy, 4),
            threshold=threshold,
            severity=severity,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=(
                f"Accuracy dropped from {baseline_accuracy:.1%} to {current_accuracy:.1%} "
                f"(drop={drop:.1%}, threshold={threshold:.1%})"
                if has_drift
                else f"Accuracy stable at {current_accuracy:.1%} (baseline={baseline_accuracy:.1%})"
            ),
        )

    @staticmethod
    def check_confidence_drift(
        confidence_distribution: Dict[str, float],
        baseline_distribution: Dict[str, float],
        threshold: float = 0.1,
    ) -> DriftResult:
        total_drift = 0.0
        all_keys = set(confidence_distribution) | set(baseline_distribution)
        for key in all_keys:
            curr = confidence_distribution.get(key, 0.0)
            base = baseline_distribution.get(key, 0.0)
            total_drift += abs(curr - base)
        has_drift = total_drift > threshold
        severity: str = "none"
        if has_drift:
            if total_drift > threshold * 2:
                severity = "critical"
            else:
                severity = "warning"
        return DriftResult(
            has_drift=has_drift,
            metric_name="confidence_distribution",
            current_value=round(total_drift, 4),
            baseline_value=0.0,
            threshold=threshold,
            severity=severity,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=(
                f"Confidence distribution drift={total_drift:.1%} "
                f"(threshold={threshold:.1%})"
                if has_drift
                else f"Confidence distribution stable (drift={total_drift:.1%})"
            ),
        )

    @staticmethod
    def check_data_drift(
        current_class_ratio: float,
        baseline_class_ratio: float,
        threshold: float = 0.1,
    ) -> DriftResult:
        change = abs(current_class_ratio - baseline_class_ratio)
        has_drift = change > threshold
        severity: str = "none"
        if has_drift:
            if change > threshold * 2:
                severity = "critical"
            else:
                severity = "warning"
        return DriftResult(
            has_drift=has_drift,
            metric_name="class_ratio",
            current_value=round(current_class_ratio, 4),
            baseline_value=round(baseline_class_ratio, 4),
            threshold=threshold,
            severity=severity,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=(
                f"Class ratio changed from {baseline_class_ratio:.2f} to {current_class_ratio:.2f} "
                f"(change={change:.2f}, threshold={threshold:.2f})"
                if has_drift
                else f"Class ratio stable at {current_class_ratio:.2f}"
            ),
        )

    @staticmethod
    def check_latency_drift(
        current_p95: float,
        baseline_p95: float,
        threshold: float = 0.2,
    ) -> DriftResult:
        if baseline_p95 <= 0:
            return DriftResult(
                has_drift=False,
                metric_name="latency_p95",
                current_value=round(current_p95, 1),
                baseline_value=round(baseline_p95, 1),
                threshold=threshold,
                severity="none",
                timestamp=datetime.now(timezone.utc).isoformat(),
                details="No baseline latency available",
            )
        increase = (current_p95 - baseline_p95) / baseline_p95
        has_drift = increase > threshold
        severity: str = "none"
        if has_drift:
            if increase > threshold * 2:
                severity = "critical"
            else:
                severity = "warning"
        return DriftResult(
            has_drift=has_drift,
            metric_name="latency_p95",
            current_value=round(current_p95, 1),
            baseline_value=round(baseline_p95, 1),
            threshold=threshold,
            severity=severity,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=(
                f"P95 latency increased by {increase:.1%} "
                f"({baseline_p95:.1f}ms -> {current_p95:.1f}ms, threshold={threshold:.1%})"
                if has_drift
                else f"P95 latency stable ({current_p95:.1f}ms vs baseline {baseline_p95:.1f}ms)"
            ),
        )

    @classmethod
    def run_all_checks(
        cls,
        prediction_logger: Any,
    ) -> List[DriftResult]:
        results: List[DriftResult] = []
        stats = prediction_logger.get_stats()
        if stats["total"] == 0:
            return results

        results.append(cls.check_accuracy_drift(
            current_accuracy=1.0 - (stats.get("scam", 0) / max(stats["total"], 1)),
            baseline_accuracy=0.95,
        ))

        conf_dist = stats.get("confidence_distribution", {})
        total = sum(conf_dist.values()) or 1
        conf_pct = {k: v / total for k, v in conf_dist.items()}
        results.append(cls.check_confidence_drift(
            confidence_distribution=conf_pct,
            baseline_distribution={"0.7_0.9": 0.3, "0.9_1.0": 0.7},
        ))

        scam_ratio = stats.get("scam_ratio", 0.0)
        results.append(cls.check_data_drift(
            current_class_ratio=scam_ratio,
            baseline_class_ratio=0.7,
        ))

        return results

    @staticmethod
    def generate_report(results: List[DriftResult]) -> str:
        if not results:
            return "No drift checks performed."

        lines = ["=" * 60, "  DRIFT DETECTION REPORT", "=" * 60]
        drift_count = sum(1 for r in results if r.has_drift)
        lines.append(f"  Checks: {len(results)}  Drifts detected: {drift_count}")
        lines.append("")

        for r in results:
            icon = "DRIFT" if r.has_drift else "OK"
            sev = f"[{r.severity.upper()}]" if r.has_drift else ""
            lines.append(f"  {icon:5s} {sev:10s} {r.metric_name}")
            lines.append(f"         {r.details}")

        lines.append("=" * 60)
        return "\n".join(lines)


def detect_drift() -> List[DriftResult]:
    from core.prediction_logger import get_prediction_logger
    pl = get_prediction_logger()
    return DriftDetector.run_all_checks(pl)
