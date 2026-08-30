"""
Evaluate gold dataset against the FULL pipeline (services.orchestrator.analyze_text()).
Not raw model.predict() — this runs every message through the complete analysis pipeline.
"""
import csv, sys, os, time
from pathlib import Path
from collections import defaultdict, Counter

BACKEND_DIR = str(Path(__file__).resolve().parent.parent.parent / "backend")
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from services.orchestrator import analyze_text

GOLD_PATH = Path(__file__).parent / "gold_dataset.csv"

print("Loading gold dataset...")
texts, labels, cats, langs = [], [], [], []
with open(GOLD_PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        texts.append(r["text"])
        labels.append(1 if r["is_scam"].strip().lower() == "true" else 0)
        cats.append(r["category"])
        langs.append(r.get("language", "en"))

print(f"Loaded {len(texts)} gold samples. Running full pipeline...")

y_true = []
y_pred = []
errors = []

for i, (text, label, cat) in enumerate(zip(texts, labels, cats)):
    try:
        result = analyze_text(text)
        # Use ML prediction field ("safe"/"scam") as the binary output
        ml_pred = result.get("prediction", "safe")
        pred = 1 if ml_pred == "scam" else 0
        y_true.append(label)
        y_pred.append(pred)
        if pred != label:
            errors.append({
                "text": text[:120],
                "category": cat,
                "true": "scam" if label == 1 else "safe",
                "predicted": "scam" if pred == 1 else "safe",
                "confidence": result.get("confidence", 0),
                "risk_level": result.get("risk_level", "?"),
            })
    except Exception as e:
        y_true.append(label)
        y_pred.append(0)  # treat errors as safe (conservative)
        errors.append({
            "text": text[:120],
            "category": cat,
            "true": "scam" if label == 1 else "safe",
            "predicted": f"ERROR: {e}",
            "confidence": 0,
            "risk_level": "ERROR",
        })
    if (i + 1) % 50 == 0:
        print(f"  {i+1}/{len(texts)} done...")

# Compute metrics
tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)

precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
acc = (tp + tn) / len(y_true) if y_true else 0.0

print(f"\n=== FULL PIPELINE GOLD EVALUATION ===")
print(f"Date: 2026-08-30")
print(f"Method: services.orchestrator.analyze_text() (full pipeline, not raw model)")
print(f"Samples: {len(y_true)}")
print(f"Accuracy:  {acc:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1:        {f1:.4f}")
print(f"FPR:       {fpr:.4f}")
print(f"FNR:       {fnr:.4f}")
print(f"Confusion: TP={tp} FP={fp} FN={fn} TN={tn}")

# Per-category
cat_groups = defaultdict(lambda: {"tp":0,"fp":0,"fn":0,"tn":0})
for t, p, c in zip(y_true, y_pred, cats):
    if t == 1 and p == 1: cat_groups[c]["tp"] += 1
    elif t == 0 and p == 1: cat_groups[c]["fp"] += 1
    elif t == 1 and p == 0: cat_groups[c]["fn"] += 1
    else: cat_groups[c]["tn"] += 1

print(f"\nPer-category (scam categories with FPs or FNs):")
for c in sorted(cat_groups):
    m = cat_groups[c]
    total = m["tp"]+m["fp"]+m["fn"]+m["tn"]
    cat_prec = m["tp"]/(m["tp"]+m["fp"]) if (m["tp"]+m["fp"])>0 else 0
    cat_rec = m["tp"]/(m["tp"]+m["fn"]) if (m["tp"]+m["fn"])>0 else 0
    if m["fp"] > 0 or m["fn"] > 0:
        print(f"  {c:35s} TP={m['tp']:3d} FP={m['fp']:3d} FN={m['fn']:3d} TN={m['tn']:3d} (n={total})")

# Top errors
print(f"\nTop false negatives (scam missed):")
fns = [e for e in errors if e["true"] == "scam"]
for e in fns[:10]:
    print(f"  [{e['category']}] conf={e['confidence']:.2f} risk={e['risk_level']}: {e['text'][:80]}")

print(f"\nTop false positives (safe flagged as scam):")
fps = [e for e in errors if e["true"] == "safe"]
for e in fps[:10]:
    print(f"  [{e['category']}] conf={e['confidence']:.2f} risk={e['risk_level']}: {e['text'][:80]}")
