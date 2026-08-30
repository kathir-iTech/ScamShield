"""Detailed FP analysis: show assessment scores, ML confidence, and FP rules triggered."""
import csv, sys, os
from collections import Counter

sys.path.insert(0, r"D:\Developer\Desktop\ScamShield\backend")
os.chdir(r"D:\Developer\Desktop\ScamShield\backend")
from services.orchestrator import analyze_text

texts, labels, cats = [], [], []
with open(r"D:\Developer\Desktop\ScamShield\datasets\gold\gold_dataset.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        texts.append(r["text"])
        labels.append(1 if r["is_scam"].strip().lower() == "true" else 0)
        cats.append(r.get("category", ""))

# Collect all FPs and FNs
fps = []
fns = []
for i, (t, l, c) in enumerate(zip(texts, labels, cats)):
    r = analyze_text(t)
    refined = r.get("refined_prediction", r.get("prediction", "safe"))
    pred = 1 if refined == "scam" else 0
    if l == 0 and pred == 1:
        fps.append({"text": t, "cat": c, "conf": r.get("confidence", 0),
                     "score": r.get("assessment_score", 0),
                     "rules": [x["rule_id"] for x in r.get("refinement_applied_rules", []) if x.get("category") == "fp_reduction"]})
    elif l == 1 and pred == 0:
        fns.append({"text": t, "cat": c, "conf": r.get("confidence", 0),
                     "score": r.get("assessment_score", 0),
                     "refined_score": r.get("refined_assessment_score", 0),
                     "rules": [x["rule_id"] for x in r.get("refinement_applied_rules", []) if x.get("category") == "fp_reduction"],
                     "ml_pred": r.get("prediction")})

print(f"FPs: {len(fps)}, FNs: {len(fns)}")
print()

# FPs by category
print("=== FPs by category ===")
for cat, n in Counter(fp["cat"] for fp in fps).most_common():
    print(f"  {n:3d}x  {cat}")

print()
print("=== FNs by category ===")
for cat, n in Counter(fn["cat"] for fn in fns).most_common():
    print(f"  {n:3d}x  {cat}")

print()
print("=== FP samples (still flagged as scam) ===")
for fp in fps[:10]:
    print(f"  [{fp['cat']}] conf={fp['conf']:.2f} score={fp['score']} rules={fp['rules']}")
    print(f"    {fp['text'][:100]}")
    print()

print("=== FN samples (legit-looking scams flipped to safe) ===")
for fn in fns[:20]:
    print(f"  [{fn['cat']}] ml_pred={fn['ml_pred']} conf={fn['conf']:.2f} score={fn['score']} refined={fn['refined_score']} rules={fn['rules']}")
    print(f"    {fn['text'][:100]}")
    print()
