from __future__ import annotations

import json
import time
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple

import numpy as np

from ..config.evaluation_config import EvaluationConfig, DEFAULT_METRICS, ALL_CATEGORIES
from ..config.dataset_schema import validate_dataset
from .dataset_utils import load_dataset_json, load_dataset_csv
from .evaluation_metrics import (
    EvaluationMetrics,
    compute_calibration,
    compute_roc_curve,
    compute_pr_curve,
    find_optimal_threshold,
    regression_check,
    format_metrics_table,
)
from .error_analysis import analyze_errors, generate_error_report, profile_failure_patterns, find_ambiguous_samples, category_confusion_matrix


def _load_dataset(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".json":
        return load_dataset_json(path)
    elif suffix == ".csv":
        return load_dataset_csv(path)
    else:
        raise ValueError(f"Unsupported dataset format: {suffix}. Use .json or .csv")


def evaluate_model(
    model_fn: Callable[[str], Dict[str, Any]],
    dataset_path: str,
    output_dir: str = "reports",
    config: Optional[EvaluationConfig] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    if config is None:
        config = EvaluationConfig()

    samples = _load_dataset(dataset_path)
    if not samples:
        raise ValueError(f"No samples found in {dataset_path}")

    is_valid, errors = validate_dataset(samples)
    if not is_valid:
        if verbose:
            print(f"Warning: dataset has {len(errors)} validation errors")
            for e in errors[:20]:
                print(f"  {e}")

    y_true: List[int] = []
    y_pred: List[int] = []
    y_scores: List[float] = []
    categories: List[str] = []
    sample_ids: List[str] = []
    raw_predictions: List[Dict[str, Any]] = []

    start_time = time.time()
    for i, sample in enumerate(samples):
        text = sample.get("text_clean") or sample.get("text", "")
        if not text:
            continue

        try:
            result = model_fn(text)
        except Exception as e:
            if verbose:
                print(f"Error processing sample {i}: {e}")
            result = {"prediction": "safe", "confidence": 0.0, "category": "UNKNOWN"}

        pred_label = result.get("prediction", "safe")
        confidence = result.get("confidence", 0.5)
        pred_category = result.get("category", "UNKNOWN")

        true_is_scam = sample.get("is_scam", False)
        gt_label = sample.get("ground_truth_label", "")

        y_true.append(1 if true_is_scam else 0)
        y_pred.append(1 if pred_label == "scam" else 0)
        y_scores.append(confidence)
        categories.append(sample.get("category", "UNKNOWN"))
        sample_ids.append(sample.get("id", str(i)))
        raw_predictions.append(result)

    elapsed = time.time() - start_time

    y_true_arr = np.array(y_true, dtype=int)
    y_pred_arr = np.array(y_pred, dtype=int)
    y_scores_arr = np.array(y_scores, dtype=float)

    metrics = EvaluationMetrics(
        y_true=y_true.tolist(),
        y_pred=y_pred.tolist(),
        y_scores=y_scores.tolist(),
        categories=["legitimate", "scam"],
    )

    per_cat = metrics.per_category_metrics(
        y_true=y_true.tolist(),
        y_pred=y_pred.tolist(),
        categories=categories,
    )

    roc_data = compute_roc_curve(y_true.tolist(), y_scores)
    pr_data = compute_pr_curve(y_true.tolist(), y_scores)
    calib_data = compute_calibration(y_true.tolist(), y_scores, n_bins=10)
    opt_thresh = find_optimal_threshold(y_true.tolist(), y_scores, metric="f1")

    error_analysis = analyze_errors(samples, raw_predictions)
    failure_profile = profile_failure_patterns(
        error_analysis.get("fp_details", []),
        error_analysis.get("fn_details", []),
        error_analysis.get("wrong_category_details", []),
    )
    ambiguous = find_ambiguous_samples(samples, raw_predictions)
    cat_confusion = category_confusion_matrix(samples, raw_predictions)

    result: Dict[str, Any] = {
        "evaluation_id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "path": str(Path(dataset_path).resolve()),
            "num_samples": len(samples),
            "num_valid": len(y_true),
            "validation_errors": len(errors),
        },
        "config": config.to_dict(),
        "performance": {
            "inference_time_seconds": round(elapsed, 4),
            "samples_per_second": round(len(y_true) / elapsed, 2) if elapsed > 0 else 0.0,
            "throughput": f"{round(len(y_true) / elapsed, 2)} samples/s" if elapsed > 0 else "N/A",
        },
        "metrics": metrics.to_dict(),
        "per_category_metrics": per_cat,
        "roc_curve": roc_data,
        "pr_curve": pr_data,
        "calibration": calib_data,
        "optimal_threshold": opt_thresh,
        "error_analysis": {
            "summary": {
                "total": error_analysis["total_samples"],
                "correct": error_analysis["correct"],
                "incorrect": error_analysis["incorrect"],
                "accuracy": error_analysis["accuracy"],
                "false_positives": error_analysis["false_positives"],
                "false_negatives": error_analysis["false_negatives"],
                "wrong_category": error_analysis["wrong_category_count"],
                "wrong_risk_level": error_analysis["wrong_risk_level_count"],
            },
            "failure_profile": failure_profile,
            "ambiguous_samples": len(ambiguous),
            "confusion_matrix": metrics.confusion_matrix(),
            "category_confusion_matrix": cat_confusion,
        },
        "raw_predictions_sample": raw_predictions[:10],
    }

    if verbose:
        print(metrics.summary())
        print()
        print(format_metrics_table(metrics.to_dict()))

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    save_path = save_results(result, output_dir)
    _ = generate_report(result, str(Path(output_dir) / "report.html"))

    return result


def evaluate_multiple(
    models: Dict[str, Callable[[str], Dict[str, Any]]],
    dataset_path: str,
    output_dir: str = "reports",
    config: Optional[EvaluationConfig] = None,
    verbose: bool = False,
) -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}
    for name, model_fn in models.items():
        if verbose:
            print(f"\n{'='*60}")
            print(f"Evaluating model: {name}")
            print(f"{'='*60}")
        model_output = str(Path(output_dir) / name)
        results[name] = evaluate_model(
            model_fn=model_fn,
            dataset_path=dataset_path,
            output_dir=model_output,
            config=config,
            verbose=verbose,
        )

    comparison = compare_results(results)
    cmp_path = Path(output_dir) / "comparison.json"
    cmp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cmp_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    cmp_html_path = Path(output_dir) / "comparison.html"
    html = _generate_comparison_html(comparison)
    with open(cmp_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    if verbose:
        print(f"\nComparison saved to {cmp_path}")
        print(comparison.get("comparison_table", ""))

    return results


def compare_results(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if not results:
        return {"error": "No results to compare"}

    metrics_keys = [
        "accuracy", "precision", "recall", "f1", "fpr", "fnr",
        "auc", "mcc", "balanced_accuracy",
    ]

    comparison: Dict[str, Any] = {
        "models": list(results.keys()),
        "metrics": {},
        "best_model": {},
        "rankings": {},
        "comparison_table": "",
    }

    for metric in metrics_keys:
        vals: Dict[str, float] = {}
        for name, result in results.items():
            m = result.get("metrics", {})
            if metric in m:
                vals[name] = m[metric]
        if vals:
            comparison["metrics"][metric] = vals

    for metric in metrics_keys:
        vals = comparison["metrics"].get(metric, {})
        if not vals:
            continue
        higher_better = metric not in ("fpr", "fnr")
        if higher_better:
            best_name = max(vals, key=vals.get)
            best_val = vals[best_name]
        else:
            best_name = min(vals, key=vals.get)
            best_val = vals[best_name]
        comparison["best_model"][metric] = {"model": best_name, "value": best_val}

    perf_scores: Dict[str, float] = {}
    for name in results:
        score = 0.0
        count = 0
        m = results[name].get("metrics", {})
        for metric in metrics_keys:
            if metric not in m:
                continue
            vals = comparison["metrics"].get(metric, {})
            if not vals:
                continue
            higher_better = metric not in ("fpr", "fnr")
            min_v = min(vals.values())
            max_v = max(vals.values())
            if max_v == min_v:
                norm = 0.5
            else:
                norm = (m[metric] - min_v) / (max_v - min_v)
                if not higher_better:
                    norm = 1.0 - norm
            score += norm
            count += 1
        perf_scores[name] = round(score / count, 4) if count > 0 else 0.0

    ranked = sorted(perf_scores.items(), key=lambda x: x[1], reverse=True)
    comparison["rankings"] = {
        name: {"rank": i + 1, "score": score}
        for i, (name, score) in enumerate(ranked)
    }

    header = f"{'Model':<20s}" + "".join(f"{m:>12s}" for m in metrics_keys)
    sep = "-" * len(header)
    rows = [header, sep]
    for name, _ in ranked:
        row = f"{name:<20s}"
        m = results[name].get("metrics", {})
        for mk in metrics_keys:
            val = m.get(mk)
            if val is not None:
                row += f"{val:>12.4f}"
            else:
                row += f"{'N/A':>12s}"
        rows.append(row)
    rows.append(sep)
    rows.append(f"{'Ranking':<20s}" + "".join(
        f"{perf_scores.get(name, 0):>12.4f}" for name, _ in ranked
    ))

    comparison["comparison_table"] = "\n".join(rows)

    return comparison


def generate_report(result: Dict[str, Any], output_path: str) -> str:
    metrics = result.get("metrics", {})
    perf = result.get("performance", {})
    ds = result.get("dataset", {})

    cm = metrics.get("confusion_matrix", [[0, 0], [0, 0]])
    error_summary = result.get("error_analysis", {}).get("summary", {})

    calibrations = result.get("calibration", {})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ScamShield v2 Evaluation Report</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
  h1, h2, h3 {{ color: #1a1a2e; }}
  .card {{ background: white; border-radius: 8px; padding: 20px; margin: 16px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
  .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }}
  .metric {{ text-align: center; padding: 12px; background: #f8f9fa; border-radius: 6px; }}
  .metric .value {{ font-size: 24px; font-weight: bold; color: #0d6efd; }}
  .metric .label {{ font-size: 12px; color: #6c757d; text-transform: uppercase; }}
  .confusion {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; max-width: 300px; margin: 0 auto; }}
  .confusion-cell {{ padding: 16px; text-align: center; font-weight: bold; border-radius: 4px; }}
  .confusion-tn {{ background: #d4edda; color: #155724; }}
  .confusion-fp {{ background: #f8d7da; color: #721c24; }}
  .confusion-fn {{ background: #fff3cd; color: #856404; }}
  .confusion-tp {{ background: #cce5ff; color: #004085; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
  th {{ background: #f8f9fa; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
  .badge-pass {{ background: #d4edda; color: #155724; }}
  .badge-fail {{ background: #f8d7da; color: #721c24; }}
</style>
</head>
<body>
<h1>🛡️ ScamShield v2 — Evaluation Report</h1>

<div class="card">
  <h2>Dataset Overview</h2>
  <table>
    <tr><th>Property</th><th>Value</th></tr>
    <tr><td>Path</td><td>{ds.get('path', 'N/A')}</td></tr>
    <tr><td>Total Samples</td><td>{ds.get('num_samples', 0)}</td></tr>
    <tr><td>Valid Samples</td><td>{ds.get('num_valid', 0)}</td></tr>
    <tr><td>Validation Errors</td><td>{ds.get('validation_errors', 0)}</td></tr>
    <tr><td>Evaluation ID</td><td>{result.get('evaluation_id', 'N/A')}</td></tr>
    <tr><td>Timestamp</td><td>{result.get('timestamp', 'N/A')}</td></tr>
  </table>
</div>

<div class="card">
  <h2>Performance</h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Inference Time</td><td>{perf.get('inference_time_seconds', 'N/A')}s</td></tr>
    <tr><td>Throughput</td><td>{perf.get('throughput', 'N/A')}</td></tr>
    <tr><td>Samples / Second</td><td>{perf.get('samples_per_second', 0)}</td></tr>
  </table>
</div>

<div class="card">
  <h2>Overall Metrics</h2>
  <div class="metric-grid">
"""
    key_labels = {
        "accuracy": "Accuracy", "precision": "Precision", "recall": "Recall",
        "f1": "F1 Score", "fpr": "False Positive Rate", "fnr": "False Negative Rate",
        "auc": "AUC-ROC", "mcc": "Matthews Corr.", "balanced_accuracy": "Balanced Acc.",
    }
    for key, label in key_labels.items():
        val = metrics.get(key)
        if val is not None:
            html += f'    <div class="metric"><div class="value">{val:.4f}</div><div class="label">{label}</div></div>\n'

    html += """  </div>
</div>

<div class="card">
  <h2>Confusion Matrix</h2>
  <div class="confusion">
    <div class="confusion-cell confusion-tn">TN<br>{}</div>
    <div class="confusion-cell confusion-fp">FP<br>{}</div>
    <div class="confusion-cell confusion-fn">FN<br>{}</div>
    <div class="confusion-cell confusion-tp">TP<br>{}</div>
  </div>
</div>

<div class="card">
  <h2>Error Analysis</h2>
  <div class="metric-grid">
    <div class="metric"><div class="value">{:.1%}</div><div class="label">Accuracy</div></div>
    <div class="metric"><div class="value">{}</div><div class="label">Correct</div></div>
    <div class="metric"><div class="value">{}</div><div class="label">Incorrect</div></div>
    <div class="metric"><div class="value" style="color:#dc3545">{}</div><div class="label">False Positives</div></div>
    <div class="metric"><div class="value" style="color:#dc3545">{}</div><div class="label">False Negatives</div></div>
    <div class="metric"><div class="value" style="color:#ffc107">{}</div><div class="label">Wrong Category</div></div>
  </div>
</div>

<div class="card">
  <h2>Calibration (ECE: {:.4f})</h2>
  <table>
    <tr><th>Bin</th><th>Confidence</th><th>Accuracy</th><th>Count</th><th>Gap</th></tr>
""".format(
        cm[0][0], cm[0][1], cm[1][0], cm[1][1],
        error_summary.get("accuracy", 0),
        error_summary.get("correct", 0),
        error_summary.get("incorrect", 0),
        error_summary.get("false_positives", 0),
        error_summary.get("false_negatives", 0),
        error_summary.get("wrong_category", 0),
        calibrations.get("ece", 0),
    )

    bins = calibrations.get("bins", [])
    accs = calibrations.get("accuracy", [])
    confs = calibrations.get("confidence", [])
    counts = calibrations.get("counts", [])
    for i in range(len(bins) - 1):
        if i < len(accs) and i < len(confs) and i < len(counts):
            gap = abs(confs[i] - accs[i])
            html += f"    <tr><td>[{bins[i]:.2f}, {bins[i+1]:.2f})</td><td>{confs[i]:.4f}</td><td>{accs[i]:.4f}</td><td>{int(counts[i])}</td><td>{gap:.4f}</td></tr>\n"

    html += """  </table>
</div>

<div class="card">
  <h2>Optimal Threshold</h2>
  <table>
    <tr><th>Metric</th><th>Optimal Threshold</th><th>Value at Threshold</th></tr>
"""
    ot = result.get("optimal_threshold", {})
    html += f'    <tr><td>{ot.get("metric", "f1").upper()}</td><td>{ot.get("threshold", 0.5):.4f}</td><td>{ot.get("metric_value", 0):.4f}</td></tr>\n'

    html += """  </table>
</div>

<div class="card">
  <h2>Per-Category Metrics</h2>
  <table>
    <tr><th>Category</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr>
"""
    per_cat = result.get("per_category_metrics", {})
    for cat in ALL_CATEGORIES:
        if cat in per_cat:
            cm = per_cat[cat]
            sup = cm.get("tp", 0) + cm.get("fn", 0)
            html += f'    <tr><td>{cat}</td><td>{cm.get("precision", 0):.4f}</td><td>{cm.get("recall", 0):.4f}</td><td>{cm.get("f1", 0):.4f}</td><td>{sup}</td></tr>\n'

    html += """  </table>
</div>

</body>
</html>"""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return html


def _generate_comparison_html(comparison: Dict[str, Any]) -> str:
    models = comparison.get("models", [])
    metrics_data = comparison.get("metrics", {})
    rankings = comparison.get("rankings", {})

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ScamShield v2 — Model Comparison</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
  h1 {{ color: #1a1a2e; }}
  .card {{ background: white; border-radius: 8px; padding: 20px; margin: 16px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #dee2e6; }}
  th {{ background: #f8f9fa; font-weight: 600; }}
  tr:hover {{ background: #f1f3f5; }}
  .best {{ background: #d4edda !important; font-weight: bold; }}
  .rank-1 {{ background: #fff3cd; }}
</style>
</head>
<body>
<h1>🛡️ ScamShield v2 — Model Comparison</h1>

<div class="card">
  <h2>Metrics Comparison</h2>
  <table>
    <tr><th>Model</th><th>Rank</th>
"""

    metric_keys = list(metrics_data.keys())
    for mk in metric_keys:
        html += f"<th>{mk.upper()}</th>"
    html += "</tr>\n"

    ranked_models = sorted(rankings.keys(), key=lambda x: rankings[x]["rank"])
    for model in ranked_models:
        rank = rankings[model]["score"]
        cls = "rank-1" if rankings[model]["rank"] == 1 else ""
        html += f'    <tr class="{cls}"><td>{model}</td><td>{rankings[model]["rank"]} ({rankings[model]["score"]:.4f})</td>'
        for mk in metric_keys:
            vals = metrics_data[mk]
            val = vals.get(model, "N/A")
            if val != "N/A":
                higher_better = mk not in ("fpr", "fnr")
                cell_class = ""
                if higher_better and val == max(vals.values()):
                    cell_class = ' class="best"'
                elif not higher_better and val == min(vals.values()):
                    cell_class = ' class="best"'
                html += f'<td{cell_class}>{val:.4f}</td>'
            else:
                html += "<td>N/A</td>"
        html += "</tr>\n"

    html += """  </table>
</div>

<div class="card">
  <h2>Best Model Per Metric</h2>
  <table>
    <tr><th>Metric</th><th>Best Model</th><th>Value</th></tr>
"""
    best = comparison.get("best_model", {})
    for mk, data in best.items():
        html += f'    <tr><td>{mk.upper()}</td><td><strong>{data.get("model", "N/A")}</strong></td><td>{data.get("value", 0):.4f}</td></tr>\n'

    html += """  </table>
</div>

</body>
</html>"""

    return html


def save_results(result: Dict[str, Any], output_dir: str) -> str:
    p = Path(output_dir) / "json"
    p.mkdir(parents=True, exist_ok=True)

    eval_id = result.get("evaluation_id", "unknown")
    path = p / f"evaluation_{eval_id}.json"

    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)

    return str(path)
