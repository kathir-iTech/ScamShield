from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional, Tuple

from ..config.dataset_schema import VALID_CATEGORIES, SCAM_CATEGORIES


def _safe_divide(a: float, b: float) -> float:
    return a / b if b != 0 else 0.0


def analyze_errors(
    samples: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if len(samples) != len(predictions):
        raise ValueError(
            f"samples ({len(samples)}) and predictions ({len(predictions)}) length mismatch"
        )

    false_positives: List[Dict[str, Any]] = []
    false_negatives: List[Dict[str, Any]] = []
    true_positives: List[Dict[str, Any]] = []
    true_negatives: List[Dict[str, Any]] = []
    wrong_category: List[Dict[str, Any]] = []
    wrong_risk: List[Dict[str, Any]] = []

    pred_labels: List[str] = []
    true_labels: List[str] = []
    pred_scores: List[float] = []
    pred_categories: List[str] = []
    true_categories: List[str] = []

    for sample, pred in zip(samples, predictions):
        true_label = sample.get("ground_truth_label", "")
        pred_label = pred.get("prediction", "")
        score = pred.get("confidence", 0.5)
        pred_cat = pred.get("category", "")
        true_cat = sample.get("category", "")

        pred_labels.append(pred_label)
        true_labels.append(true_label)
        pred_scores.append(score)
        pred_categories.append(pred_cat)
        true_categories.append(true_cat)

        is_true_scam = true_label == "scam"
        is_pred_scam = pred_label == "scam"
        entry = {
            "sample": sample,
            "prediction": pred,
            "confidence": score,
        }

        if is_pred_scam and not is_true_scam:
            false_positives.append(entry)
        elif not is_pred_scam and is_true_scam:
            false_negatives.append(entry)
        elif is_pred_scam and is_true_scam:
            true_positives.append(entry)
        else:
            true_negatives.append(entry)

        if is_pred_scam and is_true_scam and pred_cat != true_cat:
            wrong_category.append(entry)

        if is_pred_scam and is_true_scam and pred.get("risk_level") != sample.get("risk_level"):
            wrong_risk.append(entry)

    errors = {
        "total_samples": len(samples),
        "correct": len(true_positives) + len(true_negatives),
        "incorrect": len(false_positives) + len(false_negatives),
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "wrong_category_count": len(wrong_category),
        "wrong_risk_level_count": len(wrong_risk),
        "accuracy": _safe_divide(len(true_positives) + len(true_negatives), len(samples)),
        "fp_details": false_positives[:100],
        "fn_details": false_negatives[:100],
        "wrong_category_details": wrong_category[:100],
    }

    return errors


def profile_failure_patterns(
    false_positives: List[Dict[str, Any]],
    false_negatives: List[Dict[str, Any]],
    wrong_category: List[Dict[str, Any]],
) -> Dict[str, Any]:
    profile: Dict[str, Any] = {}

    def _profile_samples(samples: List[Dict[str, Any]], name: str) -> Dict[str, Any]:
        if not samples:
            return {
                "count": 0,
                "categories": {},
                "languages": {},
                "avg_confidence": 0.0,
                "entity_patterns": defaultdict(int),
            }

        cats: Counter = Counter()
        langs: Counter = Counter()
        entities: Counter = Counter()
        total_conf = 0.0

        for entry in samples:
            sample = entry.get("sample", entry)
            cats[sample.get("category", "unknown")] += 1
            langs[sample.get("language", "unknown")] += 1
            total_conf += entry.get("confidence", 0.5)
            ents = sample.get("extracted_entities", {})
            if isinstance(ents, dict):
                for ent_type, vals in ents.items():
                    if isinstance(vals, list) and vals:
                        entities[ent_type] += 1

        return {
            "count": len(samples),
            "categories": dict(cats.most_common()),
            "languages": dict(langs.most_common()),
            "avg_confidence": round(_safe_divide(total_conf, len(samples)), 4),
            "entity_patterns": dict(entities.most_common()),
        }

    profile["false_positives"] = _profile_samples(false_positives, "FP")
    profile["false_negatives"] = _profile_samples(false_negatives, "FN")
    profile["wrong_category"] = _profile_samples(wrong_category, "WC")

    all_fails = false_positives + false_negatives + wrong_category
    profile["combined"] = _profile_samples(all_fails, "ALL_ERRORS")

    return profile


def generate_error_report(error_analysis: Dict[str, Any]) -> str:
    lines = ["Error Analysis Report", "=" * 60, ""]

    total = error_analysis.get("total_samples", 0)
    correct = error_analysis.get("correct", 0)
    incorrect = error_analysis.get("incorrect", 0)
    acc = error_analysis.get("accuracy", 0.0)

    lines.append(f"Total Samples:    {total}")
    lines.append(f"Correct:          {correct} ({acc:.2%})")
    lines.append(f"Incorrect:        {incorrect} ({(1-acc):.2%})")
    lines.append("")
    lines.append(f"False Positives:  {error_analysis.get('false_positives', 0)}")
    lines.append(f"False Negatives:  {error_analysis.get('false_negatives', 0)}")
    lines.append(f"Wrong Category:   {error_analysis.get('wrong_category_count', 0)}")
    lines.append(f"Wrong Risk Level: {error_analysis.get('wrong_risk_level_count', 0)}")
    lines.append("")

    fp_details = error_analysis.get("fp_details", [])
    fn_details = error_analysis.get("fn_details", [])
    wc_details = error_analysis.get("wrong_category_details", [])

    if fp_details:
        lines.append("False Positives (Top 10):")
        lines.append("-" * 40)
        for i, entry in enumerate(fp_details[:10]):
            sample = entry.get("sample", {})
            text = (sample.get("text", "") or "")[:80]
            conf = entry.get("confidence", 0.0)
            cat = sample.get("category", "?")
            lines.append(f"  {i+1}. [{cat}] (conf={conf:.3f}) {text}")

    if fn_details:
        lines.append("")
        lines.append("False Negatives (Top 10):")
        lines.append("-" * 40)
        for i, entry in enumerate(fn_details[:10]):
            sample = entry.get("sample", {})
            text = (sample.get("text", "") or "")[:80]
            conf = entry.get("confidence", 0.0)
            cat = sample.get("category", "?")
            lines.append(f"  {i+1}. [{cat}] (conf={conf:.3f}) {text}")

    if wc_details:
        lines.append("")
        lines.append("Wrong Category Predictions (Top 10):")
        lines.append("-" * 40)
        for i, entry in enumerate(wc_details[:10]):
            sample = entry.get("sample", {})
            pred = entry.get("prediction", {})
            text = (sample.get("text", "") or "")[:80]
            true_cat = sample.get("category", "?")
            pred_cat = pred.get("category", "?")
            lines.append(f"  {i+1}. True:{true_cat} → Pred:{pred_cat}  {text}")

    return "\n".join(lines)


def find_ambiguous_samples(
    samples: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
    confidence_threshold: float = 0.1,
) -> List[Dict[str, Any]]:
    ambiguous: List[Dict[str, Any]] = []

    for sample, pred in zip(samples, predictions):
        score = pred.get("confidence", 0.5)
        if abs(score - 0.5) <= confidence_threshold:
            ambiguous.append({
                "sample": sample,
                "prediction": pred,
                "confidence": score,
                "distance_from_threshold": abs(score - 0.5),
            })

    ambiguous.sort(key=lambda x: x["distance_from_threshold"])
    return ambiguous


def category_confusion_matrix(
    samples: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    all_cats = sorted(VALID_CATEGORIES)
    cat_index = {cat: i for i, cat in enumerate(all_cats)}
    n = len(all_cats)
    matrix = [[0] * n for _ in range(n)]
    row_counts = [0] * n

    for sample, pred in zip(samples, predictions):
        true_cat = sample.get("category", "")
        pred_cat = pred.get("category", "")
        if true_cat in cat_index and pred_cat in cat_index:
            i = cat_index[true_cat]
            j = cat_index[pred_cat]
            matrix[i][j] += 1
            row_counts[i] += 1

    misclassifications: Dict[str, Dict[str, int]] = {}
    for i, true_cat in enumerate(all_cats):
        if row_counts[i] == 0:
            continue
        misclassifications[true_cat] = {}
        for j, pred_cat in enumerate(all_cats):
            if i != j and matrix[i][j] > 0:
                misclassifications[true_cat][pred_cat] = matrix[i][j]

    overall_accuracy = _safe_divide(
        sum(matrix[i][i] for i in range(n)),
        sum(row_counts)
    )

    return {
        "categories": all_cats,
        "matrix": matrix,
        "row_totals": row_counts,
        "misclassifications": misclassifications,
        "overall_accuracy": round(overall_accuracy, 4),
    }
