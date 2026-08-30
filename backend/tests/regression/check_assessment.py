"""Check assessment scores for first 5 FPs."""
import csv, sys, os
from pathlib import Path

sys.path.insert(0, r"D:\Developer\Desktop\ScamShield\backend")
os.chdir(r"D:\Developer\Desktop\ScamShield\backend")
from services.orchestrator import analyze_text

texts, labels = [], []
with open(r"D:\Developer\Desktop\ScamShield\datasets\gold\gold_dataset.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        texts.append(r["text"])
        labels.append(1 if r["is_scam"].strip().lower() == "true" else 0)

count = 0
for i, (t, l) in enumerate(zip(texts, labels)):
    if l != 0:
        continue
    r = analyze_text(t)
    if r.get("prediction") != "scam":
        continue
    print(f"text: {t[:100]}")
    print(f"  assessment_score={r.get('assessment_score', '?')} band={r.get('assessment_band', '?')}")
    print(f"  refined_pred={r.get('refined_prediction', '?')} refined_score={r.get('refined_assessment_score', '?')}")
    print(f"  ml_pred={r.get('prediction')} conf={r.get('confidence', 0):.2f}")
    print(f"  rule_score={r.get('rule_score', 0)} rule_label={r.get('rule_label')}")
    print(f"  indicators={r.get('detected_indicators', [])}")
    print(f"  reasons={r.get('reasons', [])}")
    print()
    count += 1
    if count >= 5:
        break
