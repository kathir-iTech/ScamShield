import importlib
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(data: Any, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def check_pytest(pytest_args: Optional[List[str]] = None) -> Dict[str, Any]:
    print("=== RUN: pytest ===")
    args = [sys.executable, "-m", "pytest"] + (pytest_args or ["tests/"])
    result = subprocess.run(args, capture_output=True, text=True, timeout=300)
    lines = result.stdout.splitlines()
    passed = sum(1 for l in lines if "PASSED" in l)
    failed = sum(1 for l in lines if "FAILED" in l)
    total = passed + failed
    return {
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "total": total,
        "passed_count": passed,
        "failed_count": failed,
        "output": result.stdout[-2000:],
        "errors": result.stderr[-2000:],
    }


def check_benchmarks() -> Dict[str, Any]:
    print("=== RUN: benchmarks ===")
    try:
        result = subprocess.run(
            [sys.executable, "tests/benchmark.py"],
            capture_output=True, text=True, timeout=300,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        return {
            "passed": result.returncode == 0,
            "output": result.stdout[-1000:],
            "errors": result.stderr[-500:],
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}


def check_imports() -> Dict[str, Any]:
    print("=== CHECK: imports ===")
    modules = [
        "core.calibration", "core.multilingual", "core.dataset_manager",
        "core.evaluation_v2", "core.constants", "core.exceptions",
        "core.logger", "core.metrics", "core.diagnostics", "core.middleware",
        "config.settings", "services.orchestrator", "routers.health",
        "routers.analyze", "schemas.requests", "schemas.responses",
        "utils.validate", "predict",
    ]
    failures = []
    for mod in modules:
        try:
            importlib.import_module(mod)
        except Exception:
            failures.append(mod)
    return {"passed": len(failures) == 0, "failed_modules": failures}


def run_quality_gate() -> Dict[str, Any]:
    print("=== RUN: quality gate ===")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/quality_gate.py"],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        output = result.stdout
        passed = "FAILURES: 0" in output or result.returncode == 0
        return {"passed": passed, "exit_code": result.returncode, "output": output[-2000:]}
    except Exception as e:
        return {"passed": False, "error": str(e)}


def run_quality_dashboard(output_dir: str = "reports/dashboard"):
    from scripts.quality_dashboard import generate_dashboard
    dashboard = generate_dashboard()
    path = os.path.join(output_dir, "dashboard.json")
    _save_json(dashboard, path)
    return dashboard


def evaluate_model_on_dataset(
    dataset_path: str,
    output_dir: str,
    sample_limit: int = 0,
) -> Dict[str, Any]:
    from core.evaluation_v2 import evaluate_classification, save_evaluation_result
    from services.orchestrator import analyze_text

    samples = _load_json(dataset_path)
    if not isinstance(samples, list):
        return {"error": "Dataset must be a list", "passed": False}

    if sample_limit > 0:
        samples = samples[:sample_limit]

    def classifier(text: str) -> dict:
        return analyze_text(text)

    result = evaluate_classification(classifier, samples, verbose=True)
    save_evaluation_result(result, output_dir)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Continuous Evaluation Pipeline")
    parser.add_argument("--dataset", default="", help="Path to evaluation dataset JSON")
    parser.add_argument("--output", default="reports/continuous_eval", help="Output directory")
    parser.add_argument("--sample", type=int, default=0, help="Limit samples")
    parser.add_argument("--pytest-args", default="", help="Extra pytest arguments")
    parser.add_argument("--check", action="store_true", help="Fail if any check fails")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)
    sys.path.insert(0, base_dir)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_dir, args.output, f"eval_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    results: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checks": {},
    }

    print(f"\n{'='*60}")
    print("  CONTINUOUS EVALUATION PIPELINE")
    print(f"{'='*60}\n")

    results["checks"]["pytest"] = check_pytest(args.pytest_args.split() if args.pytest_args else None)
    results["checks"]["benchmarks"] = check_benchmarks()
    results["checks"]["imports"] = check_imports()
    results["checks"]["quality_gate"] = run_quality_gate()

    all_passed = all(c.get("passed", False) for c in results["checks"].values())
    results["all_checks_passed"] = all_passed

    if args.dataset:
        dataset_path = args.dataset
        if not os.path.isabs(dataset_path):
            dataset_path = os.path.join(base_dir, dataset_path)
        if os.path.isfile(dataset_path):
            print(f"\n=== EVALUATING: {dataset_path} ===")
            eval_result = evaluate_model_on_dataset(dataset_path, output_dir, sample_limit=args.sample)
            results["evaluation"] = eval_result.get("metrics", {})
            results["evaluation_path"] = output_dir

    summary_path = os.path.join(output_dir, "continuous_eval_summary.json")
    _save_json(results, summary_path)

    print(f"\n{'='*60}")
    print("  CONTINUOUS EVALUATION SUMMARY")
    print(f"{'='*60}")
    for name, check in results["checks"].items():
        status = "PASS" if check.get("passed") else "FAIL"
        print(f"  {name:25s} [{status}]")
    print(f"\n  All checks: {'PASSED' if all_passed else 'FAILED'}")
    print(f"  Report: {summary_path}")
    print(f"{'='*60}\n")

    if args.check and not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
