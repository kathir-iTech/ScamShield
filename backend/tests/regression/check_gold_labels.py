import csv
with open(r"D:\Developer\Desktop\ScamShield\datasets\gold\gold_dataset.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        cat = r.get("category", "")
        if cat in ("LEGITIMATE_PERSONAL", "LEGITIMATE_TELECOM", "LEGITIMATE_UPI"):
            print(f"{cat}: is_scam={r['is_scam']} text={r['text'][:80]}")
