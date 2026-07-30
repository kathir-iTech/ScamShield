import csv, json, logging, os, sys, time, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("transformer-benchmark")

from benchmarks.v2.scripts.models import train_transformer, ModelWrapper
from benchmarks.v2.scripts.evaluation_metrics import (
    compute_calibration, compute_roc_curve, compute_pr_curve, find_optimal_threshold,
)
from benchmarks.v2.scripts.error_analysis import (
    analyze_errors, profile_failure_patterns, find_ambiguous_samples, category_confusion_matrix,
)
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix, matthews_corrcoef, balanced_accuracy_score)
import numpy as np

SEED = 42
RESULTS_DIR = Path(__file__).resolve().parent
MAIN_DATASET = RESULTS_DIR.parent.parent / "backend" / "data" / "scam_dataset.csv"
V2_ALPHA = RESULTS_DIR.parent.parent / "datasets" / "v2" / "annotated" / "dataset_v2_alpha.csv"

def load_main_dataset(path):
    texts, labels = [], []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row.get("text", ""))
            labels.append(1 if row.get("label", "").strip().lower() == "scam" else 0)
    logger.info("Main dataset: %d samples (%d scam)", len(texts), sum(labels))
    return texts, labels

def load_v2_alpha(path):
    texts, labels, categories = [], [], []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("text_clean") or row.get("text", "")
            texts.append(text)
            is_scam = row.get("is_scam", "False").strip().lower() in ("true", "1", "yes")
            labels.append(1 if is_scam else 0)
            categories.append(row.get("category", "UNKNOWN").strip())
    logger.info("V2 alpha: %d samples (%d scam)", len(texts), sum(labels))
    return texts, labels, categories

def main():
    train_texts, train_labels = load_main_dataset(str(MAIN_DATASET))
    eval_texts, eval_labels, eval_categories = load_v2_alpha(str(V2_ALPHA))

    t0 = time.time()
    tokenizer, model = train_transformer(train_texts, train_labels, model_name="distilbert-base-uncased")
    train_time = time.time() - t0
    logger.info("Transformer training took %.1f seconds", train_time)

    wrapper = ModelWrapper(model, vectorizer=None)
    wrapper._tokenizer = tokenizer
    wrapper._is_transformer = True

    t1 = time.time()
    y_pred, y_scores, y_true = [], [], []
    for text, true_label in zip(eval_texts, eval_labels):
        result = wrapper.predict(text)
        pred = 1 if result["prediction"] == "scam" else 0
        y_pred.append(pred)
        y_scores.append(result.get("confidence", 0.5))
        y_true.append(true_label)
    eval_time = time.time() - t1

    opt_thresh = find_optimal_threshold(y_true, y_scores, metric="f1")
    wrapper.threshold = opt_thresh["threshold"]
    y_pred_opt = [1 if p >= wrapper.threshold else 0 for p in y_scores]

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred_opt).ravel()
    overall = {
        "total": len(y_true), "accuracy": accuracy_score(y_true, y_pred_opt),
        "precision": precision_score(y_true, y_pred_opt, zero_division=0),
        "recall": recall_score(y_true, y_pred_opt, zero_division=0),
        "f1": f1_score(y_true, y_pred_opt, zero_division=0),
        "specificity": tn / (tn + fp) if (tn + fp) > 0 else 0.0,
        "false_positive_rate": fp / (fp + tn) if (fp + tn) > 0 else 0.0,
        "false_negative_rate": fn / (fn + tp) if (fn + tp) > 0 else 0.0,
        "mcc": matthews_corrcoef(y_true, y_pred_opt),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred_opt),
        "roc_auc": roc_auc_score(y_true, y_scores),
        "confusion_matrix": {"tp": int(tp), "fn": int(fn), "fp": int(fp), "tn": int(tn)},
    }
    logger.info("Results: %s", overall)

    per_category = {}
    for cat in sorted(set(eval_categories)):
        mask = [c == cat for c in eval_categories]
        cat_true = [y_true[i] for i, m in enumerate(mask) if m]
        cat_pred = [y_pred_opt[i] for i, m in enumerate(mask) if m]
        if len(cat_true):
            cat_tn, cat_fp, cat_fn, cat_tp = confusion_matrix(cat_true, cat_pred, labels=[0, 1]).ravel()
            per_category[cat] = {
                "total": len(cat_true), "f1": f1_score(cat_true, cat_pred, zero_division=0),
                "precision": precision_score(cat_true, cat_pred, zero_division=0),
                "recall": recall_score(cat_true, cat_pred, zero_division=0),
                "tp": int(cat_tp), "fn": int(cat_fn), "fp": int(cat_fp), "tn": int(cat_tn),
            }

    samples_for_error = [{"text": t, "text_clean": t, "category": c, "is_scam": bool(l),
                          "ground_truth_label": "scam" if l else "legitimate", "risk_level": "HIGH" if l else "NONE"}
                         for t, c, l in zip(eval_texts, eval_categories, y_true)]
    preds_for_error = [{"prediction": "scam" if p else "safe", "confidence": s}
                       for p, s in zip(y_pred_opt, y_scores)]
    error_analysis = analyze_errors(samples_for_error, preds_for_error)
    failure_profile = profile_failure_patterns(
        error_analysis.get("fp_details", []), error_analysis.get("fn_details", []), [])

    result = {
        "model_type": "transformer",
        "train_time_seconds": round(train_time, 1),
        "eval_time_seconds": round(eval_time, 4),
        "throughput_samples_per_sec": round(len(eval_texts) / eval_time, 2) if eval_time > 0 else 0,
        "optimal_threshold": opt_thresh,
        "overall": overall,
        "per_category": per_category,
        "roc_curve": compute_roc_curve(y_true, y_scores),
        "pr_curve": compute_pr_curve(y_true, y_scores),
        "calibration": compute_calibration(y_true, y_scores),
        "error_analysis": {
            "summary": {
                "total": error_analysis["total_samples"], "correct": error_analysis["correct"],
                "incorrect": error_analysis["incorrect"], "accuracy": error_analysis["accuracy"],
                "false_positives": error_analysis["false_positives"],
                "false_negatives": error_analysis["false_negatives"],
            },
            "failure_profile": failure_profile,
            "ambiguous_samples": len(find_ambiguous_samples(samples_for_error, preds_for_error)),
        },
    }

    out_path = RESULTS_DIR / "reports" / "transformer_result.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=lambda x: float(x) if isinstance(x, (np.floating,)) else int(x) if isinstance(x, np.integer) else x)
    logger.info("Transformer results saved to %s", out_path)

if __name__ == "__main__":
    main()
