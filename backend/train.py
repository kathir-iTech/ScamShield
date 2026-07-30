import csv
import json
import logging
import os
import time
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score,
)

from config.settings import DATASET_PATH, MODEL_FOLDER, MODEL_PATH, VECTORIZER_PATH
from utils.text import clean_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_data(path: str) -> Tuple[List[str], List[int], List[str]]:
    texts: List[str] = []
    labels: List[int] = []
    categories: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            if "is_scam" in row:
                raw = row["is_scam"].strip().lower()
                labels.append(1 if raw in ("true", "1", "yes") else 0)
            else:
                labels.append(1 if row.get("label", "safe") == "scam" else 0)
            categories.append(row.get("category", "unknown"))
    return texts, labels, categories


def evaluate_model(model, vectorizer, X_test, y_test) -> Dict[str, Any]:
    X_test_vec = vectorizer.transform(X_test)
    y_pred = model.predict(X_test_vec)
    y_proba = model.predict_proba(X_test_vec)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()

    try:
        roc_auc = roc_auc_score(y_test, y_proba)
    except Exception:
        roc_auc = 0.0

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "fpr": round(fp / (fp + tn) if (fp + tn) > 0 else 0.0, 4),
        "fnr": round(fn / (fn + tp) if (fn + tp) > 0 else 0.0, 4),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "n_test": len(y_test),
        "y_pred": y_pred.tolist() if hasattr(y_pred, "tolist") else list(y_pred),
        "y_proba": y_proba.tolist() if hasattr(y_proba, "tolist") else list(y_proba),
    }


def cross_validate(vectorizer_params: Dict[str, Any], model_params: Dict[str, Any],
                   texts: List[str], labels: List[int], n_splits: int = 5) -> Dict[str, Any]:
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    fold_metrics: List[Dict[str, float]] = []

    for fold, (train_idx, test_idx) in enumerate(skf.split(texts, labels)):
        X_train_fold = [texts[i] for i in train_idx]
        X_test_fold = [texts[i] for i in test_idx]
        y_train_fold = [labels[i] for i in train_idx]
        y_test_fold = [labels[i] for i in test_idx]

        vec = TfidfVectorizer(**vectorizer_params)
        X_train_vec = vec.fit_transform(X_train_fold)
        model = LogisticRegression(**model_params)
        model.fit(X_train_vec, y_train_fold)

        metrics = evaluate_model(model, vec, X_test_fold, y_test_fold)
        fold_metrics.append({
            "fold": fold + 1,
            "accuracy": metrics["accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
            "roc_auc": metrics["roc_auc"],
            "fpr": metrics["fpr"],
            "fnr": metrics["fnr"],
        })
        logger.info("  Fold %d: acc=%.4f f1=%.4f roc_auc=%.4f", fold + 1, metrics["accuracy"], metrics["f1"], metrics["roc_auc"])

    avg_metrics = {
        "accuracy": np.mean([m["accuracy"] for m in fold_metrics]),
        "f1": np.mean([m["f1"] for m in fold_metrics]),
        "roc_auc": np.mean([m["roc_auc"] for m in fold_metrics]),
    }
    std_metrics = {
        "accuracy_std": np.std([m["accuracy"] for m in fold_metrics]),
        "f1_std": np.std([m["f1"] for m in fold_metrics]),
        "roc_auc_std": np.std([m["roc_auc"] for m in fold_metrics]),
    }

    return {
        "fold_metrics": fold_metrics,
        "average": avg_metrics,
        "std": std_metrics,
    }


def main() -> None:
    os.makedirs(MODEL_FOLDER, exist_ok=True)
    training_log_path = os.path.join(MODEL_FOLDER, "training_log.json")

    logger.info("Loading dataset from %s", DATASET_PATH)
    texts, labels, categories = load_data(DATASET_PATH)
    n_scam = sum(labels)
    n_safe = len(labels) - n_scam
    logger.info("Loaded %d samples (%d scam, %d safe)", len(texts), n_scam, n_safe)

    texts = [clean_text(t) for t in texts]

    report_dir = os.path.join(MODEL_FOLDER, "training_reports")
    os.makedirs(report_dir, exist_ok=True)

    logger.info("Training configuration:")
    vectorizer_params: Dict[str, Any] = {
        "max_features": 5000,
        "ngram_range": (1, 2),
        "stop_words": "english",
        "min_df": 2,
        "max_df": 0.95,
    }
    model_params: Dict[str, Any] = {
        "class_weight": "balanced",
        "max_iter": 1000,
        "random_state": 42,
        "C": 1.0,
        "solver": "lbfgs",
    }
    logger.info("  Vectorizer: %s", vectorizer_params)
    logger.info("  Model: %s", model_params)

    logger.info("Running %d-fold cross-validation...", 5)
    start = time.perf_counter()
    cv_results = cross_validate(vectorizer_params, model_params, texts, labels, n_splits=5)
    cv_elapsed = time.perf_counter() - start
    logger.info("Cross-validation completed in %.1fs", cv_elapsed)
    logger.info("  CV Accuracy: %.4f (+/- %.4f)", cv_results["average"]["accuracy"], cv_results["std"]["accuracy_std"])
    logger.info("  CV F1:       %.4f (+/- %.4f)", cv_results["average"]["f1"], cv_results["std"]["f1_std"])
    logger.info("  CV ROC-AUC:  %.4f (+/- %.4f)", cv_results["average"]["roc_auc"], cv_results["std"]["roc_auc_std"])

    logger.info("Training final model on full training set...")
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    logger.info("  Train size: %d, Test size: %d", len(X_train), len(X_test))

    vectorizer = TfidfVectorizer(**vectorizer_params)
    X_train_vec = vectorizer.fit_transform(X_train)

    model = LogisticRegression(**model_params)
    model.fit(X_train_vec, y_train)

    test_metrics = evaluate_model(model, vectorizer, X_test, y_test)
    logger.info("Test set results:")
    logger.info("  Accuracy:  %.4f", test_metrics["accuracy"])
    logger.info("  Precision: %.4f", test_metrics["precision"])
    logger.info("  Recall:    %.4f", test_metrics["recall"])
    logger.info("  F1:        %.4f", test_metrics["f1"])
    logger.info("  ROC-AUC:   %.4f", test_metrics["roc_auc"])
    logger.info("  FPR:       %.4f", test_metrics["fpr"])
    logger.info("  FNR:       %.4f", test_metrics["fnr"])
    logger.info("  Confusion: TP=%d FP=%d FN=%d TN=%d",
                test_metrics["tp"], test_metrics["fp"], test_metrics["fn"], test_metrics["tn"])

    X_test_vec = vectorizer.transform(X_test)
    y_pred = model.predict(X_test_vec)
    print()
    print(classification_report(y_test, y_pred, target_names=["safe", "scam"]))

    coef_df = _extract_top_features(vectorizer, model, top_n=20)
    print()
    print("Top 20 most important features for scam detection:")
    print(f"  {'Feature':40s} {'Coefficient':>12s}")
    print(f"  {'-'*40} {'-'*12}")
    for feat, coef in coef_df["top_scam"]:
        print(f"  {feat:40s} {coef:>12.4f}")
    print()
    print("Top 20 most important features for safe classification:")
    for feat, coef in coef_df["top_safe"]:
        print(f"  {feat:40s} {coef:>12.4f}")

    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    logger.info("Model saved to %s", MODEL_PATH)
    logger.info("Vectorizer saved to %s", VECTORIZER_PATH)

    session = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset": {
            "path": DATASET_PATH,
            "n_samples": len(texts),
            "n_scam": n_scam,
            "n_safe": n_safe,
        },
        "vectorizer_params": {k: str(v) if isinstance(v, tuple) else v for k, v in vectorizer_params.items()},
        "model_params": {k: str(v) if isinstance(v, type) else v for k, v in model_params.items()},
        "cross_validation": {
            "n_splits": 5,
            "duration_seconds": round(cv_elapsed, 1),
            "average": {k: round(v, 4) for k, v in cv_results["average"].items()},
            "std": {k: round(v, 4) for k, v in cv_results["std"].items()},
            "fold_metrics": cv_results["fold_metrics"],
        },
        "test_set": test_metrics,
        "top_features": {
            "scam": [(f, round(c, 4)) for f, c in coef_df["top_scam"]],
            "safe": [(f, round(c, 4)) for f, c in coef_df["top_safe"]],
        },
    }

    with open(training_log_path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, ensure_ascii=False, default=str)
    logger.info("Training log saved to %s", training_log_path)


def _extract_top_features(vectorizer: TfidfVectorizer, model: LogisticRegression, top_n: int = 20) -> Dict[str, List[Tuple[str, float]]]:
    feature_names = vectorizer.get_feature_names_out()
    coef = model.coef_[0]
    top_scam_idx = np.argsort(coef)[-top_n:][::-1]
    top_safe_idx = np.argsort(coef)[:top_n]
    top_scam = [(feature_names[i], coef[i]) for i in top_scam_idx]
    top_safe = [(feature_names[i], coef[i]) for i in top_safe_idx]
    return {"top_scam": top_scam, "top_safe": top_safe}


if __name__ == "__main__":
    main()
