"""Check which FN rules fire for each scam category."""
import csv, sys, os
from collections import defaultdict

sys.path.insert(0, r"D:\Developer\Desktop\ScamShield\backend")
os.chdir(r"D:\Developer\Desktop\ScamShield\backend")
from services.orchestrator import analyze_text

texts, labels, cats = [], [], []
with open(r"D:\Developer\Desktop\ScamShield\datasets\gold\gold_dataset.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        texts.append(r["text"])
        labels.append(1 if r["is_scam"].strip().lower() == "true" else 0)
        cats.append(r.get("category", ""))

fn_by_cat = defaultdict(list)
for i, (t, l, c) in enumerate(zip(texts, labels, cats)):
    if l != 1:
        continue
    r = analyze_text(t)
    refined = r.get("refined_prediction", r.get("prediction", "safe"))
    if refined == "safe":
        fp_rules = [x["rule_id"] for x in r.get("refinement_applied_rules", []) if x.get("category") == "fp_reduction"]
        fn_rules = [x["rule_id"] for x in r.get("refinement_applied_rules", []) if x.get("category") == "fn_reduction"]
        fn_by_cat[c].append({
            "text": t[:80],
            "ml_pred": r.get("prediction"),
            "conf": r.get("confidence", 0),
            "score": r.get("assessment_score", 0),
            "refined": r.get("refined_assessment_score", 0),
            "fp_rules": fp_rules,
            "fn_rules": fn_rules,
        })

for cat in sorted(fn_by_cat.keys()):
    msgs = fn_by_cat[cat]
    print(f"=== {cat} ({len(msgs)} FNs) ===")
    for m in msgs[:3]:
        print(f"  ml={m['ml_pred']} conf={m['conf']:.2f} score={m['score']}->ref={m['refined']} fp={m['fp_rules']} fn={m['fn_rules']}")
        print(f"    {m['text']}")
    if len(msgs) > 3:
        print(f"  ... and {len(msgs)-3} more")
    print()
