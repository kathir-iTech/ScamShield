"""Analyze new false negatives after refinement fix."""
import csv, sys, os, json
from pathlib import Path
from collections import Counter

sys.path.insert(0, r"D:\Developer\Desktop\ScamShield\backend")
os.chdir(r"D:\Developer\Desktop\ScamShield\backend")
from services.orchestrator import analyze_text

texts, labels, cats = [], [], []
with open(r"D:\Developer\Desktop\ScamShield\datasets\gold\gold_dataset.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        texts.append(r["text"])
        labels.append(1 if r["is_scam"].strip().lower() == "true" else 0)
        cats.append(r["category"])

# Find new FNs (scam messages now classified as safe)
new_fns = []
for i, (t, l, c) in enumerate(zip(texts, labels, cats)):
    if l != 1:
        continue
    r = analyze_text(t)
    refined = r.get("refined_prediction", r.get("prediction", "safe"))
    if refined == "safe":
        new_fns.append({
            "text": t[:120],
            "category": c,
            "ml_pred": r.get("prediction"),
            "refined_pred": refined,
            "confidence": r.get("confidence", 0),
            "refined_score": r.get("refined_assessment_score", 0),
            "applied_rules": r.get("refinement_applied_rules", []),
        })

print(f"New FNs (scam->safe): {len(new_fns)}")
print()

# Group by category
cat_counts = Counter(fn["category"] for fn in new_fns)
print("By category:")
for cat, n in cat_counts.most_common():
    print(f"  {n:3d}x  {cat}")

print()
# Show samples with applied rules
for fn in new_fns[:15]:
    rule_ids = [r.get("rule_id", "?") for r in fn["applied_rules"]]
    print(f"  [{fn['category']}] conf={fn['confidence']:.2f} rules={rule_ids}")
    print(f"    {fn['text']}")
    print()
