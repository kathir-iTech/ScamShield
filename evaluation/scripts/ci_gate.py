"""
Single CI threshold gate for gold-set evaluations.

Runs the backend full-pipeline evaluation (datasets/gold/eval_gold_pipeline.py)
and, when node is available, the JS pipeline evaluation
(frontend/scripts/eval-gold-js.mjs). Thresholds come from evaluation/thresholds.json.

Writes evaluation/reports/ci_gate/metrics.json and prints a PASS/FAIL table.

Exit codes: 0 = pass, 1 = regression, 2 = error.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THRESHOLDS_PATH = ROOT / "evaluation" / "thresholds.json"
REPORT_DIR = ROOT / "evaluation" / "reports" / "ci_gate"
BACKEND_EVAL = ROOT / "datasets" / "gold" / "eval_gold_pipeline.py"
JS_EVAL = ROOT / "frontend" / "scripts" / "eval-gold-js.mjs"


class GateError(Exception):
    pass


def load_thresholds(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        raise GateError(f"cannot read thresholds {path}: {exc}") from exc
    for engine in ("backend", "js"):
        if engine not in data or not isinstance(data[engine], dict):
            raise GateError(f"thresholds file missing '{engine}' section: {path}")
    return data


def run_backend(thresholds: dict) -> dict:
    backend_metrics_path = REPORT_DIR / "metrics_backend.json"
    backend_metrics_path.parent.mkdir(parents=True, exist_ok=True)
    if backend_metrics_path.exists():
        backend_metrics_path.unlink()

    cmd = [sys.executable, str(BACKEND_EVAL), "--json", str(backend_metrics_path)]
    for key, flag in (("min_accuracy", "--min-accuracy"),
                      ("min_recall", "--min-recall"),
                      ("max_fpr", "--max-fpr")):
        value = thresholds.get("backend", {}).get(key)
        if value is not None:
            cmd.extend([flag, str(value)])

    env = dict(os.environ)
    env["SCAMSHIELD_LOG_LEVEL"] = "WARNING"
    try:
        proc = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=1800)
    except Exception as exc:
        raise GateError(f"backend evaluation failed to run: {exc}") from exc

    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)

    if not backend_metrics_path.is_file():
        raise GateError(
            f"backend evaluation produced no metrics.json (exit={proc.returncode})"
        )
    try:
        with open(backend_metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    except Exception as exc:
        raise GateError(f"cannot parse backend metrics: {exc}") from exc

    return {
        "status": "ok",
        "exit_code": proc.returncode,
        "metrics_file": str(backend_metrics_path.relative_to(ROOT)).replace("\\", "/"),
        "metrics": {
            k: metrics.get(k)
            for k in ("accuracy", "precision", "recall", "f1", "fpr", "fnr",
                      "tp", "fp", "fn", "tn", "samples")
        },
        "per_language": metrics.get("per_language", {}),
        "raw_ml": metrics.get("raw_ml", {}),
    }


def parse_js_metrics(output: str) -> dict:
    patterns = {
        "accuracy": r"Accuracy:\s+([0-9.]+)",
        "precision": r"Precision:\s+([0-9.]+)",
        "recall": r"Recall:\s+([0-9.]+)",
        "f1": r"F1:\s+([0-9.]+)",
        "fpr": r"FPR:\s+([0-9.]+)",
        "fnr": r"FNR:\s+([0-9.]+)",
        "confusion": r"Confusion:\s+(TP=\d+\s+FP=\d+\s+FN=\d+\s+TN=\d+)",
        "samples": r"Samples:\s+(\d+)",
    }
    metrics = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, output)
        if match:
            metrics[key] = match.group(1) if key in ("confusion",) else float(match.group(1))
    if "confusion" in metrics:
        for part in metrics["confusion"].split():
            name, value = part.split("=")
            metrics[name.lower()] = int(value)
        del metrics["confusion"]
    missing = [k for k in ("accuracy", "recall", "fpr") if k not in metrics]
    if missing:
        raise GateError(f"could not parse JS eval output (missing {missing})")
    return metrics


def run_js(thresholds: dict) -> dict:
    node = shutil.which("node")
    if node is None:
        print("JS evaluation SKIPPED: node not found on PATH")
        return {"status": "skipped", "reason": "node not found on PATH"}
    try:
        proc = subprocess.run([node, str(JS_EVAL)], cwd=str(ROOT),
                              capture_output=True, text=True, timeout=1800)
    except Exception as exc:
        raise GateError(f"JS evaluation failed to run: {exc}") from exc
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.returncode != 0:
        raise GateError(f"JS evaluation exited {proc.returncode}: {proc.stderr[-2000:]}")
    metrics = parse_js_metrics(proc.stdout + proc.stderr)
    return {"status": "ok", "metrics": metrics}


def check(engine: str, metrics: dict, thresholds: dict) -> list:
    rows = []
    specs = (
        ("accuracy", "min_accuracy", ">=", "min"),
        ("recall", "min_recall", ">=", "min"),
        ("fpr", "max_fpr", "<=", "max"),
    )
    for metric, key, op, kind in specs:
        threshold = thresholds.get(key)
        if threshold is None:
            continue
        if metric not in metrics or metrics[metric] is None:
            raise GateError(f"{engine}: metric '{metric}' missing from results")
        actual = float(metrics[metric])
        passed = actual >= threshold if kind == "min" else actual <= threshold
        rows.append({
            "engine": engine,
            "metric": metric,
            "actual": round(actual, 4),
            "threshold": threshold,
            "operator": op,
            "passed": passed,
        })
    return rows


def print_table(rows: list, skipped: list) -> None:
    print("=" * 68)
    print("CI GOLD GATE")
    print("=" * 68)
    header = f"{'engine':8s} {'metric':10s} {'actual':>9s} {'operator':>9s} {'threshold':>10s}  result"
    print(header)
    print("-" * len(header))
    for row in rows:
        status = "PASS" if row["passed"] else "FAIL"
        print(f"{row['engine']:8s} {row['metric']:10s} {row['actual']:9.4f} "
              f"{row['operator']:>9s} {row['threshold']:10.4f}  {status}")
    for item in skipped:
        print(f"{item['engine']:8s} {'-':10s} {'-':>9s} {'':>9s} {'-':>10s}  SKIPPED ({item['reason']})")
    print("-" * len(header))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Gold-set regression gate for CI")
    parser.add_argument("--thresholds", default=str(THRESHOLDS_PATH),
                        help="Path to thresholds JSON")
    args = parser.parse_args(argv)

    try:
        thresholds = load_thresholds(Path(args.thresholds))
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

        backend = run_backend(thresholds["backend"])
        rows = check("backend", backend["metrics"], thresholds["backend"])

        skipped = []
        try:
            js = run_js(thresholds["js"])
        except GateError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            js = {"status": "error", "reason": str(exc)}
        if js["status"] == "ok":
            rows.extend(check("js", js["metrics"], thresholds["js"]))
        else:
            skipped.append({"engine": "js", "reason": js.get("reason", js["status"])})

        failed = [r for r in rows if not r["passed"]]
        js_error = js.get("status") == "error"

        report = {
            "thresholds_file": str(Path(args.thresholds)),
            "backend": backend,
            "js": js,
            "checks": rows,
            "skipped": skipped,
            "result": "FAIL" if (failed or js_error) else "PASS",
        }
        report_path = REPORT_DIR / "metrics.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report written to {report_path}")

        print_table(rows, skipped)
        if js_error:
            print("RESULT: ERROR (js evaluation failed)")
            return 2
        if failed:
            print(f"RESULT: FAIL ({len(failed)} threshold(s) breached)")
            return 1
        print("RESULT: PASS")
        return 0
    except GateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
