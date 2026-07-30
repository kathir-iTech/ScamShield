import csv, collections, json, sys
from pathlib import Path

path = Path(r"D:\Developer\Desktop\ScamShield\datasets\v2\annotated\dataset_v2_alpha.csv")
with open(path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"=== RAW DATASET ===")
print(f"Total rows: {len(rows)}")
print(f"Columns: {list(rows[0].keys())}")

seen = {}
dups = 0
dup_ids = []
for r in rows:
    t = r.get("text_clean", r.get("text", "")).strip().lower()
    if t in seen:
        dups += 1
        dup_ids.append((r["id"], seen[t]))
    seen[t] = r["id"]

print(f"Duplicate texts: {dups}")
for d in dup_ids[:5]:
    print(f"  {d[0]} duplicates {d[1]}")

texts = [r.get("text_clean", r.get("text", "")).strip().lower() for r in rows]
print(f"Unique texts: {len(set(texts))}")
print(f"Empty texts: {sum(1 for t in texts if not t)}")

is_scam_vals = collections.Counter(r["is_scam"] for r in rows)
gt_vals = collections.Counter(r["ground_truth_label"] for r in rows)
print(f"is_scam values: {dict(is_scam_vals)}")
print(f"ground_truth_label values: {dict(gt_vals)}")

inconsistent = 0
for r in rows:
    is_scam = r["is_scam"].strip().lower() in ("true", "1", "yes")
    gt = r["ground_truth_label"].strip().lower()
    if (is_scam and gt != "scam") or (not is_scam and gt != "legitimate"):
        inconsistent += 1
        if inconsistent <= 3:
            print(f'  INCONSISTENT: id={r["id"]} is_scam={r["is_scam"]} gt={r["ground_truth_label"]}')
print(f"Label inconsistencies: {inconsistent}")

cats = collections.Counter(r["category"] for r in rows)
print(f"Categories: {len(cats)}")
for c, n in sorted(cats.items(), key=lambda x: -x[1]):
    scam_in_cat = sum(1 for r in rows if r["category"] == c and r["is_scam"].strip().lower() in ("true", "1", "yes"))
    print(f"  {c}: {n} (scam: {scam_in_cat})")

langs = collections.Counter(r.get("language", "unknown") for r in rows)
print(f"Languages: {dict(langs)}")

risks = collections.Counter(r.get("risk_level", "NONE") for r in rows)
print(f"Risk levels: {dict(risks)}")

sources = collections.Counter(r.get("source", "unknown") for r in rows)
print(f"Sources: {dict(sources)}")

missing = {}
for r in rows:
    for k, v in r.items():
        if not v or v == "nan":
            missing[k] = missing.get(k, 0) + 1
missing = {k: v for k, v in missing.items() if v > 0}
print(f"Missing values: {missing}")
