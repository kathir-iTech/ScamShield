import json
import os
from typing import Any, Dict, List, Optional, Tuple


def load_metrics(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def regression_check(
    previous: Dict[str, Any],
    current: Dict[str, Any],
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    if thresholds is None:
        thresholds = {
            "accuracy": 0.02,
            "precision": 0.02,
            "recall": 0.02,
            "f1": 0.02,
            "fp": 1,
            "fn": 1,
            "latency_ms": 50.0,
        }
    issues: List[str] = []
    passed = True

    for key in ("accuracy", "precision", "recall", "f1"):
        prev_val = previous.get(key, 0.0)
        curr_val = current.get(key, 0.0)
        drop = prev_val - curr_val
        threshold = thresholds.get(key, 0.02)
        if drop > threshold:
            passed = False
            issues.append(
                f"{key}: {prev_val:.4f} -> {curr_val:.4f} (drop of {drop:.4f}, "
                f"threshold: {threshold})"
            )

    prev_fp = previous.get("fp", 0)
    curr_fp = current.get("fp", 0)
    fp_increase = curr_fp - prev_fp
    if fp_increase > thresholds.get("fp", 1):
        passed = False
        issues.append(
            f"False Positives: {prev_fp} -> {curr_fp} (increase of {fp_increase}, "
            f"threshold: +{thresholds['fp']})"
        )

    prev_fn = previous.get("fn", 0)
    curr_fn = current.get("fn", 0)
    fn_increase = curr_fn - prev_fn
    if fn_increase > thresholds.get("fn", 1):
        passed = False
        issues.append(
            f"False Negatives: {prev_fn} -> {curr_fn} (increase of {fn_increase}, "
            f"threshold: +{thresholds['fn']})"
        )

    prev_latency = previous.get("p95_latency_ms", 0.0)
    curr_latency = current.get("p95_latency_ms", 0.0)
    latency_increase = curr_latency - prev_latency
    if latency_increase > thresholds.get("latency_ms", 50.0):
        passed = False
        issues.append(
            f"P95 Latency: {prev_latency:.1f}ms -> {curr_latency:.1f}ms "
            f"(increase of {latency_increase:.1f}ms, threshold: +{thresholds['latency_ms']}ms)"
        )

    return {"passed": passed, "issues": issues}


def _delta_cell(prev: float, curr: float, fmt: str = ".1%", invert: bool = False) -> str:
    delta = curr - prev
    if abs(delta) < 0.001:
        cls = ""
        arrow = ""
    elif (delta > 0 and not invert) or (delta < 0 and invert):
        cls = "good"
        arrow = "&#9650;"
    else:
        cls = "bad"
        arrow = "&#9660;"
    formatted_curr = f"{curr:{fmt}}" if fmt else str(curr)
    formatted_delta = f"{delta:+.1%}" if "%" in fmt else f"{delta:+.1f}"
    return f'<span class="{cls}">{formatted_curr} {arrow}</span> <span style="font-size:11px;color:#a1a1aa;">{formatted_delta}</span>'


def _delta_cell_count(prev: int, curr: int, invert: bool = False) -> str:
    delta = curr - prev
    if delta == 0:
        return f"<strong>{curr}</strong>"
    elif (delta < 0 and not invert) or (delta > 0 and invert):
        cls = "good"
        arrow = "&#9660;"
    else:
        cls = "bad"
        arrow = "&#9650;"
    return f'<span class="{cls}"><strong>{curr}</strong> {arrow} ({delta:+d})</span>'


def _delta_indicator(passed: bool) -> str:
    if passed:
        return '<span class="badge badge-success">PASSED</span>'
    return '<span class="badge badge-danger">FAILED</span>'


def generate_comparison_report(
    baseline: Dict[str, Any],
    current: Dict[str, Any],
    regression: Dict[str, Any],
    output_path: str,
) -> str:
    b = baseline.get("metrics", baseline)
    c = current.get("metrics", current)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ScamShield Refinement Comparison Report</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
       background:#fafafa; color:#18181b; padding:20px; }}
.container {{ max-width:960px; margin:0 auto; }}
h1 {{ font-size:24px; margin-bottom:4px; }}
h2 {{ font-size:18px; margin:24px 0 12px; padding-bottom:6px; border-bottom:2px solid #e4e4e7; }}
.card {{ background:white; border-radius:8px; padding:20px; margin:12px 0; box-shadow:0 1px 3px rgba(0,0,0,0.08); }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ padding:8px 12px; text-align:left; border-bottom:1px solid #e4e4e7; }}
th {{ background:#f4f4f5; font-weight:600; color:#52525b; }}
tr:hover {{ background:#fafafa; }}
.good {{ color:#16a34a; }} .bad {{ color:#dc2626; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; }}
.badge-danger {{ background:#fee2e2; color:#991b1b; }}
.badge-success {{ background:#dcfce7; color:#166534; }}
.badge-warning {{ background:#fef3c7; color:#92400e; }}
.summary-row {{ display:flex; gap:12px; flex-wrap:wrap; }}
.footer {{ margin-top:30px; padding-top:12px; border-top:1px solid #e4e4e7; font-size:11px; color:#a1a1aa; text-align:center; }}
</style>
</head>
<body>
<div class="container">

<h1>Refinement Engine: Before vs After Comparison</h1>
<p style="color:#71717a;margin-bottom:16px;">
  Baseline: {b.get('total_samples', 0)} samples | Current: {c.get('total_samples', 0)} samples
</p>

<div class="card">
<h2>Regression Safety Check</h2>
<p>Status: {_delta_indicator(regression.get('passed', False))}</p>
"""
    if regression.get("issues"):
        html += '<h3>Issues Found:</h3><ul>'
        for issue in regression["issues"]:
            html += f"<li>{issue}</li>"
        html += "</ul>"
    else:
        html += "<p>No regression detected. All metrics within thresholds.</p>"

    html += """</div>

<div class="card">
<h2>Key Metrics Comparison</h2>
<table>
<tr><th>Metric</th><th>Baseline</th><th>Current</th><th>Change</th></tr>
"""
    metrics_table = [
        ("Accuracy", b.get("accuracy", 0), c.get("accuracy", 0), ".1%", False),
        ("Precision", b.get("precision", 0), c.get("precision", 0), ".1%", False),
        ("Recall", b.get("recall", 0), c.get("recall", 0), ".1%", False),
        ("F1 Score", b.get("f1", 0), c.get("f1", 0), ".1%", False),
        ("False Positive Rate", b.get("false_positive_rate", 0), c.get("false_positive_rate", 0), ".1%", True),
        ("False Negative Rate", b.get("false_negative_rate", 0), c.get("false_negative_rate", 0), ".1%", True),
        ("Category Accuracy", b.get("category_accuracy", 0), c.get("category_accuracy", 0), ".1%", False),
        ("Risk Accuracy", b.get("risk_accuracy", 0), c.get("risk_accuracy", 0), ".1%", False),
        ("Assessment Accuracy", b.get("assessment_accuracy", 0), c.get("assessment_accuracy", 0), ".1%", False),
        ("Avg Confidence", b.get("average_confidence", 0), c.get("average_confidence", 0), ".1%", False),
    ]
    for label, prev_val, curr_val, fmt, invert in metrics_table:
        html += f"<tr><td>{label}</td><td>{prev_val:{fmt}}</td><td>{_delta_cell(prev_val, curr_val, fmt, invert)}</td><td>{curr_val - prev_val:+.1%}</td></tr>"

    html += f"""
<tr><td>Avg Inference (ms)</td><td>{b.get('average_inference_ms', 0):.1f}</td><td>{_delta_cell(b.get('average_inference_ms', 0), c.get('average_inference_ms', 0), '.1f', False)}</td><td>{c.get('average_inference_ms', 0) - b.get('average_inference_ms', 0):+.1f}</td></tr>
<tr><td>P95 Latency (ms)</td><td>{b.get('p95_latency_ms', 0):.1f}</td><td>{_delta_cell(b.get('p95_latency_ms', 0), c.get('p95_latency_ms', 0), '.1f', True)}</td><td>{c.get('p95_latency_ms', 0) - b.get('p95_latency_ms', 0):+.1f}</td></tr>
</table>
</div>

<div class="card">
<h2>Confusion Matrix Comparison</h2>
<table>
<tr><th>Cell</th><th>Baseline</th><th>Current</th><th>Change</th></tr>
"""
    cm_items = [
        ("True Positives", "tp", False),
        ("False Positives", "fp", True),
        ("False Negatives", "fn", True),
        ("True Negatives", "tn", False),
    ]
    for label, key, invert in cm_items:
        prev_val = b.get(key, 0)
        curr_val = c.get(key, 0)
        html += f"<tr><td>{label}</td><td>{prev_val}</td><td>{_delta_cell_count(prev_val, curr_val, invert)}</td><td>{curr_val - prev_val:+d}</td></tr>"

    html += "</table></div>"

    reg_issues = regression.get("issues", [])
    if reg_issues:
        html += '<div class="card"><h2>Issues Requiring Attention</h2><ul>'
        for issue in reg_issues:
            html += f"<li>{issue}</li>"
        html += "</ul></div>"

    html += """
<div class="footer">
  Generated by ScamShield Evaluation Framework |
  <span id="timestamp"></span>
</div>
</div>
<script>document.getElementById('timestamp').textContent = new Date().toISOString();</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def _svg_bar(label: str, value: float, max_val: float, color: str, width: int = 300) -> str:
    pct = (value / max_val * 100) if max_val > 0 else 0
    bar_w = max(int(pct * width / 100), 1)
    return (
        f'<div style="display:flex;align-items:center;margin:4px 0;font-size:13px;">'
        f'<span style="width:160px;text-align:right;padding-right:10px;color:#71717a;">{label}</span>'
        f'<div style="flex:1;height:22px;background:#e4e4e7;border-radius:4px;overflow:hidden;">'
        f'<div style="height:100%;width:{bar_w}px;background:{color};border-radius:4px;'
        f'display:flex;align-items:center;justify-content:center;min-width:30px;">'
        f'<span style="color:white;font-size:11px;font-weight:600;">{value}</span>'
        f'</div></div></div>'
    )


def _svg_hbar(
    labels: List[str], values: List[float], title: str, color: str, width: int = 600, height: int = 250,
) -> str:
    if not values:
        return "<p>No data</p>"
    max_v = max(values)
    bar_h = max(18, min(30, height // len(labels) - 4))
    svg_h = len(labels) * (bar_h + 8) + 40
    bars = []
    for i, (label, val) in enumerate(zip(labels, values)):
        bar_w = int((val / max_v) * (width - 160)) if max_v > 0 else 0
        y = 30 + i * (bar_h + 8)
        bars.append(
            f'<text x="5" y="{y + bar_h - 4}" font-size="12" fill="#52525b">{label}</text>'
            f'<rect x="155" y="{y}" width="{max(bar_w, 2)}" height="{bar_h}" '
            f'rx="3" fill="{color}" opacity="0.85"/>'
            f'<text x="{160 + max(bar_w, 2)}" y="{y + bar_h - 4}" font-size="11" fill="#18181b">'
            f'{val}</text>'
        )
    svg = [
        f'<svg width="{width}" height="{svg_h}" xmlns="http://www.w3.org/2000/svg">',
        f'<text x="5" y="18" font-size="14" font-weight="bold" fill="#18181b">{title}</text>',
        *bars,
        '</svg>',
    ]
    return '\n'.join(svg)


def _confusion_matrix_svg(tp: int, fp: int, fn: int, tn: int) -> str:
    total = tp + fp + fn + tn or 1
    svg = f'''<svg width="380" height="200" xmlns="http://www.w3.org/2000/svg">
  <text x="190" y="20" font-size="14" font-weight="bold" text-anchor="middle" fill="#18181b">Confusion Matrix</text>
  <text x="95" y="40" font-size="12" text-anchor="middle" fill="#71717a">Predicted: Safe</text>
  <text x="285" y="40" font-size="12" text-anchor="middle" fill="#71717a">Predicted: Scam</text>
  <text x="12" y="100" font-size="12" text-anchor="middle" fill="#71717a" transform="rotate(-90,12,100)">Actual: Safe</text>
  <text x="12" y="170" font-size="12" text-anchor="middle" fill="#71717a" transform="rotate(-90,12,170)">Actual: Scam</text>
  <rect x="60" y="55" width="140" height="70" rx="6" fill="#dcfce7" stroke="#86efac" stroke-width="2"/>
  <text x="130" y="90" font-size="28" font-weight="bold" text-anchor="middle" fill="#166534">{tn}</text>
  <text x="130" y="110" font-size="10" text-anchor="middle" fill="#166534">TN</text>
  <rect x="210" y="55" width="140" height="70" rx="6" fill="#fee2e2" stroke="#fca5a5" stroke-width="2"/>
  <text x="280" y="90" font-size="28" font-weight="bold" text-anchor="middle" fill="#991b1b">{fp}</text>
  <text x="280" y="110" font-size="10" text-anchor="middle" fill="#991b1b">FP</text>
  <rect x="60" y="130" width="140" height="70" rx="6" fill="#fee2e2" stroke="#fca5a5" stroke-width="2"/>
  <text x="130" y="165" font-size="28" font-weight="bold" text-anchor="middle" fill="#991b1b">{fn}</text>
  <text x="130" y="185" font-size="10" text-anchor="middle" fill="#991b1b">FN</text>
  <rect x="210" y="130" width="140" height="70" rx="6" fill="#dcfce7" stroke="#86efac" stroke-width="2"/>
  <text x="280" y="165" font-size="28" font-weight="bold" text-anchor="middle" fill="#166534">{tp}</text>
  <text x="280" y="185" font-size="10" text-anchor="middle" fill="#166534">TP</text>
</svg>'''
    return svg


def generate_html_report(
    metrics: Dict[str, Any],
    error_analysis: Dict[str, Any],
    confusion: Tuple[int, int, int, int],
    category_stats: List[Dict[str, Any]],
    samples: List[Dict[str, Any]],
    output_path: str,
    title: str = "ScamShield Evaluation Report",
) -> str:
    tp, fp, fn, tn = confusion
    total = tp + fp + fn + tn

    cat_labels = [c["category"] for c in category_stats]
    cat_acc = [c["accuracy"] for c in category_stats]
    cat_counts = [c["total"] for c in category_stats]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
       background:#fafafa; color:#18181b; padding:20px; }}
.container {{ max-width:960px; margin:0 auto; }}
h1 {{ font-size:24px; margin-bottom:4px; }}
h2 {{ font-size:18px; margin:24px 0 12px; padding-bottom:6px; border-bottom:2px solid #e4e4e7; }}
h3 {{ font-size:15px; margin:16px 0 8px; color:#3f3f46; }}
.card {{ background:white; border-radius:8px; padding:20px; margin:12px 0; box-shadow:0 1px 3px rgba(0,0,0,0.08); }}
.metric-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(130px,1fr)); gap:12px; }}
.metric {{ text-align:center; padding:12px; background:#f4f4f5; border-radius:6px; }}
.metric .value {{ font-size:28px; font-weight:700; color:#18181b; }}
.metric .label {{ font-size:11px; color:#71717a; text-transform:uppercase; letter-spacing:0.5px; }}
.metric .good {{ color:#16a34a; }} .metric .bad {{ color:#dc2626; }} .metric .warn {{ color:#f59e0b; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ padding:8px 12px; text-align:left; border-bottom:1px solid #e4e4e7; }}
th {{ background:#f4f4f5; font-weight:600; color:#52525b; }}
tr:hover {{ background:#fafafa; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; }}
.badge-danger {{ background:#fee2e2; color:#991b1b; }}
.badge-success {{ background:#dcfce7; color:#166534; }}
.badge-warning {{ background:#fef3c7; color:#92400e; }}
.summary-row {{ display:flex; gap:12px; flex-wrap:wrap; }}
.summary-item {{ flex:1; min-width:200px; }}
.footer {{ margin-top:30px; padding-top:12px; border-top:1px solid #e4e4e7; font-size:11px; color:#a1a1aa; text-align:center; }}
</style>
</head>
<body>
<div class="container">

<h1>{title}</h1>
<p style="color:#71717a;margin-bottom:16px;">
  {total} samples evaluated |
  {tp + tn} correct |
  {fp + fn} errors |
  Accuracy: {metrics.get('accuracy', 0):.1%}
</p>

<div class="card">
<h2>Overall Metrics</h2>
<div class="metric-grid">
  <div class="metric"><div class="value">{metrics.get('accuracy', 0):.1%}</div><div class="label">Accuracy</div></div>
  <div class="metric"><div class="value {('good' if metrics.get('precision', 0) > 0.8 else 'warn')}">{metrics.get('precision', 0):.1%}</div><div class="label">Precision</div></div>
  <div class="metric"><div class="value {('good' if metrics.get('recall', 0) > 0.8 else 'warn')}">{metrics.get('recall', 0):.1%}</div><div class="label">Recall</div></div>
  <div class="metric"><div class="value {('good' if metrics.get('f1', 0) > 0.8 else 'warn')}">{metrics.get('f1', 0):.1%}</div><div class="label">F1 Score</div></div>
  <div class="metric"><div class="value bad">{metrics.get('false_positive_rate', 0):.1%}</div><div class="label">False Positive Rate</div></div>
  <div class="metric"><div class="value bad">{metrics.get('false_negative_rate', 0):.1%}</div><div class="label">False Negative Rate</div></div>
  <div class="metric"><div class="value">{metrics.get('average_confidence', 0):.1%}</div><div class="label">Avg Confidence</div></div>
  <div class="metric"><div class="value">{metrics.get('average_inference_ms', 0):.1f}</div><div class="label">Avg Inference (ms)</div></div>
  <div class="metric"><div class="value">{metrics.get('p95_latency_ms', 0):.1f}</div><div class="label">P95 Latency (ms)</div></div>
  <div class="metric"><div class="value">{metrics.get('category_accuracy', 0):.1%}</div><div class="label">Category Accuracy</div></div>
  <div class="metric"><div class="value">{metrics.get('risk_accuracy', 0):.1%}</div><div class="label">Risk Level Accuracy</div></div>
  <div class="metric"><div class="value">{metrics.get('assessment_accuracy', 0):.1%}</div><div class="label">Assessment Accuracy</div></div>
</div>
</div>

<div class="card">
{_confusion_matrix_svg(tp, fp, fn, tn)}
</div>

<div class="card">
<h2>Per-Category Accuracy</h2>
{_svg_hbar(cat_labels, [c * 100 for c in cat_acc], 'Accuracy by Category (%)', '#22c55e', width=600, height=len(cat_labels) * 28 + 40)}
</div>

<div class="card">
<h2>Category Sample Counts</h2>
{_svg_hbar(cat_labels, cat_counts, 'Samples per Category', '#3b82f6', width=600, height=len(cat_labels) * 28 + 40)}
</div>

<div class="card">
<h2>Error Analysis</h2>
<div class="summary-row">
  <div class="summary-item">
    <h3>Summary</h3>
    <table>
      <tr><td>False Positives</td><td><strong>{error_analysis.get('fp_count', 0)}</strong></td></tr>
      <tr><td>False Negatives</td><td><strong>{error_analysis.get('fn_count', 0)}</strong></td></tr>
      <tr><td>Wrong Category</td><td><strong>{error_analysis.get('wc_count', 0)}</strong></td></tr>
      <tr><td>Low Confidence</td><td><strong>{error_analysis.get('lc_count', 0)}</strong></td></tr>
      <tr><td>Entity Extraction Failures</td><td><strong>{error_analysis.get('ef_count', 0)}</strong></td></tr>
    </table>
  </div>
</div>
</div>
"""

    if error_analysis.get("false_positives"):
        html += '<div class="card"><h2>False Positives (Safe classified as Scam)</h2><table><tr><th>ID</th><th>Text</th><th>Confidence</th><th>Difficulty</th></tr>'
        for fp_item in error_analysis["false_positives"][:15]:
            html += f'<tr><td>{fp_item["id"]}</td><td style="max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{fp_item["text"]}</td><td>{fp_item["confidence"]:.1%}</td><td>{fp_item["difficulty"]}</td></tr>'
        html += "</table></div>"

    if error_analysis.get("false_negatives"):
        html += '<div class="card"><h2>False Negatives (Scam classified as Safe)</h2><table><tr><th>ID</th><th>Text</th><th>Confidence</th><th>Difficulty</th></tr>'
        for fn_item in error_analysis["false_negatives"][:15]:
            html += f'<tr><td>{fn_item["id"]}</td><td style="max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{fn_item["text"]}</td><td>{fn_item["confidence"]:.1%}</td><td>{fn_item["difficulty"]}</td></tr>'
        html += "</table></div>"

    html += """
<div class="footer">
  Generated by ScamShield Evaluation Framework |
  <span id="timestamp"></span>
</div>
</div>
<script>document.getElementById('timestamp').textContent = new Date().toISOString();</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path
