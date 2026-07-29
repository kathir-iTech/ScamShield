import csv
import json
import logging
import os
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from .models import ModelWrapper, available_models, create_model

logger = logging.getLogger(__name__)

_CATEGORY_MAP: Dict[str, str] = {}


def load_training_data(path: str) -> Tuple[List[str], List[int]]:
    texts: List[str] = []
    labels: List[int] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row.get("text", ""))
            raw_label = row.get("label", "").strip().lower()
            labels.append(1 if raw_label in ("scam", "1", "true") else 0)
    logger.info("Loaded %d samples from %s (%d scam, %d safe)", len(texts), path, sum(labels), len(labels) - sum(labels))
    return texts, labels


def load_benchmark_dataset(path: str) -> Dict[str, List[Tuple[str, int]]]:
    categories: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("text", "")
            raw_label = row.get("label", "").strip().lower()
            label = 1 if raw_label in ("scam", "1", "true") else 0
            category = row.get("category", "general").strip()
            _CATEGORY_MAP[category] = _CATEGORY_MAP.get(category, category)
            categories[category].append((text, label))
    logger.info("Loaded benchmark dataset from %s (%d categories)", path, len(categories))
    for cat, samples in sorted(categories.items()):
        logger.info("  %s: %d samples", cat, len(samples))
    return dict(categories)


def find_optimal_threshold(wrapper: ModelWrapper, texts: List[str], labels: List[int]) -> float:
    probas = []
    for t in texts:
        result = wrapper.predict(t)
        probas.append(result.get("probabilities", {}).get("scam", 0.5))
    thresholds = np.linspace(0.1, 0.9, 81)
    best_f1 = 0.0
    best_threshold = 0.5
    for thresh in thresholds:
        preds = [1 if p >= thresh else 0 for p in probas]
        f1 = f1_score(labels, preds, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh
    logger.info("Optimal threshold: %.2f (F1=%.4f)", best_threshold, best_f1)
    return best_threshold


def compute_category_metrics(
    wrapper: ModelWrapper, categories: Dict[str, List[Tuple[str, int]]]
) -> Dict[str, Dict]:
    results: Dict[str, Dict] = {}
    for cat, samples in categories.items():
        texts = [s[0] for s in samples]
        labels = [s[1] for s in samples]
        preds = []
        for t in texts:
            result = wrapper.predict(t)
            preds.append(1 if result["prediction"] == "scam" else 0)
        results[cat] = {
            "total": len(labels),
            "accuracy": accuracy_score(labels, preds),
            "precision": precision_score(labels, preds, zero_division=0),
            "recall": recall_score(labels, preds, zero_division=0),
            "f1": f1_score(labels, preds, zero_division=0),
            "confusion_matrix": confusion_matrix(labels, preds).tolist(),
        }
    return results


def compute_overall_metrics(
    wrapper: ModelWrapper, categories: Dict[str, List[Tuple[str, int]]]
) -> Dict:
    all_texts: List[str] = []
    all_labels: List[int] = []
    for samples in categories.values():
        for t, l in samples:
            all_texts.append(t)
            all_labels.append(l)
    preds = []
    probas = []
    for t in all_texts:
        result = wrapper.predict(t)
        preds.append(1 if result["prediction"] == "scam" else 0)
        probas.append(result.get("probabilities", {}).get("scam", 0.5))
    try:
        auc = roc_auc_score(all_labels, probas)
    except Exception:
        auc = 0.0
    tn, fp, fn, tp = confusion_matrix(all_labels, preds).ravel()
    return {
        "total": len(all_labels),
        "accuracy": accuracy_score(all_labels, preds),
        "precision": precision_score(all_labels, preds, zero_division=0),
        "recall": recall_score(all_labels, preds, zero_division=0),
        "f1": f1_score(all_labels, preds, zero_division=0),
        "specificity": tn / (tn + fp) if (tn + fp) > 0 else 0.0,
        "false_positive_rate": fp / (fp + tn) if (fp + tn) > 0 else 0.0,
        "roc_auc": auc,
        "confusion_matrix": {"tp": int(tp), "fn": int(fn), "fp": int(fp), "tn": int(tn)},
    }


def train_all_models(
    texts: List[str], labels: List[int], output_dir: str, model_types: Optional[List[str]] = None
) -> Dict[str, ModelWrapper]:
    if model_types is None:
        model_types = ["tfidf_lr", "tfidf_svm", "embedding", "transformer"]
    trained: Dict[str, ModelWrapper] = {}
    for mtype in model_types:
        try:
            logger.info("Training model: %s", mtype)
            wrapper = create_model(mtype, texts=texts, labels=labels)
            trained[mtype] = wrapper
            model_dir = os.path.join(output_dir, "models", mtype)
            wrapper.save(model_dir)
            logger.info("Saved model %s to %s", mtype, model_dir)
        except Exception as e:
            logger.error("Failed to train model %s: %s", mtype, e)
    return trained


def evaluate_all(
    models: Dict[str, ModelWrapper],
    benchmark: Dict[str, List[Tuple[str, int]]],
    output_dir: str,
) -> Dict[str, Dict]:
    results: Dict[str, Dict] = {}
    for name, wrapper in models.items():
        logger.info("Evaluating model: %s", name)
        optimal_threshold = find_optimal_threshold(
            wrapper,
            [s[0] for samples in benchmark.values() for s in samples],
            [s[1] for samples in benchmark.values() for s in samples],
        )
        wrapper.threshold = optimal_threshold
        cat_metrics = compute_category_metrics(wrapper, benchmark)
        overall = compute_overall_metrics(wrapper, benchmark)
        results[name] = {
            "optimal_threshold": optimal_threshold,
            "overall": overall,
            "per_category": cat_metrics,
        }
        cat_path = os.path.join(output_dir, "results", f"{name}_category_metrics.json")
        os.makedirs(os.path.dirname(cat_path), exist_ok=True)
        with open(cat_path, "w", encoding="utf-8") as f:
            json.dump(cat_metrics, f, indent=2)
    overall_path = os.path.join(output_dir, "results", "all_results.json")
    with open(overall_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info("All results saved to %s", overall_path)
    return results


def generate_comparison_report(results: Dict[str, Dict], output_path: str) -> str:
    lines: List[str] = []
    lines.append("=" * 120)
    lines.append("  SCAMSHIELD V2 MODEL COMPARISON REPORT")
    lines.append(f"  Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 120)
    lines.append("")
    header = f"{'Model':<20} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'AUC':>10} {'Threshold':>10}"
    lines.append(header)
    lines.append("-" * len(header))
    for model_name, metrics in sorted(results.items()):
        o = metrics["overall"]
        lines.append(
            f"{model_name:<20} {o['accuracy']:>10.4f} {o['precision']:>10.4f} {o['recall']:>10.4f} "
            f"{o['f1']:>10.4f} {o['roc_auc']:>10.4f} {metrics['optimal_threshold']:>10.2f}"
        )
    lines.append("")
    categories = set()
    for metrics in results.values():
        categories.update(metrics["per_category"].keys())
    for cat in sorted(categories):
        lines.append("")
        lines.append(f"  Category: {cat}")
        lines.append("-" * 80)
        cat_header = f"{'Model':<20} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}"
        lines.append(cat_header)
        lines.append("-" * len(cat_header))
        for model_name, metrics in sorted(results.items()):
            if cat in metrics["per_category"]:
                c = metrics["per_category"][cat]
                lines.append(
                    f"{model_name:<20} {c['accuracy']:>10.4f} {c['precision']:>10.4f} {c['recall']:>10.4f} {c['f1']:>10.4f}"
                )
    lines.append("")
    lines.append("=" * 120)
    lines.append("  CONFUSION MATRICES")
    lines.append("=" * 120)
    for model_name, metrics in sorted(results.items()):
        cm = metrics["overall"]["confusion_matrix"]
        lines.append(f"\n  {model_name}:")
        lines.append(f"    TP={cm['tp']:>5}  FN={cm['fn']:>5}")
        lines.append(f"    FP={cm['fp']:>5}  TN={cm['tn']:>5}")
    report = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("Comparison report written to %s", output_path)
    return report


def run_benchmark(
    dataset_path: str,
    output_dir: str,
    model_types: Optional[List[str]] = None,
    benchmark_path: Optional[str] = None,
) -> Dict:
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "models"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "results"), exist_ok=True)

    texts, labels = load_training_data(dataset_path)
    trained = train_all_models(texts, labels, output_dir, model_types)
    if not trained:
        logger.error("No models trained successfully")
        return {}
    if benchmark_path is None:
        benchmark_dir = os.path.dirname(dataset_path)
        candidate = os.path.join(benchmark_dir, "benchmark.csv")
        if os.path.exists(candidate):
            benchmark_path = candidate
        else:
            logger.warning("No benchmark dataset found, using training data as evaluation set")
            from sklearn.model_selection import train_test_split
            _, eval_texts, _, eval_labels = train_test_split(texts, labels, test_size=0.2, random_state=42, stratify=labels)
            benchmark = {"evaluation": list(zip(eval_texts, eval_labels))}
            results = evaluate_all(trained, benchmark, output_dir)
            generate_comparison_report(results, os.path.join(output_dir, "results", "comparison_report.txt"))
            return results
    benchmark = load_benchmark_dataset(benchmark_path)
    results = evaluate_all(trained, benchmark, output_dir)
    report_path = os.path.join(output_dir, "results", "comparison_report.txt")
    generate_comparison_report(results, report_path)
    logger.info("Benchmark complete. Results in %s", output_dir)
    return results
