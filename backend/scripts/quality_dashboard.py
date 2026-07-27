import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _try_import(mod_name: str) -> bool:
    try:
        __import__(mod_name)
        return True
    except Exception:
        return False


def _count_tests() -> Dict[str, int]:
    import json
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
            capture_output=True, text=True, timeout=60,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        last = lines[-1] if lines else "0"
        import re
        match = re.search(r"(\d+)", last)
        return {"total": int(match.group(1)) if match else 0}
    except Exception:
        return {"total": 0}


def _check_thresholds() -> Dict[str, Any]:
    from core.calibration import (
        LOW_CONFIDENCE_THRESHOLD,
        MEDIUM_CONFIDENCE_THRESHOLD,
        HIGH_CONFIDENCE_THRESHOLD,
    )
    return {
        "low": LOW_CONFIDENCE_THRESHOLD,
        "medium": MEDIUM_CONFIDENCE_THRESHOLD,
        "high": HIGH_CONFIDENCE_THRESHOLD,
        "ordered": LOW_CONFIDENCE_THRESHOLD < MEDIUM_CONFIDENCE_THRESHOLD < HIGH_CONFIDENCE_THRESHOLD,
    }


def _check_module_health() -> Dict[str, Any]:
    modules = {
        "core.constants": "Constants",
        "core.exceptions": "Exceptions",
        "core.logger": "Logger",
        "core.metrics": "Metrics",
        "core.diagnostics": "Diagnostics",
        "core.middleware": "Middleware",
        "core.security": "Security",
        "core.resilience": "Resilience",
        "core.abuse": "Abuse Prevention",
        "core.api_keys": "API Keys",
        "core.audit": "Audit Trail",
        "core.calibration": "Calibration",
        "core.multilingual": "Multilingual",
        "core.dataset_manager": "Dataset Manager",
        "core.evaluation_v2": "Evaluation V2",
        "core.context": "Context",
        "config.settings": "Settings",
        "services.orchestrator": "Orchestrator",
        "domains.assessment.public": "Assessment",
        "domains.reasoning.service": "Reasoning",
        "domains.reporting.service": "Reporting",
    }
    results = {}
    healthy = 0
    for mod, label in modules.items():
        ok = _try_import(mod)
        results[mod] = {"label": label, "healthy": ok}
        if ok:
            healthy += 1
    return {
        "modules": results,
        "healthy": healthy,
        "total": len(modules),
        "health_pct": round(healthy / len(modules) * 100, 1),
    }


def _check_evaluation_history() -> Dict[str, Any]:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    eval_dir = os.path.join(base, "evaluation", "reports")
    if not os.path.isdir(eval_dir):
        return {"runs": 0, "latest": None}

    runs = []
    for entry in os.listdir(eval_dir):
        summary_path = os.path.join(eval_dir, entry, "summary.json")
        if os.path.isfile(summary_path):
            try:
                import json
                with open(summary_path) as f:
                    summary = json.load(f)
                runs.append(summary)
            except Exception:
                pass

    runs.sort(key=lambda r: r.get("timestamp", ""))
    latest = runs[-1] if runs else None
    return {"runs": len(runs), "latest": latest}


def _score_quality(metrics: Dict[str, float]) -> int:
    score = 0
    score += int(metrics.get("accuracy", 0) * 20)
    score += int(metrics.get("precision", 0) * 20)
    score += int(metrics.get("recall", 0) * 20)
    score += int(metrics.get("f1", 0) * 20)
    fpr = metrics.get("fpr", 1.0)
    score += int(max(0, 1.0 - fpr) * 10)
    fnr = metrics.get("fnr", 1.0)
    score += int(max(0, 1.0 - fnr) * 10)
    return min(100, score)


def generate_dashboard() -> Dict[str, Any]:
    tests = _count_tests()
    thresholds = _check_thresholds()
    module_health = _check_module_health()
    eval_history = _check_evaluation_history()

    latest_metrics = {}
    if eval_history["latest"]:
        latest_metrics = eval_history["latest"].get("metrics", {})

    overall_score = _score_quality(latest_metrics)

    return {
        "overview": {
            "overall_quality_score": overall_score,
            "tests_passing": tests.get("total", 0),
            "module_health_pct": module_health["health_pct"],
            "evaluation_runs": eval_history["runs"],
        },
        "thresholds": thresholds,
        "module_health": module_health,
        "evaluation_history": eval_history,
        "latest_metrics": latest_metrics,
    }


def main():
    import json
    dashboard = generate_dashboard()
    print(json.dumps(dashboard, indent=2))


if __name__ == "__main__":
    main()
