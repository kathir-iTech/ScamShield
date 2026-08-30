import csv
with open(r"D:\Developer\Desktop\ScamShield\datasets\gold\gold_dataset.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        cat = r.get("category", "")
        lang = r.get("language", "")
        rid = r["id"]
        scam = r["is_scam"].strip().lower()
        if cat == "LEGITIMATE_BANKING" and lang == "en" and scam == "false":
            print(f"EN: {rid}: {r['text'][:80]}")
            break
    f.seek(0)
    for r in csv.DictReader(f):
        cat = r.get("category", "")
        lang = r.get("language", "")
        scam = r["is_scam"].strip().lower()
        if cat == "LEGITIMATE_UPI" and lang == "en" and scam == "false":
            print(f"EN: {r['id']}: {r['text'][:80]}")
            break
    f.seek(0)
    for r in csv.DictReader(f):
        cat = r.get("category", "")
        lang = r.get("language", "")
        scam = r["is_scam"].strip().lower()
        if cat == "LEGITIMATE_PERSONAL" and lang == "en" and scam == "false":
            print(f"EN: {r['id']}: {r['text'][:80]}")
            break
    f.seek(0)
    for r in csv.DictReader(f):
        cat = r.get("category", "")
        lang = r.get("language", "")
        scam = r["is_scam"].strip().lower()
        if cat == "LEGITIMATE_TELECOM" and lang == "en" and scam == "false":
            print(f"EN: {r['id']}: {r['text'][:80]}")
            break
    f.seek(0)
    for r in csv.DictReader(f):
        cat = r.get("category", "")
        lang = r.get("language", "")
        scam = r["is_scam"].strip().lower()
        if cat == "LEGITIMATE_SHOPPING" and lang == "en" and scam == "false":
            print(f"EN: {r['id']}: {r['text'][:80]}")
            break
