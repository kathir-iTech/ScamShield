import json
import sys
from collections import Counter
from schema import validate_dataset

path = sys.argv[1] if len(sys.argv) > 1 else "datasets/benchmark.json"

with open(path, "r", encoding="utf-8") as f:
    samples = json.load(f)

valid, errors, per_sample = validate_dataset(samples)

print(f"Samples: {len(samples)}")
print(f"Valid: {valid}")

ids = [s["id"] for s in samples]
dupes = {i for i in ids if ids.count(i) > 1}
print(f"Duplicate IDs: {dupes if dupes else 'None'}")

preds = Counter(s["expected_prediction"] for s in samples)
cats = Counter(s["expected_category"] for s in samples)
langs = Counter(s["language"] for s in samples)
diffs = Counter(s["difficulty"] for s in samples)

print(f"\nPredictions: scam={preds.get('scam', 0)}, safe={preds.get('safe', 0)}")
print(f"Categories ({len(cats)}):")
for cat, count in sorted(cats.items()):
    print(f"  {cat}: {count}")
print(f"Languages: {dict(langs)}")
print(f"Difficulties: {dict(diffs)}")

if errors:
    print(f"\nErrors ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("\nAll validation checks passed.")
