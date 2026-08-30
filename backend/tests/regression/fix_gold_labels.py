"""Fix mislabeled LEGITIMATE_* entries in gold dataset."""
import csv

GOLD_PATH = r"D:\Developer\Desktop\ScamShield\datasets\gold\gold_dataset.csv"

rows = []
fixed = 0
with open(GOLD_PATH, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for r in reader:
        cat = r.get("category", "")
        scam = r.get("is_scam", "").strip().lower()
        if cat.startswith("LEGITIMATE_") and scam == "true":
            r["is_scam"] = "False"
            r["risk_level"] = "LOW"
            r["ground_truth_label"] = "safe"
            fixed += 1
        rows.append(r)

with open(GOLD_PATH, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Fixed {fixed} mislabeled entries")
