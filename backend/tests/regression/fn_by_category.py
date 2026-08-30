"""Show scam messages where ML predicts safe (FN categories)."""
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

# Find FNs grouped by category
fn_by_cat = defaultdict(list)
for i, (t, l, c) in enumerate(zip(texts, labels, cats)):
    if l != 1:
        continue
    r = analyze_text(t)
    if r.get("prediction") == "safe":
        fn_by_cat[c].append(t)

for cat in sorted(fn_by_cat.keys()):
    msgs = fn_by_cat[cat]
    print(f"=== {cat} ({len(msgs)} FNs) ===")
    for m in msgs[:5]:
        print(f"  {m[:120]}")
    if len(msgs) > 5:
        print(f"  ... and {len(msgs)-5} more")
    print()
