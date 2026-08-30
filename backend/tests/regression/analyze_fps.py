"""Analyze the gold false positives."""
import json
from collections import Counter

with open(r"D:\Developer\Desktop\ScamShield\backend\tests\regression\gold_false_positives.json") as f:
    fps = json.load(f)

print(f"Total FPs: {len(fps)}")
print()

ml_pred_counts = Counter(fp["ml_prediction"] for fp in fps)
rule_label_counts = Counter(fp["rule_label"] for fp in fps)
risk_counts = Counter(fp["risk_level"] for fp in fps)

print(f"ML predictions: {dict(ml_pred_counts)}")
print(f"Rule labels: {dict(rule_label_counts)}")
print(f"Risk levels: {dict(risk_counts)}")
print()

has_rule = sum(1 for fp in fps if fp["rule_score"] > 0)
no_rule = sum(1 for fp in fps if fp["rule_score"] == 0)
print(f"FPs with rule_score > 0: {has_rule}")
print(f"FPs with rule_score == 0: {no_rule}")
print()

print("=== FPs WITH RULE SCORE > 0 ===")
for fp in fps:
    if fp["rule_score"] > 0:
        print(f"  score={fp['rule_score']:.2f} label={fp['rule_label']} reasons={fp['reasons']} indicators={fp['detected_indicators']}")
        print(f"    text: {fp['text'][:120]}")
        print()

print("=== FPs WITH RULE SCORE == 0 (pure ML) - first 15 ===")
count = 0
for fp in fps:
    if fp["rule_score"] == 0:
        print(f"  ml_pred={fp['ml_prediction']} conf={fp['confidence']:.2f} risk={fp['risk_level']}")
        print(f"    text: {fp['text'][:120]}")
        print()
        count += 1
        if count >= 15:
            break

# Analyze by gold category
cat_counts = Counter(fp["gold_category"] for fp in fps)
print("=== FPs by gold category ===")
for cat, n in cat_counts.most_common():
    print(f"  {n:3d}x  {cat}")

# What does the pipeline actually look at?
print()
print("=== SAMPLE FULL PIPELINE OUTPUT (first 3 FP) ===")
for fp in fps[:3]:
    print(f"  prediction={fp['ml_prediction']} confidence={fp['confidence']:.2f}")
    print(f"  rule_score={fp['rule_score']} rule_label={fp['rule_label']}")
    print(f"  risk_level={fp['risk_level']} scam_category={fp['scam_category']}")
    print(f"  reasons={fp['reasons']}")
    print(f"  indicators={fp['detected_indicators']}")
    print(f"  threats={fp['threats']}")
    print(f"  summary={fp['summary'][:150]}")
    print(f"  text: {fp['text'][:120]}")
    print()
