"""
ScamShield v1.1 Comprehensive Evaluation
Phase 2: Data Quality Audit
Phase 3/4: Model Comparison + Evaluation Framework
Phase 5: Root Cause Analysis

Usage: python v1_1_evaluation.py
"""
import csv
import json
import math
import os
import re
import sys
import time
import warnings
from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score,
    roc_curve, precision_recall_curve
)
from utils.text import clean_text

RESULTS_DIR = os.path.join(BASE_DIR, "evaluation", "reports", "v1_1_comprehensive")
os.makedirs(RESULTS_DIR, exist_ok=True)

DATASET_PATH = os.path.join(BACKEND_DIR, "data", "scam_dataset.csv")
BENCHMARK_PATH = os.path.join(BASE_DIR, "evaluation", "datasets", "benchmark.json")

# ============================================================
# PHASE 2: DATA QUALITY AUDIT
# ============================================================

def phase2_data_quality_audit() -> Dict[str, Any]:
    print("=" * 70)
    print("PHASE 2: DATA QUALITY AUDIT")
    print("=" * 70)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    texts = [r["text"] for r in rows]
    labels = [r["label"] for r in rows]
    categories = [r["category"] for r in rows]

    print(f"\nTotal rows: {total}")
    scam_count = sum(1 for l in labels if l == "scam")
    safe_count = sum(1 for l in labels if l == "safe")
    print(f"Scam: {scam_count} ({scam_count/total*100:.1f}%)")
    print(f"Safe: {safe_count} ({safe_count/total*100:.1f}%)")

    cat_dist = Counter(categories)
    print(f"\nCategory distribution:")
    for cat, count in sorted(cat_dist.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    lens = [len(t) for t in texts]
    print(f"\nText length stats:")
    print(f"  Min: {min(lens)}, Max: {max(lens)}, Mean: {np.mean(lens):.1f}, Median: {np.median(lens):.1f}")

    unique_texts = len(set(texts))
    print(f"\nUnique texts: {unique_texts} / {total}")
    print(f"Duplicates: {total - unique_texts}")

    text_freq = Counter(texts)
    dupes = [(t, c) for t, c in text_freq.items() if c > 1]
    print(f"  ({len(dupes)} texts appear 2+ times)")

    non_ascii = sum(1 for t in texts if any(ord(c) > 127 for c in t))
    print(f"\nNon-ASCII texts: {non_ascii} / {total}")

    indian_patterns = re.compile(
        r"\b(lor|leh|mah|lah|liao|machan|da|pa|thambi|anna|bro|yaar|boss)\b",
        re.IGNORECASE
    )
    indian_context = sum(1 for t in texts if indian_patterns.search(t))
    print(f"Indian-context texts (Singlish/Manglish): {indian_context}")

    indian_scam_cats = {
        "upi_fraud", "fake_kyc", "govt_scheme", "bank_fraud",
        "tanglish", "bill_scam", "courier_scam", "fake_job",
        "investment_scam", "lottery_scam", "phishing",
        "romance_scam", "tech_support", "loan_scam", "customs_scam"
    }
    print(f"\nCategory counts for Indian scam types:")
    for cat in sorted(indian_scam_cats):
        count = cat_dist.get(cat, 0)
        scam_in_cat = sum(1 for c, l in zip(categories, labels) if c == cat and l == "scam")
        if count > 0:
            print(f"  {cat}: {count} total, {scam_in_cat} scam")

    pipe_char_count = sum(1 for t in texts if "|" in t)
    col_sep_issues = sum(1 for t in texts if t.startswith("http") and "|" not in t)
    print(f"\nPipe char in texts: {pipe_char_count}")
    print(f"Texts starting with URL (no pipe): {col_sep_issues}")

    audit = {
        "total_rows": total,
        "scam_count": scam_count,
        "safe_count": safe_count,
        "scam_pct": round(scam_count / total * 100, 1),
        "category_distribution": dict(cat_dist),
        "min_len": min(lens),
        "max_len": max(lens),
        "mean_len": round(np.mean(lens), 1),
        "median_len": round(np.median(lens), 1),
        "unique_texts": unique_texts,
        "duplicate_count": total - unique_texts,
        "non_ascii_count": non_ascii,
        "indian_context_count": indian_context,
    }
    return audit

# ============================================================
# PHASE 3/4: MODEL COMPARISON
# ============================================================

def train_and_evaluate_models() -> Dict[str, Any]:
    print("\n" + "=" * 70)
    print("PHASE 3/4: MODEL COMPARISON + EVALUATION FRAMEWORK")
    print("=" * 70)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    texts = [clean_text(r["text"]) for r in rows]
    labels = [1 if r["label"] == "scam" else 0 for r in rows]
    categories = [r["category"] for r in rows]

    # Load benchmark
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    bench_texts_raw = [s["text"] for s in benchmark]
    bench_texts_clean = [clean_text(s["text"]) for s in benchmark]
    bench_labels = [1 if s["expected_prediction"] == "scam" else 0 for s in benchmark]

    print(f"\nTraining data: {len(texts)} samples ({sum(labels)} scam)")
    print(f"Benchmark data: {len(bench_texts_clean)} samples ({sum(bench_labels)} scam)")

    # Train/test split on training data for validation
    from sklearn.model_selection import train_test_split
    X_tr, X_te, y_tr, y_te, cat_tr, cat_te = train_test_split(
        texts, labels, categories, test_size=0.2, random_state=42, stratify=labels
    )

    # Vectorizer
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
    X_tr_vec = vectorizer.fit_transform(X_tr)
    X_te_vec = vectorizer.transform(X_te)
    bench_vec = vectorizer.transform(bench_texts_clean)

    models = {
        "LogisticRegression": LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
        "SVM (linear)": SVC(kernel="linear", class_weight="balanced", probability=True, random_state=42, max_iter=2000),
        "SVM (rbf)": SVC(kernel="rbf", class_weight="balanced", probability=True, random_state=42, max_iter=2000),
    }

    # Check if xgboost is available
    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            scale_pos_weight=(len(y_tr) - sum(y_tr)) / sum(y_tr),
            random_state=42, use_label_encoder=False, eval_metric="logloss"
        )
        has_xgb = True
    except ImportError:
        print("XGBoost not available, skipping")
        has_xgb = False

    results = {}
    for name, model in models.items():
        print(f"\n--- Training {name} ---")
        start = time.perf_counter()
        model.fit(X_tr_vec, y_tr)
        train_time = time.perf_counter() - start

        # Cross-validation
        cv_scores = cross_val_score(model, X_tr_vec, y_tr, cv=5, scoring="f1")
        print(f"  CV F1: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")

        # Test set
        y_pred_te = model.predict(X_te_vec)
        y_prob_te = model.predict_proba(X_te_vec)[:, 1] if hasattr(model, "predict_proba") else model.decision_function(X_te_vec)

        te_acc = accuracy_score(y_te, y_pred_te)
        te_prec = precision_score(y_te, y_pred_te)
        te_rec = recall_score(y_te, y_pred_te)
        te_f1 = f1_score(y_te, y_pred_te)
        te_auc = roc_auc_score(y_te, y_prob_te) if hasattr(model, "predict_proba") or hasattr(model, "decision_function") else 0.0

        # Benchmark evaluation
        y_pred_bench = model.predict(bench_vec)
        y_prob_bench = model.predict_proba(bench_vec)[:, 1] if hasattr(model, "predict_proba") else model.decision_function(bench_vec)

        # Per-category benchmark eval
        cat_results = defaultdict(lambda: {"total": 0, "correct": 0, "tp": 0, "fp": 0, "fn": 0, "tn": 0})
        for i, s in enumerate(benchmark):
            cat = s.get("expected_category", "Unknown")
            expected = 1 if s["expected_prediction"] == "scam" else 0
            cat_results[cat]["total"] += 1
            if expected == 1:
                if y_pred_bench[i] == 1:
                    cat_results[cat]["tp"] += 1
                    cat_results[cat]["correct"] += 1
                else:
                    cat_results[cat]["fn"] += 1
            else:
                if y_pred_bench[i] == 0:
                    cat_results[cat]["tn"] += 1
                    cat_results[cat]["correct"] += 1
                else:
                    cat_results[cat]["fp"] += 1

        # ROC curve data for threshold analysis
        fpr, tpr, thresholds = roc_curve(bench_labels, y_prob_bench)
        prec_vals, rec_vals, pr_thresholds = precision_recall_curve(bench_labels, y_prob_bench)

        # Find optimal threshold
        youden = tpr - fpr
        best_idx = np.argmax(youden)
        best_threshold = thresholds[best_idx]

        # Apply best threshold
        y_pred_bench_opt = (y_prob_bench >= best_threshold).astype(int)
        opt_acc = accuracy_score(bench_labels, y_pred_bench_opt)
        opt_prec = precision_score(bench_labels, y_pred_bench_opt)
        opt_rec = recall_score(bench_labels, y_pred_bench_opt)
        opt_f1 = f1_score(bench_labels, y_pred_bench_opt)

        bench_acc = accuracy_score(bench_labels, y_pred_bench)
        bench_prec = precision_score(bench_labels, y_pred_bench)
        bench_rec = recall_score(bench_labels, y_pred_bench)
        bench_f1 = f1_score(bench_labels, y_pred_bench)
        bench_auc = roc_auc_score(bench_labels, y_prob_bench) if hasattr(model, "predict_proba") or hasattr(model, "decision_function") else 0.0

        print(f"  Train time: {train_time:.2f}s")
        print(f"  Test set:   acc={te_acc:.4f} prec={te_prec:.4f} rec={te_rec:.4f} f1={te_f1:.4f} auc={te_auc:.4f}")
        print(f"  Benchmark:  acc={bench_acc:.4f} prec={bench_prec:.4f} rec={bench_rec:.4f} f1={bench_f1:.4f} auc={bench_auc:.4f}")
        print(f"  Optimal threshold: {best_threshold:.4f} -> acc={opt_acc:.4f} prec={opt_prec:.4f} rec={opt_rec:.4f} f1={opt_f1:.4f}")

        # Category breakdown
        cat_breakdown = []
        for cat, stats in sorted(cat_results.items()):
            cat_acc = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
            cat_prec = stats["tp"] / (stats["tp"] + stats["fp"]) if (stats["tp"] + stats["fp"]) > 0 else 0.0
            cat_rec = stats["tp"] / (stats["tp"] + stats["fn"]) if (stats["tp"] + stats["fn"]) > 0 else 0.0
            cat_breakdown.append({
                "category": cat,
                "total": stats["total"],
                "correct": stats["correct"],
                "accuracy": round(cat_acc, 4),
                "precision": round(cat_prec, 4),
                "recall": round(cat_rec, 4),
                "tp": stats["tp"],
                "fp": stats["fp"],
                "fn": stats["fn"],
            })
            print(f"    {cat:30s} acc={cat_acc:.1%} prec={cat_prec:.1%} rec={cat_rec:.1%} n={stats['total']} tp={stats['tp']} fp={stats['fp']} fn={stats['fn']}")

        results[name] = {
            "model": model,
            "train_time": round(train_time, 2),
            "cv_f1_mean": round(cv_scores.mean(), 4),
            "cv_f1_std": round(cv_scores.std(), 4),
            "test": {
                "accuracy": round(te_acc, 4),
                "precision": round(te_prec, 4),
                "recall": round(te_rec, 4),
                "f1": round(te_f1, 4),
                "auc": round(te_auc, 4),
            },
            "benchmark": {
                "accuracy": round(bench_acc, 4),
                "precision": round(bench_prec, 4),
                "recall": round(bench_rec, 4),
                "f1": round(bench_f1, 4),
                "auc": round(bench_auc, 4),
            },
            "benchmark_optimal_threshold": {
                "threshold": round(best_threshold, 4),
                "accuracy": round(opt_acc, 4),
                "precision": round(opt_prec, 4),
                "recall": round(opt_rec, 4),
                "f1": round(opt_f1, 4),
            },
            "category_breakdown": cat_breakdown,
            "confusion_matrix": confusion_matrix(bench_labels, y_pred_bench).tolist(),
            "roc_curve": {
                "fpr": [round(float(x), 4) for x in fpr.tolist()],
                "tpr": [round(float(x), 4) for x in tpr.tolist()],
                "thresholds": [round(float(x), 4) for x in thresholds.tolist()],
            },
            "pr_curve": {
                "precision": [round(float(x), 4) for x in prec_vals.tolist()],
                "recall": [round(float(x), 4) for x in rec_vals.tolist()],
            },
        }

    # Find best model
    best_model_name = max(results, key=lambda n: results[n]["benchmark"]["f1"])
    print(f"\n=== Best model (by benchmark F1): {best_model_name} ===")

    return {
        "best_model_name": best_model_name,
        "model_comparison": results,
        "benchmark_samples": len(benchmark),
        "training_samples": len(texts),
    }

# ============================================================
# PHASE 5: ROOT CAUSE ANALYSIS
# ============================================================

def phase5_root_cause_analysis(model_results: Dict[str, Any]) -> Dict[str, Any]:
    print("\n" + "=" * 70)
    print("PHASE 5: ROOT CAUSE ANALYSIS (FP/FN)")
    print("=" * 70)

    best_name = model_results["best_model_name"]
    best_info = model_results["model_comparison"][best_name]
    model = best_info["model"]

    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        train_rows = list(reader)

    bench_texts = [clean_text(s["text"]) for s in benchmark]

    # Re-fit vectorizer on full training set
    train_texts = [clean_text(r["text"]) for r in train_rows]
    train_labels = [1 if r["label"] == "scam" else 0 for r in train_rows]
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
    X_train_vec = vectorizer.fit_transform(train_texts)
    model.fit(X_train_vec, train_labels)
    bench_vec = vectorizer.transform(bench_texts)

    y_pred = model.predict(bench_vec)
    y_prob = model.predict_proba(bench_vec)[:, 1]

    # Get feature names
    feature_names = vectorizer.get_feature_names_out()

    fns = []
    fps = []
    wcs = []

    for i, s in enumerate(benchmark):
        expected = 1 if s["expected_prediction"] == "scam" else 0
        actual = y_pred[i]

        # Top features for this prediction
        row = bench_vec[i].toarray()[0]
        top_feat_idx = np.argsort(row)[-15:]
        top_feats = [(feature_names[j], float(row[j])) for j in top_feat_idx if row[j] > 0]
        top_feats.reverse()

        entry = {
            "id": s["id"],
            "text": s["text"],
            "expected_category": s.get("expected_category", "Unknown"),
            "confidence": round(float(y_prob[i]), 4),
            "top_features": top_feats,
        }

        if expected == 1 and actual == 0:
            fns.append(entry)
        elif expected == 0 and actual == 1:
            fps.append(entry)
        elif expected == 1 and actual == 1:
            got_cat = s.get("expected_category", "")
            # For now, just record successful predictions
            pass

    # Analyze FP patterns
    fp_patterns = Counter()
    for fp in fps:
        text = fp["text"].lower()
        if any(u in text for u in ["otp", "verification code", "one time"]):
            fp_patterns["otp_triggered"] += 1
        if "http" in text:
            fp_patterns["url_present"] += 1
        if any(b in text for b in ["sbi", "hdfc", "icici", "axis", "bank"]):
            fp_patterns["bank_mentioned"] += 1
        if any(p in text for p in ["rs ", "pay ", "fee", "price"]):
            fp_patterns["money_mentioned"] += 1
        if any(w in text for w in ["urgent", "immediately", "now", "expire"]):
            fp_patterns["urgency_mentioned"] += 1

    fn_patterns = Counter()
    for fn in fns:
        text = fn["text"].lower()
        if not any(u in text for u in ["urgent", "immediately", "now"]):
            fn_patterns["no_urgency"] += 1
        if not any(m in text for m in ["rs ", "pay ", "fee", "money"]):
            fn_patterns["no_money_mention"] += 1
        if "http" not in text:
            fn_patterns["no_url"] += 1
        if any(w in text for w in ["dear", "hello", "hi"]):
            fn_patterns["greeting_pattern"] += 1

    # Check: is the model relying on training set similarities?
    # For each FN, find most similar training texts
    fn_train_similarity = []
    for fn in fns:
        fn_vec = vectorizer.transform([clean_text(fn["text"])])
        similarities = (X_train_vec * fn_vec.T).toarray().flatten()
        top_train_idx = np.argsort(similarities)[-5:][::-1]
        top_sims = []
        for idx in top_train_idx:
            if similarities[idx] > 0:
                top_sims.append({
                    "train_text": train_rows[idx]["text"][:80],
                    "train_label": train_rows[idx]["label"],
                    "train_category": train_rows[idx]["category"],
                    "similarity": round(float(similarities[idx]), 4),
                })
        fn_train_similarity.append({
            "id": fn["id"],
            "text": fn["text"][:80],
            "category": fn["expected_category"],
            "confidence": fn["confidence"],
            "top_similar_training": top_sims,
        })

    print(f"\nFalse Negatives: {len(fns)}")
    for fn in fns:
        print(f"  [{fn['id']}] conf={fn['confidence']:.4f} cat={fn['expected_category']}")
        print(f"    Text: {fn['text'][:100]}")
        print(f"    Top features: {', '.join(f'{f[0]}({f[1]:.3f})' for f in fn['top_features'][:5])}")

    print(f"\nFalse Positives: {len(fps)}")
    for fp in fps:
        print(f"  [{fp['id']}] conf={fp['confidence']:.4f} cat={fp['expected_category']}")
        print(f"    Text: {fp['text'][:100]}")
        print(f"    Top features: {', '.join(f'{f[0]}({f[1]:.3f})' for f in fp['top_features'][:5])}")

    print(f"\nFP pattern breakdown:")
    for pattern, count in fp_patterns.most_common():
        print(f"  {pattern}: {count}/{len(fps)} ({count/len(fps)*100:.0f}% of FPs)" if fps else f"  {pattern}: 0")

    print(f"\nFN pattern breakdown:")
    for pattern, count in fn_patterns.most_common():
        print(f"  {pattern}: {count}/{len(fns)} ({count/len(fns)*100:.0f}% of FNs)" if fns else f"  {pattern}: 0")

    # Frenquency analysis: what categories are FNs/FP concentated in?
    fn_cats = Counter(fn["expected_category"] for fn in fns)
    fp_cats = Counter(fp["expected_category"] for fp in fps)

    print(f"\nFN by category:")
    for cat, count in fn_cats.most_common():
        total_in_bench = sum(1 for s in benchmark if s.get("expected_category") == cat and s["expected_prediction"] == "scam")
        print(f"  {cat}: {count}/{total_in_bench} ({count/total_in_bench*100:.0f}%)" if total_in_bench else f"  {cat}: {count}")

    print(f"\nFP by category:")
    for cat, count in fp_cats.most_common():
        total_in_bench = sum(1 for s in benchmark if s.get("expected_category") == cat and s["expected_prediction"] == "safe")
        print(f"  {cat}: {count}/{total_in_bench} ({count/total_in_bench*100:.0f}%)" if total_in_bench else f"  {cat}: {count}")

    # Which features are globally most scam-indicative?
    if hasattr(model, "coef_"):
        coef = model.coef_[0]
        top_scam_idx = np.argsort(coef)[-20:][::-1]
        top_safe_idx = np.argsort(coef)[:20]
        print(f"\nTop 20 scam-indicative features:")
        for idx in top_scam_idx:
            print(f"  +{coef[idx]:+.4f}  {feature_names[idx]}")
        print(f"\nTop 20 safe-indicative features (most negative):")
        for idx in top_safe_idx:
            print(f"  {coef[idx]:+.4f}  {feature_names[idx]}")

    return {
        "false_negatives": fns,
        "false_positives": fps,
        "fn_patterns": dict(fn_patterns),
        "fp_patterns": dict(fp_patterns),
        "fn_categories": dict(fn_cats),
        "fp_categories": dict(fp_cats),
        "fn_train_similarity": fn_train_similarity,
    }

# ============================================================
# MAIN
# ============================================================

def run_current_model_on_benchmark() -> Dict[str, Any]:
    """Run the current production model on benchmark.json"""
    print("\n" + "=" * 70)
    print("RUNNING CURRENT PRODUCTION MODEL ON BENCHMARK")
    print("=" * 70)

    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    model_path = os.path.join(BACKEND_DIR, "models", "model.joblib")
    vec_path = os.path.join(BACKEND_DIR, "models", "vectorizer.joblib")

    if not os.path.exists(model_path):
        print("Current production model not found, retraining...")
        from train import main as train_main
        train_main()

    model = joblib.load(model_path)
    vec = joblib.load(vec_path)

    bench_texts = [clean_text(s["text"]) for s in benchmark]
    bench_vec = vec.transform(bench_texts)
    bench_labels = [1 if s["expected_prediction"] == "scam" else 0 for s in benchmark]

    y_pred = model.predict(bench_vec)
    y_prob = model.predict_proba(bench_vec)[:, 1]

    acc = accuracy_score(bench_labels, y_pred)
    prec = precision_score(bench_labels, y_pred)
    rec = recall_score(bench_labels, y_pred)
    f1 = f1_score(bench_labels, y_pred)
    auc = roc_auc_score(bench_labels, y_prob)

    cm = confusion_matrix(bench_labels, y_pred).tolist()

    cat_results = defaultdict(lambda: {"total": 0, "correct": 0})
    for i, s in enumerate(benchmark):
        cat = s.get("expected_category", "Unknown")
        cat_results[cat]["total"] += 1
        if (s["expected_prediction"] == "scam" and y_pred[i] == 1) or \
           (s["expected_prediction"] == "safe" and y_pred[i] == 0):
            cat_results[cat]["correct"] += 1

    cat_breakdown = []
    for cat, stats in sorted(cat_results.items()):
        cat_breakdown.append({
            "category": cat,
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(stats["correct"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
        })

    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1:        {f1:.4f}")
    print(f"  AUC:       {auc:.4f}")
    print(f"  Confusion: {cm}")
    print(f"\n  Category breakdown:")
    for c in cat_breakdown:
        bar = "=" * int(c["accuracy"] * 30)
        print(f"    {c['category']:30s} {c['accuracy']:.1%} {c['correct']:3d}/{c['total']:<3d} {bar}")

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "auc": round(auc, 4),
        "confusion_matrix": cm,
        "category_breakdown": cat_breakdown,
    }


def main():
    start = time.time()
    print("=" * 70)
    print("  SCAMSHIELD v1.1 COMPREHENSIVE EVALUATION")
    print(f"  Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Phase 2
    data_audit = phase2_data_quality_audit()

    # Current model eval
    current_model = run_current_model_on_benchmark()

    # Phase 3/4
    model_comparison = train_and_evaluate_models()

    # Phase 5
    root_cause = phase5_root_cause_analysis(model_comparison)

    elapsed = time.time() - start
    print(f"\n{'=' * 70}")
    print(f"  Total time: {elapsed:.1f}s")
    print(f"  Results saved to: {RESULTS_DIR}")
    print(f"{'=' * 70}")

    best_name = model_comparison["best_model_name"]
    best_info = model_comparison["model_comparison"][best_name]
    bm = best_info["benchmark"]

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(elapsed, 1),
        "phase2_data_quality_audit": data_audit,
        "current_production_model": current_model,
        "phase3_4_model_comparison": {
            "best_model": best_name,
            "models": {
                name: {
                    "train_time_seconds": info["train_time"],
                    "cv_f1_mean": info["cv_f1_mean"],
                    "cv_f1_std": info["cv_f1_std"],
                    "test_set": info["test"],
                    "benchmark": info["benchmark"],
                    "benchmark_optimal_threshold": info["benchmark_optimal_threshold"],
                    "category_breakdown": info["category_breakdown"],
                    "confusion_matrix": info["confusion_matrix"],
                }
                for name, info in model_comparison["model_comparison"].items()
            },
            "roc_data": {
                name: info["roc_curve"]
                for name, info in model_comparison["model_comparison"].items()
            },
            "pr_data": {
                name: info["pr_curve"]
                for name, info in model_comparison["model_comparison"].items()
            },
        },
        "phase5_root_cause_analysis": {
            "false_negatives": root_cause["fn_categories"],
            "false_positives": root_cause["fp_categories"],
            "fn_patterns": root_cause["fn_patterns"],
            "fp_patterns": root_cause["fp_patterns"],
            "fn_count": len(root_cause["false_negatives"]),
            "fp_count": len(root_cause["false_positives"]),
            "fn_details": root_cause["false_negatives"],
            "fp_details": root_cause["false_positives"],
            "fn_train_similarity": root_cause["fn_train_similarity"],
        },
        "actionable_recommendations": generate_recommendations(
            data_audit, current_model, model_comparison, root_cause
        ),
    }

    report_path = os.path.join(RESULTS_DIR, "v1_1_comprehensive_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    # Print summary
    print_summary(report)

    return report


def generate_recommendations(
    data_audit: Dict, current_model: Dict,
    model_comparison: Dict, root_cause: Dict
) -> List[Dict[str, Any]]:
    recs = []

    best_name = model_comparison["best_model_name"]
    best_info = model_comparison["model_comparison"][best_name]
    bm = best_info["benchmark"]

    # Dataset recommendations
    if data_audit["scam_count"] < 2000:
        recs.append({
            "area": "Dataset",
            "priority": "CRITICAL",
            "finding": f"Only {data_audit['scam_count']} scam samples in training set",
            "recommendation": "Expand scam dataset to 3000-5000 labelled Indian scam messages",
        })
    if data_audit["duplicate_count"] > 100:
        recs.append({
            "area": "Dataset",
            "priority": "HIGH",
            "finding": f"{data_audit['duplicate_count']} duplicate texts inflate metrics",
            "recommendation": "Deduplicate training data, keep only unique texts",
        })
    if data_audit["indian_context_count"] < 500:
        recs.append({
            "area": "Dataset",
            "priority": "CRITICAL",
            "finding": f"Only ~{data_audit['indian_context_count']} Indian-context messages",
            "recommendation": "Add Indian scam patterns: UPI, Aadhaar, KYC, courier, fake job, electricity bill",
        })

    # Model recommendations
    for name, info in model_comparison["model_comparison"].items():
        ibm = info["benchmark"]
        if name == best_name:
            recs.append({
                "area": "Model Selection",
                "priority": "HIGH",
                "finding": f"Best model: {name} (F1={ibm['f1']:.4f}, AUC={ibm['auc']:.4f})",
                "recommendation": f"Replace current logistic regression with {name}",
            })

    # Threshold
    for name, info in model_comparison["model_comparison"].items():
        if name == best_name:
            opt = info["benchmark_optimal_threshold"]
            if opt["threshold"] != 0.5:
                recs.append({
                    "area": "Threshold Tuning",
                    "priority": "HIGH",
                    "finding": f"Optimal threshold={opt['threshold']:.4f} (current=0.5)",
                    "recommendation": f"Change decision threshold from 0.5 to {opt['threshold']:.4f} (improves F1 from {bm['f1']:.4f} to {opt['f1']:.4f})",
                })

    # FP/FN patterns
    fp_count = root_cause.get("fp_count", 0)
    fn_count = root_cause.get("fn_count", 0)
    if fp_count > 5:
        recs.append({
            "area": "False Positives",
            "priority": "HIGH",
            "finding": f"{fp_count} false positives detected",
            "recommendation": f"Top FP patterns: {', '.join(f'{k}({v})' for k, v in root_cause.get('fp_patterns', {}).items())}",
        })
    if fn_count > 5:
        recs.append({
            "area": "False Negatives",
            "priority": "HIGH",
            "finding": f"{fn_count} false negatives detected",
            "recommendation": f"Top FN patterns: {', '.join(f'{k}({v})' for k, v in root_cause.get('fn_patterns', {}).items())}",
        })

    # Category-specific recommendations
    fn_cats = root_cause.get("fn_categories", {})
    for cat, count in fn_cats.items():
        if count >= 2:
            recs.append({
                "area": "Category Recall",
                "priority": "MEDIUM",
                "finding": f"{cat}: {count} false negatives",
                "recommendation": f"Add more {cat} samples to training set; create specific rules for {cat}",
            })

    return recs


def print_summary(report: Dict[str, Any]):
    print("\n" + "=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)

    dq = report["phase2_data_quality_audit"]
    print(f"\nData Quality:")
    print(f"  {dq['total_rows']} rows ({dq['scam_count']} scam, {dq['safe_count']} safe)")
    print(f"  {dq['duplicate_count']} duplicates, {dq['indian_context_count']} Indian-context")
    print(f"  Mean len: {dq['mean_len']:.0f} chars")

    cm = report["current_production_model"]
    print(f"\nCurrent Production Model (benchmark={cm.get('accuracy', 0)*100:.1f}% acc):")
    print(f"  Acc={cm.get('accuracy', 0):.4f} Prec={cm.get('precision', 0):.4f} Rec={cm.get('recall', 0):.4f} F1={cm.get('f1', 0):.4f} AUC={cm.get('auc', 0):.4f}")

    mc = report["phase3_4_model_comparison"]
    best = mc["best_model"]
    print(f"\nBest Model: {best}")
    for name, info in mc["models"].items():
        b = info["benchmark"]
        marker = " <-- BEST" if name == best else ""
        print(f"  {name:25s} Acc={b['accuracy']:.4f} Prec={b['precision']:.4f} Rec={b['recall']:.4f} F1={b['f1']:.4f} AUC={b['auc']:.4f}{marker}")

    rca = report["phase5_root_cause_analysis"]
    print(f"\nRoot Cause:")
    print(f"  {rca['fn_count']} FNs, {rca['fp_count']} FPs")

    print(f"\nRecommendations:")
    for i, rec in enumerate(report.get("actionable_recommendations", []), 1):
        print(f"  [{rec['priority']:8s}] [{rec['area']:20s}] {rec['recommendation']}")

    print(f"\nFull report saved to: {os.path.join(RESULTS_DIR, 'v1_1_comprehensive_report.json')}")


if __name__ == "__main__":
    main()