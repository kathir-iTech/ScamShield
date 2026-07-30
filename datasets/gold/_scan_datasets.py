import csv, re, json, os
from collections import Counter

datasets = {
    "v1": "D:/Developer/Desktop/ScamShield/backend/data/scam_dataset.csv",
    "v2_alpha": "D:/Developer/Desktop/ScamShield/datasets/v2/annotated/dataset_v2_alpha.csv",
    "v2_beta": "D:/Developer/Desktop/ScamShield/datasets/v2/annotated/dataset_v2_beta.csv",
    "v2_gamma": "D:/Developer/Desktop/ScamShield/datasets/v2/annotated/dataset_v2_gamma.csv",
}

all_texts = {}
all_clean = {}
cat_counts = Counter()

for label, path in datasets.items():
    if not os.path.exists(path):
        print(f"WARN: {path} not found")
        continue
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"{label}: {len(rows)} rows")
    texts = set()
    cleans = set()
    for r in rows:
        t = r.get("text", "").strip()
        tc = r.get("text_clean", "") or t.strip().lower()
        texts.add(t)
        cleans.add(tc)
        cat_counts[r.get("category", r.get("label", "UNKNOWN"))] += 1
    all_texts[label] = texts
    all_clean[label] = cleans

all_texts_union = set()
for s in all_texts.values():
    all_texts_union |= s
all_clean_union = set()
for s in all_clean.values():
    all_clean_union |= s

print(f"\nTotal unique texts: {len(all_texts_union)}")
print(f"Total unique cleaned: {len(all_clean_union)}")

for l1 in ["v1", "v2_alpha", "v2_beta", "v2_gamma"]:
    for l2 in ["v1", "v2_alpha", "v2_beta", "v2_gamma"]:
        if l1 < l2 and l1 in all_texts and l2 in all_texts:
            overlap = all_texts[l1] & all_texts[l2]
            if overlap:
                print(f"  Overlap {l1} & {l2}: {len(overlap)} exact")
            o2 = all_clean[l1] & all_clean[l2]
            if o2:
                print(f"  Overlap (clean) {l1} & {l2}: {len(o2)} cleaned")

print(f"\nCategories across all datasets:")
for c, n in sorted(cat_counts.items()):
    print(f"  {c}: {n}")
