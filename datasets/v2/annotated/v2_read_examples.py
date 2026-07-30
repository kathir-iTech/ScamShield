import csv
from collections import defaultdict

path = r"D:\Developer\Desktop\ScamShield\datasets\v2\annotated\dataset_v2_alpha.csv"
priority = ["PAN_SCAM","INCOME_TAX_SCAM","DIGITAL_ARREST","ROMANCE_SCAM","CRYPTO_SCAM",
            "LEGITIMATE_UPI","LEGITIMATE_OTP","LEGITIMATE_COURIER",
            "LEGITIMATE_BANKING","LEGITIMATE_GOVERNMENT","QR_SCAM","TELECOM_SCAM",
            "AADHAAR_SCAM","INVESTMENT_SCAM","FAKE_CUSTOMER_CARE"]

samples = defaultdict(list)
with open(path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cat = row["category"]
        if cat in priority:
            samples[cat].append(row)

for cat in priority:
    rows = samples.get(cat, [])
    print(f"\n===== {cat} ({len(rows)} samples) =====")
    for r in rows[:5]:
        print(f'  [{r["id"]}] risk={r["risk_level"]} lang={r["language"]} src={r["source"]}')
        print(f'  TXT: {r["text"][:150]}')
        print(f'  CLN: {r["text_clean"][:150]}')
        print()
