"""
Dump every false positive from gold eval against full pipeline.
Saves to backend/tests/regression/gold_false_positives.json
"""
import csv, sys, os, json
from pathlib import Path

BACKEND_DIR = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from services.orchestrator import analyze_text

GOLD_PATH = Path(__file__).resolve().parent.parent.parent.parent / "datasets" / "gold" / "gold_dataset.csv"
OUT_PATH = Path(__file__).resolve().parent / "gold_false_positives.json"

texts, labels, cats = [], [], []
with open(GOLD_PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        texts.append(r["text"])
        labels.append(1 if r["is_scam"].strip().lower() == "true" else 0)
        cats.append(r["category"])

false_positives = []
for i, (text, label, cat) in enumerate(zip(texts, labels, cats)):
    if label != 0:
        continue  # only care about safe messages
    result = analyze_text(text)
    pred = result.get("prediction", "safe")
    if pred == "scam":
        fp = {
            "index": i,
            "text": text,
            "gold_category": cat,
            "ml_prediction": result.get("prediction"),
            "confidence": result.get("confidence", 0),
            "risk_level": result.get("risk_level"),
            "rule_score": result.get("rule_score", 0),
            "rule_label": result.get("rule_label"),
            "reasons": result.get("reasons", []),
            "detected_indicators": result.get("detected_indicators", []),
            "scam_category": result.get("scam_category"),
            "threats": result.get("threats", []),
            "summary": result.get("summary", ""),
        }
        false_positives.append(fp)
    if (i + 1) % 50 == 0:
        print(f"  {i+1}/{len(texts)} scanned...")

print(f"\nTotal false positives: {len(false_positives)} out of {sum(1 for l in labels if l==0)} safe messages")

# Save
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(false_positives, f, indent=2, ensure_ascii=False)
print(f"Saved to {OUT_PATH}")

# Quick summary
from collections import Counter
reason_counts = Counter()
for fp in false_positives:
    for r in fp["reasons"]:
        reason_counts[r] += 1

print(f"\nTop reasons across all FPs:")
for reason, count in reason_counts.most_common(10):
    print(f"  {count:3d}x  {reason}")

indicator_counts = Counter()
for fp in false_positives:
    for ind in fp["detected_indicators"]:
        indicator_counts[ind] += 1

print(f"\nTop indicators across all FPs:")
for ind, count in indicator_counts.most_common(10):
    print(f"  {count:3d}x  {ind}")
