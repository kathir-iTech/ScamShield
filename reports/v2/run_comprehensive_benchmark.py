import csv
import json
import logging
import os
import sys
import time
import collections
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    precision_recall_curve, matthews_corrcoef, balanced_accuracy_score,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("benchmark")

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent.parent / "benchmarks" / "v2"
SCRIPTS_DIR = BENCHMARKS_DIR / "scripts"
sys.path.insert(0, str(BENCHMARKS_DIR.parent.parent))

from benchmarks.v2.scripts.models import (
    train_tfidf_lr, train_tfidf_svm, train_embedding_model, train_transformer,
    ModelWrapper, create_model
)
from benchmarks.v2.scripts.evaluation_metrics import (
    EvaluationMetrics, compute_calibration, compute_roc_curve, compute_pr_curve,
    find_optimal_threshold, format_metrics_table,
)
from benchmarks.v2.scripts.error_analysis import (
    analyze_errors, profile_failure_patterns, generate_error_report,
    find_ambiguous_samples, category_confusion_matrix,
)

SEED = 42
RESULTS_DIR = Path(__file__).resolve().parent
MAIN_DATASET = RESULTS_DIR.parent.parent / "backend" / "data" / "scam_dataset.csv"
V2_ALPHA = RESULTS_DIR.parent.parent / "datasets" / "v2" / "annotated" / "dataset_v2_alpha.csv"

MODEL_TYPES = ["tfidf_lr", "tfidf_svm", "embedding", "transformer"]


def load_main_dataset(path: str) -> Tuple[List[str], List[int]]:
    texts, labels = [], []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row.get("text", ""))
            labels.append(1 if row.get("label", "").strip().lower() == "scam" else 0)
    logger.info("Main dataset: %d samples (%d scam, %d safe)", len(texts), sum(labels), len(labels) - sum(labels))
    return texts, labels


def load_v2_alpha(path: str) -> Tuple[List[str], List[int], List[str]]:
    texts, labels, categories = [], [], []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("text_clean") or row.get("text", "")
            texts.append(text)
            is_scam = row.get("is_scam", "False").strip().lower() in ("true", "1", "yes")
            labels.append(1 if is_scam else 0)
            categories.append(row.get("category", "UNKNOWN").strip())
    logger.info("V2 alpha dataset: %d samples (%d scam, %d safe, %d categories)",
                len(texts), sum(labels), len(labels) - sum(labels), len(set(categories)))
    return texts, labels, categories


def train_evaluate_model(model_type: str, train_texts: List[str], train_labels: List[int],
                         eval_texts: List[str], eval_labels: List[int],
                         eval_categories: List[str]) -> Dict[str, Any]:
    logger.info("=" * 60)
    logger.info("Training: %s", model_type)
    logger.info("=" * 60)

    t0 = time.time()
    if model_type == "tfidf_lr":
        vec, model = train_tfidf_lr(train_texts, train_labels, max_features=5000)
        wrapper = ModelWrapper(model, vectorizer=vec)
    elif model_type == "tfidf_svm":
        vec, model = train_tfidf_svm(train_texts, train_labels, max_features=5000)
        wrapper = ModelWrapper(model, vectorizer=vec)
    elif model_type == "embedding":
        result = train_embedding_model(train_texts, train_labels, model_name="all-MiniLM-L6-v2")
        if len(result) == 3:
            embedder, scaler, classifier = result
            wrapper = ModelWrapper(classifier, vectorizer=None)
            wrapper._embedder = embedder
            wrapper._scaler = scaler
        else:
            vec, model = result
            wrapper = ModelWrapper(model, vectorizer=vec)
    elif model_type == "transformer":
        result = train_transformer(train_texts, train_labels, model_name="distilbert-base-uncased")
        if len(result) == 2 and hasattr(result[0], "vocab_size"):
            tokenizer, model = result
            wrapper = ModelWrapper(model, vectorizer=None)
            wrapper._tokenizer = tokenizer
            wrapper._is_transformer = True
        else:
            vec, model = result
            wrapper = ModelWrapper(model, vectorizer=vec)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    train_time = time.time() - t0

    logger.info("Evaluating %s on v2 alpha (%d samples)...", model_type, len(eval_texts))

    t1 = time.time()
    y_pred, y_scores, y_true = [], [], []
    raw_preds = []

    for text, true_label in zip(eval_texts, eval_labels):
        result = wrapper.predict(text)
        pred = 1 if result["prediction"] == "scam" else 0
        confidence = result.get("confidence", 0.5)
        y_pred.append(pred)
        y_scores.append(confidence)
        y_true.append(true_label)
        raw_preds.append(result)
    eval_time = time.time() - t1

    opt_thresh = find_optimal_threshold(y_true, y_scores, metric="f1")
    wrapper.threshold = opt_thresh["threshold"]

    y_pred_opt = [1 if p >= wrapper.threshold else 0 for p in y_scores]

    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred_opt)

    tn, fp, fn, tp = confusion_matrix(y_true_arr, y_pred_arr).ravel()
    overall = {
        "total": len(y_true),
        "accuracy": float(accuracy_score(y_true_arr, y_pred_arr)),
        "precision": float(precision_score(y_true_arr, y_pred_arr, zero_division=0)),
        "recall": float(recall_score(y_true_arr, y_pred_arr, zero_division=0)),
        "f1": float(f1_score(y_true_arr, y_pred_arr, zero_division=0)),
        "specificity": float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0,
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0,
        "false_negative_rate": float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0,
        "mcc": float(matthews_corrcoef(y_true_arr, y_pred_arr)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true_arr, y_pred_arr)),
        "roc_auc": float(roc_auc_score(y_true_arr, y_scores)) if len(np.unique(y_true)) > 1 else 0.0,
        "confusion_matrix": {"tp": int(tp), "fn": int(fn), "fp": int(fp), "tn": int(tn)},
    }

    unique_cats = sorted(set(eval_categories))
    per_category = {}
    for cat in unique_cats:
        mask = [c == cat for c in eval_categories]
        cat_true = [y_true[i] for i, m in enumerate(mask) if m]
        cat_pred = [y_pred_opt[i] for i, m in enumerate(mask) if m]
        if len(cat_true) == 0:
            continue
        cat_tn, cat_fp, cat_fn, cat_tp = confusion_matrix(cat_true, cat_pred, labels=[0, 1]).ravel()
        per_category[cat] = {
            "total": len(cat_true),
            "accuracy": float(accuracy_score(cat_true, cat_pred)),
            "precision": float(precision_score(cat_true, cat_pred, zero_division=0)),
            "recall": float(recall_score(cat_true, cat_pred, zero_division=0)),
            "f1": float(f1_score(cat_true, cat_pred, zero_division=0)),
            "tp": int(cat_tp), "fn": int(cat_fn), "fp": int(cat_fp), "tn": int(cat_tn),
        }

    roc_data = compute_roc_curve(y_true, y_scores)
    pr_data = compute_pr_curve(y_true, y_scores)
    calib_data = compute_calibration(y_true, y_scores, n_bins=10)

    samples_for_error = [{"text": t, "text_clean": t, "category": c, "is_scam": bool(l),
                          "ground_truth_label": "scam" if l else "legitimate", "risk_level": "HIGH" if l else "NONE"}
                         for t, c, l in zip(eval_texts, eval_categories, y_true)]
    preds_for_error = [{"prediction": "scam" if p else "safe", "confidence": s}
                       for p, s in zip(y_pred_opt, y_scores)]

    error_analysis = analyze_errors(samples_for_error, preds_for_error)
    failure_profile = profile_failure_patterns(
        error_analysis.get("fp_details", []),
        error_analysis.get("fn_details", []),
        error_analysis.get("wrong_category_details", []),
    )
    cat_confusion = category_confusion_matrix(samples_for_error, preds_for_error)

    result = {
        "model_type": model_type,
        "train_time_seconds": round(train_time, 2),
        "eval_time_seconds": round(eval_time, 4),
        "throughput_samples_per_sec": round(len(eval_texts) / eval_time, 2) if eval_time > 0 else 0,
        "optimal_threshold": opt_thresh,
        "overall": overall,
        "per_category": per_category,
        "roc_curve": roc_data,
        "pr_curve": pr_data,
        "calibration": calib_data,
        "error_analysis": {
            "summary": {
                "total": error_analysis["total_samples"],
                "correct": error_analysis["correct"],
                "incorrect": error_analysis["incorrect"],
                "accuracy": error_analysis["accuracy"],
                "false_positives": error_analysis["false_positives"],
                "false_negatives": error_analysis["false_negatives"],
            },
            "failure_profile": failure_profile,
            "ambiguous_samples": len(find_ambiguous_samples(samples_for_error, preds_for_error)),
        },
    }

    return result


def generate_markdown_report(all_results: Dict[str, Dict], results_dir: Path):
    (results_dir / "reports").mkdir(parents=True, exist_ok=True)

    models = sorted(all_results.keys())

    def _fmt(v, d=4):
        return f"{v:.{d}f}"

    # ============================
    # 1. MODEL_COMPARISON.md
    # ============================
    metrics_keys = ["accuracy", "precision", "recall", "f1", "mcc", "balanced_accuracy", "roc_auc", "false_positive_rate", "false_negative_rate"]
    header = ["Model"] + [m.replace("_", " ").title() for m in metrics_keys] + ["Train Time", "Eval Time", "Throughput"]
    sep_line = "| " + " | ".join(h.center(18) for h in header) + " |"
    border = "| " + " | ".join(":------------------:" for _ in header) + " |"

    lines = ["# Model Comparison Report", ""]
    lines.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Training Data:** `backend/data/scam_dataset.csv` (5,715 samples, 15.5% scam)")
    lines.append(f"**Evaluation Data:** `datasets/v2/annotated/dataset_v2_alpha.csv` (558 samples, 470 scam, 88 legit)")
    lines.append(f"**Seed:** 42")
    lines.append("")
    lines.append("## Overall Metrics Comparison")
    lines.append("")
    lines.append(sep_line)
    lines.append(border)
    for m in models:
        r = all_results[m]
        o = r["overall"]
        vals = [_fmt(o.get(k, 0)) for k in metrics_keys]
        vals += [_fmt(r["train_time_seconds"], 1) + "s", _fmt(r["eval_time_seconds"], 3) + "s",
                 _fmt(r["throughput_samples_per_sec"], 1) + "/s"]
        row = "| " + f"`{m}`".ljust(18) + " | " + " | ".join(v.center(18) for v in vals) + " |"
        lines.append(row)
    lines.append("")

    lines.append("## Confusion Matrices")
    lines.append("")
    lines.append("| " + "Model".center(18) + " | " + "TP".center(8) + " | " + "FN".center(8) + " | " + "FP".center(8) + " | " + "TN".center(8) + " |")
    lines.append("| " + ":------------------: | " + ":------:" + " | " + ":------:" + " | " + ":------:" + " | " + ":------:" + " |")
    for m in models:
        cm = all_results[m]["overall"]["confusion_matrix"]
        lines.append("| " + f"`{m}`".ljust(18) + " | " + str(cm["tp"]).center(8) + " | " + str(cm["fn"]).center(8) + " | " + str(cm["fp"]).center(8) + " | " + str(cm["tn"]).center(8) + " |")
    lines.append("")

    lines.append("## Per-Category Performance (F1 Score)")
    lines.append("")
    all_cats = set()
    for m in models:
        all_cats.update(all_results[m]["per_category"].keys())
    all_cats = sorted(all_cats)

    cat_header = ["Category"] + [f"`{m}`" for m in models] + ["Best Model"]
    cat_sep = "| " + " | ".join(":------------------:" for _ in cat_header) + " |"
    lines.append("| " + " | ".join(h.center(18) for h in cat_header) + " |")
    lines.append(cat_sep)
    for cat in all_cats:
        row_vals = []
        best_f1 = -1
        best_m = ""
        for m in models:
            pc = all_results[m]["per_category"].get(cat, {})
            f1_val = pc.get("f1", -1)
            row_vals.append(_fmt(f1_val) if f1_val >= 0 else "N/A")
            if f1_val > best_f1:
                best_f1 = f1_val
                best_m = m
        row_vals.append(f"`{best_m}`" if best_f1 >= 0 else "N/A")
        lines.append("| " + cat.ljust(18) + " | " + " | ".join(v.center(18) for v in row_vals) + " |")
    lines.append("")

    mc_path = results_dir / "reports" / "MODEL_COMPARISON.md"
    mc_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Written: %s", mc_path)

    # ============================
    # 2. BENCHMARK_RESULTS.md
    # ============================
    b_lines = ["# Benchmark Results", ""]
    b_lines.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    b_lines.append("")
    b_lines.append("## Dataset Summary")
    b_lines.append("")
    b_lines.append("| Property | Value |")
    b_lines.append("| -------- | ----- |")
    b_lines.append("| Training Samples | 5,715 |")
    b_lines.append("| Training Scam | 888 (15.5%) |")
    b_lines.append("| Training Safe | 4,827 (84.5%) |")
    b_lines.append("| Evaluation Samples | 558 |")
    b_lines.append("| Evaluation Scam | 470 (84.2%) |")
    b_lines.append("| Evaluation Safe | 88 (15.8%) |")
    b_lines.append("| Evaluation Categories | 25 (19 scam, 6 legit) |")
    b_lines.append("")

    for m in models:
        r = all_results[m]
        o = r["overall"]
        b_lines.append(f"## Model: `{m}`")
        b_lines.append("")
        b_lines.append(f"- **Training Time:** {r['train_time_seconds']}s")
        b_lines.append(f"- **Inference Time:** {r['eval_time_seconds']}s ({r['throughput_samples_per_sec']} samples/sec)")
        b_lines.append(f"- **Optimal Threshold:** {r['optimal_threshold']['threshold']:.4f} (max {r['optimal_threshold']['metric']}: {r['optimal_threshold']['metric_value']:.4f})")
        b_lines.append("")
        b_lines.append("### Overall Metrics")
        b_lines.append("")
        b_lines.append("| Metric | Value |")
        b_lines.append("| ------ | ----- |")
        for k in ["accuracy", "precision", "recall", "f1", "mcc", "balanced_accuracy", "roc_auc", "specificity", "false_positive_rate", "false_negative_rate"]:
            b_lines.append(f"| {k.replace('_', ' ').title()} | {_fmt(o.get(k, 0))} |")
        b_lines.append("")
        b_lines.append("### Confusion Matrix")
        b_lines.append("")
        cm = o["confusion_matrix"]
        b_lines.append(f"| | Predicted Safe | Predicted Scam |")
        b_lines.append(f"| - | -------------- | -------------- |")
        b_lines.append(f"| **Actual Safe** | {cm['tn']} | {cm['fp']} |")
        b_lines.append(f"| **Actual Scam** | {cm['fn']} | {cm['tp']} |")
        b_lines.append("")

        b_lines.append("### Calibration (ECE)")
        cal = r["calibration"]
        b_lines.append(f"- **Expected Calibration Error:** {cal.get('ece', 'N/A'):.4f}")
        b_lines.append("")
        if cal.get("bins"):
            b_lines.append("| Bin | Confidence | Accuracy | Count | Gap |")
            b_lines.append("| --- | ---------- | -------- | ----- | --- |")
            bins = cal["bins"]
            accs = cal["accuracy"]
            confs = cal["confidence"]
            counts = cal["counts"]
            for i in range(len(bins) - 1):
                if i < len(accs) and i < len(confs) and i < len(counts):
                    gap = abs(confs[i] - accs[i])
                    b_lines.append(f"| [{bins[i]:.2f}, {bins[i+1]:.2f}) | {confs[i]:.4f} | {accs[i]:.4f} | {int(counts[i])} | {gap:.4f} |")
            b_lines.append("")

        b_lines.append("### Error Summary")
        ea = r["error_analysis"]["summary"]
        b_lines.append(f"- **Correct:** {ea['correct']} ({ea['accuracy']:.2%})")
        b_lines.append(f"- **Incorrect:** {ea['incorrect']} ({1-ea['accuracy']:.2%})")
        b_lines.append(f"- **False Positives:** {ea['false_positives']}")
        b_lines.append(f"- **False Negatives:** {ea['false_negatives']}")
        b_lines.append(f"- **Ambiguous:** {r['error_analysis']['ambiguous_samples']}")
        b_lines.append("")

        b_lines.append("### Per-Category F1 Scores")
        b_lines.append("")
        b_lines.append("| Category | Samples | F1 | Precision | Recall |")
        b_lines.append("| -------- | ------: | --: | --------: | -----: |")
        for cat in sorted(r["per_category"].keys()):
            pc = r["per_category"][cat]
            b_lines.append(f"| {cat} | {pc['total']} | {_fmt(pc['f1'])} | {_fmt(pc['precision'])} | {_fmt(pc['recall'])} |")
        b_lines.append("")
        b_lines.append("---")
        b_lines.append("")

    br_path = results_dir / "reports" / "BENCHMARK_RESULTS.md"
    br_path.write_text("\n".join(b_lines), encoding="utf-8")
    logger.info("Written: %s", br_path)

    # ============================
    # 3. ERROR_ANALYSIS.md
    # ============================
    e_lines = ["# Error Analysis Report", ""]
    e_lines.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    e_lines.append("")
    e_lines.append("## Overview")
    e_lines.append("")
    e_lines.append("| Model | Correct | Incorrect | Accuracy | FP | FN | FNR | FPR |")
    e_lines.append("| ----- | ------: | --------: | -------: | -: | -: | --: | --: |")
    for m in models:
        s = all_results[m]["error_analysis"]["summary"]
        o = all_results[m]["overall"]
        fpr = o["false_positive_rate"]
        fnr = o["false_negative_rate"]
        e_lines.append(f"| `{m}` | {s['correct']} | {s['incorrect']} | {s['accuracy']:.2%} | {s['false_positives']} | {s['false_negatives']} | {fnr:.2%} | {fpr:.2%} |")
    e_lines.append("")

    e_lines.append("## False Positive Analysis (Safe → Flagged as Scam)")
    e_lines.append("")
    for m in models:
        fp = all_results[m]["error_analysis"]["failure_profile"].get("false_positives", {})
        e_lines.append(f"### Model: `{m}` — {fp.get('count', 0)} False Positives")
        e_lines.append("")
        if fp.get("count", 0) > 0:
            e_lines.append(f"- **Avg Confidence:** {fp.get('avg_confidence', 0):.4f}")
            e_lines.append(f"- **Top Categories:** {', '.join(f'{k}({v})' for k, v in list(fp.get('categories', {}).items())[:5])}")
            e_lines.append(f"- **Languages:** {', '.join(f'{k}({v})' for k, v in fp.get('languages', {}).items())}")
        else:
            e_lines.append("No false positives.")
        e_lines.append("")

    e_lines.append("## False Negative Analysis (Scam → Flagged as Safe)")
    e_lines.append("")
    for m in models:
        fn_res = all_results[m]["error_analysis"]["failure_profile"].get("false_negatives", {})
        e_lines.append(f"### Model: `{m}` — {fn_res.get('count', 0)} False Negatives")
        e_lines.append("")
        if fn_res.get("count", 0) > 0:
            e_lines.append(f"- **Avg Confidence:** {fn_res.get('avg_confidence', 0):.4f}")
            e_lines.append(f"- **Top Categories:** {', '.join(f'{k}({v})' for k, v in list(fn_res.get('categories', {}).items())[:5])}")
        else:
            e_lines.append("No false negatives.")
        e_lines.append("")

    e_lines.append("## Ambiguous Predictions (Confidence near 0.5)")
    e_lines.append("")
    for m in models:
        e_lines.append(f"- **`{m}`:** {all_results[m]['error_analysis']['ambiguous_samples']} samples")
    e_lines.append("")

    e_lines.append("## Category Confusion Analysis")
    e_lines.append("")
    e_lines.append("See per-category F1 breakdown below for models that struggle with specific categories.")
    e_lines.append("")
    all_cats = sorted(set(c for m in models for c in all_results[m]["per_category"].keys()))
    e_lines.append("| Category | Samples | " + " | ".join(f"`{m}` F1" for m in models) + " | Issue? |")
    e_lines.append("| -------- | ------: | " + " | ".join("-------:" for _ in models) + " | ----- |")
    for cat in all_cats:
        worst_f1 = 1.0
        best_f1_val = -1
        f1_vals = []
        for m in models:
            pc = all_results[m]["per_category"].get(cat, {})
            f1v = pc.get("f1", 0)
            f1_vals.append(f1v)
            if f1v < worst_f1:
                worst_f1 = f1v
            if f1v > best_f1_val:
                best_f1_val = f1v
        total = all_results[models[0]]["per_category"].get(cat, {}).get("total", 0)
        threshold = 0.5
        issue = "⚠️ All models struggle" if worst_f1 < threshold else ("✅ Generally OK" if worst_f1 >= 0.7 else "⚠️ Some models struggle")
        e_lines.append(f"| {cat} | {total} | " + " | ".join(f"{f:.4f}" for f in f1_vals) + f" | {issue} |")
    e_lines.append("")

    ea_path = results_dir / "reports" / "ERROR_ANALYSIS.md"
    ea_path.write_text("\n".join(e_lines), encoding="utf-8")
    logger.info("Written: %s", ea_path)

    # ============================
    # 4. MODEL_SELECTION_REPORT.md
    # ============================
    s_lines = ["# Model Selection Report", ""]
    s_lines.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    s_lines.append("")
    s_lines.append("## Executive Summary")
    s_lines.append("")

    rankings = {}
    for m in models:
        o = all_results[m]["overall"]
        rankings[m] = {
            "f1": o["f1"],
            "accuracy": o["accuracy"],
            "precision": o["precision"],
            "recall": o["recall"],
            "mcc": o["mcc"],
            "balanced_accuracy": o["balanced_accuracy"],
            "roc_auc": o["roc_auc"],
            "train_time": all_results[m]["train_time_seconds"],
            "inference_speed": all_results[m]["throughput_samples_per_sec"],
        }

    def rank_models(metric: str, higher_better: bool = True):
        items = [(rankings[m][metric], m) for m in models]
        items.sort(reverse=higher_better)
        return items

    composite = {}
    for m in models:
        score = 0
        for metric in ["f1", "roc_auc", "mcc", "balanced_accuracy", "recall"]:
            vals = [rankings[om][metric] for om in models]
            mn, mx = min(vals), max(vals)
            if mx > mn:
                score += (rankings[m][metric] - mn) / (mx - mn)
            else:
                score += 0.5
        composite[m] = round(score / 5, 4)

    ranked = sorted(composite.items(), key=lambda x: x[1], reverse=True)
    s_lines.append(f"**Recommended Model:** `{ranked[0][0]}` (composite score: {ranked[0][1]})")
    s_lines.append("")
    s_lines.append("| Rank | Model | Composite Score | F1 | Precision | Recall | AUC | MCC | Train Time | Inference |")
    s_lines.append("| ---: | ----- | --------------: | -: | --------: | ----: | --: | --: | ---------: | --------: |")
    for i, (m, score) in enumerate(ranked, 1):
        r = rankings[m]
        s_lines.append(f"| {i} | `{m}` | {score:.4f} | {r['f1']:.4f} | {r['precision']:.4f} | {r['recall']:.4f} | {r['roc_auc']:.4f} | {r['mcc']:.4f} | {r['train_time']:.1f}s | {r['inference_speed']:.0f}/s |")
    s_lines.append("")

    s_lines.append("## Detailed Analysis By Criterion")
    s_lines.append("")

    criteria = {
        "Accuracy": "accuracy",
        "Precision": "precision",
        "Recall": "recall",
        "F1 Score": "f1",
        "ROC-AUC": "roc_auc",
        "MCC": "mcc",
        "Balanced Accuracy": "balanced_accuracy",
        "Training Speed": "train_time",
        "Inference Speed": "inference_speed",
    }
    for criterion_name, metric in criteria.items():
        higher = metric != "train_time"
        ranked_metric = rank_models(metric, higher_better=higher)
        s_lines.append(f"### {criterion_name}")
        s_lines.append("")
        best_m = ranked_metric[0][1]
        best_v = ranked_metric[0][0]
        s_lines.append(f"**Best:** `{best_m}` ({best_v})")
        s_lines.append("")
        for v, m in ranked_metric:
            marker = " ✅" if m == best_m else ""
            s_lines.append(f"- `{m}`: {v:.4f}{marker}")
        s_lines.append("")

    s_lines.append("## Trade-offs and Considerations")
    s_lines.append("")

    best_m = ranked[0][0]
    runner_up = ranked[1][0] if len(ranked) > 1 else None

    s_lines.append(f"### **`{best_m}`** (Top Ranked)")
    o = all_results[best_m]["overall"]
    s_lines.append("")
    s_lines.append("**Strengths:**")
    for metric, higher_name in [("f1", "F1"), ("roc_auc", "ROC-AUC"), ("mcc", "MCC"), ("recall", "Recall")]:
        if rank_models(metric, True)[0][1] == best_m:
            s_lines.append(f"- Best {higher_name}")
    s_lines.append("")
    s_lines.append("**Weaknesses:**")
    for metric in ["train_time"]:
        if rank_models(metric, False)[-1][1] == best_m:
            s_lines.append(f"- Slowest training")
    for metric, name in [("false_positive_rate", "FPR"), ("false_negative_rate", "FNR")]:
        vals = [(all_results[om]["overall"].get(metric, 0), om) for om in models]
        vals.sort(reverse=True)
        if vals[-1][1] == best_m:
            s_lines.append(f"- Lowest {name} (good)")
        elif vals[0][1] == best_m:
            s_lines.append(f"- Highest {name} (bad)")
    s_lines.append("")
    s_lines.append(f"**Recommendation:** {'Strongly recommended for production' if best_m == ranked[0][0] else 'Good alternative'}.")
    s_lines.append("")

    if runner_up:
        s_lines.append(f"### **`{runner_up}`** (Runner-up)")
        s_lines.append("")
        o = all_results[runner_up]["overall"]
        tradeoffs = []
        for metric in ["f1", "roc_auc", "mcc", "precision", "recall", "train_time"]:
            higher = metric != "train_time"
            rnkd = rank_models(metric, higher)
            rank_pos = [i for i, (v, m) in enumerate(rnkd) if m == runner_up][0]
            if rank_pos == 0:
                tradeoffs.append(f"Best {metric}")
            elif rank_pos == len(models) - 1:
                tradeoffs.append(f"Worst {metric}")
        if tradeoffs:
            for t in tradeoffs:
                s_lines.append(f"- {t}")
        s_lines.append("")

    if len(models) > 2:
        other_m = ranked[2][0]
        s_lines.append(f"### **`{other_m}`**")
        s_lines.append("")
        s_lines.append("**When to use:** ")
        if "tfidf" in other_m:
            s_lines.append("When inference speed and low resource usage are critical. No GPU required.")
        elif "embedding" in other_m:
            s_lines.append("When semantic understanding is needed and GPU is available.")
        elif "transformer" in other_m:
            s_lines.append("When maximum accuracy is needed and inference latency tolerances allow.")
        s_lines.append("")

    s_lines.append("## Final Recommendation")
    s_lines.append("")
    s_lines.append(f"**→ Deploy `{best_m}`** as the primary scam detection model.")
    s_lines.append("")
    s_lines.append("### Next Steps")
    s_lines.append("")
    s_lines.append("1. Replace the current production model with the selected model.")
    s_lines.append("2. Set up monitoring for false positive rate in production.")
    s_lines.append("3. Implement A/B testing framework to compare against existing model.")
    s_lines.append("4. Schedule periodic retraining with newly labeled data.")
    s_lines.append("5. Consider ensemble approach if single-model performance is insufficient.")
    s_lines.append("")

    sr_path = results_dir / "reports" / "MODEL_SELECTION_REPORT.md"
    sr_path.write_text("\n".join(s_lines), encoding="utf-8")
    logger.info("Written: %s", sr_path)

    # Also save raw results as JSON
    json_path = results_dir / "reports" / "all_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (np.integer,)): return int(obj)
                if isinstance(obj, (np.floating,)): return float(obj)
                if isinstance(obj, np.ndarray): return obj.tolist()
                return super().default(obj)
        json.dump(all_results, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
    logger.info("Written: %s", json_path)

    logger.info("\n" + "=" * 60)
    logger.info("ALL REPORTS GENERATED IN: %s", results_dir / "reports")
    logger.info("=" * 60)


def main():
    logger.info("=" * 60)
    logger.info("SCAMSHIELD V2 COMPREHENSIVE MODEL BENCHMARK")
    logger.info("=" * 60)

    train_texts, train_labels = load_main_dataset(str(MAIN_DATASET))
    eval_texts, eval_labels, eval_categories = load_v2_alpha(str(V2_ALPHA))

    all_results = {}
    for model_type in MODEL_TYPES:
        try:
            result = train_evaluate_model(
                model_type, train_texts, train_labels,
                eval_texts, eval_labels, eval_categories,
            )
            all_results[model_type] = result
        except Exception as e:
            logger.error("Failed for model %s: %s", model_type, e, exc_info=True)

    if not all_results:
        logger.error("No models completed successfully!")
        return

    generate_markdown_report(all_results, RESULTS_DIR)

    logger.info("\nDone! All models benchmarked successfully.")


if __name__ == "__main__":
    main()
