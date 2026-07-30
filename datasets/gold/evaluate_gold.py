"""
Evaluate the current production model on the gold evaluation dataset.
NEVER uses gold data for training — only final evaluation.
"""

import csv, json, sys, os
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, matthews_corrcoef,
    classification_report,
)

BACKEND_DIR = str(Path(__file__).resolve().parent.parent.parent / "backend")
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from config.settings import MODEL_PATH, VECTORIZER_PATH
from utils.text import clean_text
import joblib

GOLD_PATH = Path(__file__).parent / "gold_dataset.csv"
EVAL_REPORT_PATH = Path(__file__).parent / "GOLD_EVALUATION_REPORT.md"
ERROR_PATH = Path(__file__).parent / "ERROR_ANALYSIS_GOLD.md"

print("Loading production model...")
model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)
print(f"Model loaded from {MODEL_PATH}")

print("Loading gold dataset...")
texts, labels, cats, langs = [], [], [], []
with open(GOLD_PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        texts.append(r["text"])
        labels.append(1 if r["is_scam"].strip().lower() == "true" else 0)
        cats.append(r["category"])
        langs.append(r.get("language", "en"))

print(f"Loaded {len(texts)} gold samples")

# Evaluate
X_vec = vectorizer.transform([clean_text(t) for t in texts])
y_pred = model.predict(X_vec)
y_proba = model.predict_proba(X_vec)[:, 1]

# Overall metrics
acc = accuracy_score(labels, y_pred)
prec = precision_score(labels, y_pred, zero_division=0)
rec = recall_score(labels, y_pred, zero_division=0)
f1 = f1_score(labels, y_pred, zero_division=0)
mcc = matthews_corrcoef(labels, y_pred)
cm = confusion_matrix(labels, y_pred, labels=[0, 1])
tn, fp, fn, tp = cm.ravel()
fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0

try:
    auc_val = roc_auc_score(labels, y_proba) if len(set(labels)) > 1 else 0.0
except Exception:
    auc_val = 0.0

print(f"\n=== GOLD EVALUATION RESULTS ===")
print(f"Accuracy:  {acc:.4f}")
print(f"Precision: {prec:.4f}")
print(f"Recall:    {rec:.4f}")
print(f"F1:        {f1:.4f}")
print(f"MCC:       {mcc:.4f}")
print(f"ROC-AUC:   {auc_val:.4f}")
print(f"FPR:       {fpr:.4f}")
print(f"FNR:       {fnr:.4f}")
print(f"Specificity: {spec:.4f}")
print(f"Confusion: TP={tp} FP={fp} FN={fn} TN={tn}")

# Per-category metrics
cat_results = {}
cat_groups = defaultdict(list)
for t, l, c in zip(texts, labels, cats):
    cat_groups[c].append((t, l))

for c, samples in sorted(cat_groups.items()):
    ct = [s[0] for s in samples]
    cl = [s[1] for s in samples]
    cX = vectorizer.transform([clean_text(t) for t in ct])
    cp = model.predict(cX)
    cat_results[c] = {
        "total": len(samples),
        "accuracy": accuracy_score(cl, cp),
        "precision": precision_score(cl, cp, zero_division=0),
        "recall": recall_score(cl, cp, zero_division=0),
        "f1": f1_score(cl, cp, zero_division=0),
        "f1_legit": f1_score(cl, cp, pos_label=0, zero_division=0),
        "tp": int(confusion_matrix(cl, cp, labels=[0, 1]).ravel()[3]),
        "fp": int(confusion_matrix(cl, cp, labels=[0, 1]).ravel()[1]),
        "fn": int(confusion_matrix(cl, cp, labels=[0, 1]).ravel()[2]),
        "tn": int(confusion_matrix(cl, cp, labels=[0, 1]).ravel()[0]),
    }
    print(f"  {c:35s} F1={cat_results[c]['f1']:.4f} (n={cat_results[c]['total']})")

# Per-language metrics
lang_results = {}
lang_groups = defaultdict(list)
for t, l, la in zip(texts, labels, langs):
    lang_groups[la].append((t, l))

for la, samples in sorted(lang_groups.items()):
    lt = [s[0] for s in samples]
    ll = [s[1] for s in samples]
    lX = vectorizer.transform([clean_text(t) for t in lt])
    lp = model.predict(lX)
    lang_results[la] = {
        "total": len(samples),
        "accuracy": accuracy_score(ll, lp),
        "f1": f1_score(ll, lp, zero_division=0),
    }

# Error analysis
fp_indices = [i for i, (true, pred) in enumerate(zip(labels, y_pred)) if true == 0 and pred == 1]
fn_indices = [i for i, (true, pred) in enumerate(zip(labels, y_pred)) if true == 1 and pred == 0]

fp_texts = [(texts[i], cats[i], y_proba[i]) for i in fp_indices]
fn_texts = [(texts[i], cats[i], y_proba[i]) for i in fn_indices]

fp_cats = Counter(cats[i] for i in fp_indices)
fn_cats = Counter(cats[i] for i in fn_indices)

# Generate evaluation report
with open(EVAL_REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("# Gold Evaluation Report\n\n")
    f.write(f"**Date:** 2026-07-30\n")
    f.write(f"**Model:** TF-IDF + LogisticRegression (production)\n")
    f.write(f"**Gold dataset:** `gold_dataset.csv` ({len(texts)} samples)\n\n")
    f.write("## Overall Metrics\n\n")
    f.write("| Metric | Value |\n")
    f.write("|--------|-------|\n")
    f.write(f"| Accuracy | {acc:.4f} |\n")
    f.write(f"| Precision | {prec:.4f} |\n")
    f.write(f"| Recall | {rec:.4f} |\n")
    f.write(f"| F1 | {f1:.4f} |\n")
    f.write(f"| MCC | {mcc:.4f} |\n")
    f.write(f"| ROC-AUC | {auc_val:.4f} |\n")
    f.write(f"| FPR | {fpr:.4f} |\n")
    f.write(f"| FNR | {fnr:.4f} |\n")
    f.write(f"| Specificity | {spec:.4f} |\n\n")
    f.write("## Confusion Matrix\n\n")
    f.write("```\n")
    f.write(f"            Predicted\n")
    f.write(f"             Safe  Scam\n")
    f.write(f"Actual Safe  {tn:4d}  {fp:4d}\n")
    f.write(f"       Scam  {fn:4d}  {tp:4d}\n")
    f.write("```\n\n")
    f.write(f"TP={tp} FP={fp} FN={fn} TN={tn}\n\n")
    f.write("## Per-Category Performance\n\n")
    f.write("| Category | Samples | F1 (Scam) | F1 (Legit) | Acc | TP | FP | FN | TN |\n")
    f.write("|----------|---------|-----------|------------|-----|----|----|----|----|\n")
    legit_cats = {"LEGITIMATE_BANKING","LEGITIMATE_UPI","LEGITIMATE_COURIER","LEGITIMATE_GOVERNMENT","LEGITIMATE_OTP","LEGITIMATE_TELECOM","LEGITIMATE_COLLEGE","LEGITIMATE_UTILITY","LEGITIMATE_SHOPPING","LEGITIMATE_PERSONAL"}
    for c, m in sorted(cat_results.items()):
        display_f1 = m['f1_legit'] if c in legit_cats else m['f1']
        f.write(f"| {c} | {m['total']} | {m['f1']:.4f} | {m['f1_legit']:.4f} | {m['accuracy']:.4f} | {m['tp']} | {m['fp']} | {m['fn']} | {m['tn']} |\n")
    f.write("\n## Per-Language Performance\n\n")
    f.write("| Language | Samples | Accuracy | F1 |\n")
    f.write("|----------|---------|----------|----|\n")
    for la, m in sorted(lang_results.items()):
        f.write(f"| {la} | {m['total']} | {m['accuracy']:.4f} | {m['f1']:.4f} |\n")

print(f"\nEvaluation report saved to {EVAL_REPORT_PATH}")

# Generate error analysis
with open(ERROR_PATH, "w", encoding="utf-8") as f:
    f.write("# Error Analysis: Gold Dataset\n\n")
    f.write(f"**Total errors:** {len(fp_indices) + len(fn_indices)} / {len(texts)} ({100*(len(fp_indices)+len(fn_indices))/len(texts):.1f}%)\n\n")
    f.write("## False Positives (Legitimate flagged as Scam)\n\n")
    f.write(f"**Count:** {len(fp_indices)}\n\n")
    f.write("| Text | Category | Confidence |\n")
    f.write("|------|----------|------------|\n")
    for txt, cat, prob in sorted(fp_texts, key=lambda x: -x[2]):
        f.write(f"| {txt[:80]} | {cat} | {prob:.3f} |\n")
    f.write(f"\n**FP by Category:**\n\n")
    for c, n in fp_cats.most_common():
        f.write(f"- {c}: {n}\n")
    f.write("\n## False Negatives (Scam flagged as Legitimate)\n\n")
    f.write(f"**Count:** {len(fn_indices)}\n\n")
    f.write("| Text | Category | Confidence |\n")
    f.write("|------|----------|------------|\n")
    for txt, cat, prob in sorted(fn_texts, key=lambda x: x[2]):
        f.write(f"| {txt[:80]} | {cat} | {prob:.3f} |\n")
    f.write(f"\n**FN by Category:**\n\n")
    for c, n in fn_cats.most_common():
        f.write(f"- {c}: {n}\n")
    f.write("\n## Weak Categories\n\n")
    weak_cats = [(c, m) for c, m in cat_results.items() if m['f1'] < 0.80 and c not in legit_cats]
    if weak_cats:
        f.write("### Scam Categories (F1 < 0.80)\n\n")
        for c, m in sorted(weak_cats, key=lambda x: x[1]['f1']):
            f.write(f"- **{c}**: F1={m['f1']:.4f}, n={m['total']}\n")
    weak_legit = [(c, m) for c, m in cat_results.items() if m['f1_legit'] < 0.80 and c in legit_cats]
    if weak_legit:
        f.write("\n### Legitimate Categories (F1_legit < 0.80)\n\n")
        for c, m in sorted(weak_legit, key=lambda x: x[1]['f1_legit']):
            f.write(f"- **{c}**: F1_legit={m['f1_legit']:.4f}, n={m['total']}\n")
    f.write("\n## Language-Specific Failures\n\n")
    for la, m in sorted(lang_results.items()):
        mis = sum(1 for i in fp_indices + fn_indices if langs[i] == la)
        f.write(f"- **{la}**: {m['total']} samples, {mis} errors (F1={m['f1']:.4f})\n")
    f.write("\n## Recommendations\n\n")
    f.write("### Dataset Improvements\n\n")
    if fp_cats:
        f.write("- **FP categories to augment:** Add more diverse samples for ")
        f.write(", ".join(f"{c} ({n})" for c, n in fp_cats.most_common(5)))
        f.write("\n")
    if fn_cats:
        f.write("- **FN categories to augment:** Add more scam variants for ")
        f.write(", ".join(f"{c} ({n})" for c, n in fn_cats.most_common(5)))
        f.write("\n")
    if weak_cats:
        f.write("- **Weak scam categories**: Focus on ")
        f.write(", ".join(c for c, _ in weak_cats))
        f.write("\n")
    if weak_legit:
        f.write("- **Weak legitimate categories**: Focus on ")
        f.write(", ".join(c for c, _ in weak_legit))
        f.write("\n")
    f.write("- **Non-English data**: Expand ")
    for la, m in sorted(lang_results.items()):
        if la != "en":
            mis = sum(1 for i in fp_indices + fn_indices if langs[i] == la)
            if mis > 0:
                f.write(f"{la} ({mis} errors in {m['total']} samples), ")
    f.write("\n")
    f.write("\n### Model Improvements (if justified)\n\n")
    f.write("- **SVM + CalibratedClassifierCV**: Test if probability calibration improves AUC\n")
    miss_rate = (len(fp_indices) + len(fn_indices)) / len(texts)
    if miss_rate > 0.10:
        f.write("- **Model retrain** may be warranted if error rate exceeds 10% on growing gold dataset\n")

print(f"Error analysis saved to {ERROR_PATH}")
print("Done!")
