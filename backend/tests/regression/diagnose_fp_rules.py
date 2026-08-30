"""Diagnose why FP refinement rules aren't triggering for the 50 gold FPs."""
import csv, json, sys, os, re
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = str(_SCRIPT_DIR.parent.parent)
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)
print(f"BACKEND_DIR={BACKEND_DIR}")

from core.constants import ML_LABEL_SCAM, ML_LABEL_SAFE

# Import the FP condition functions
from domains.reasoning.refinement import (
    _fp_legitimate_banking_notification,
    _fp_government_alert,
    _fp_delivery_notification,
    _fp_legitimate_otp,
    _fp_transaction_receipt,
    _fp_subscription_reminder,
    _fp_low_indicator_high_confidence,
    _fp_security_notification,
    _fp_legitimate_marketing,
    _has_suspicious_url,
    _has_account_threat,
    _has_payment_request,
    _has_urgency,
    _has_otp_request,
    _KNOWN_BANKS,
    _GOVT_ENTITIES,
    _TRACKING_WORDS,
    _TRANSACTION_WORDS,
    _LEGITIMATE_BANK_PHRASES,
)

from services.orchestrator import analyze_text

GOLD_PATH = Path(BACKEND_DIR).parent / "datasets" / "gold" / "gold_dataset.csv"

texts, labels, cats = [], [], []
with open(GOLD_PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        texts.append(r["text"])
        labels.append(1 if r["is_scam"].strip().lower() == "true" else 0)
        cats.append(r["category"])

# Re-run and check each FP
fp_rules_triggered = {}
fp_rules_not_triggered = {}

for i, (text, label, cat) in enumerate(zip(texts, labels, cats)):
    if label != 0:
        continue
    result = analyze_text(text)
    if result.get("prediction") != "scam":
        continue

    # Build analysis dict matching what refinement sees
    analysis = dict(result)
    analysis["_original_text"] = text

    # Check each FP rule
    rules = [
        ("FP-001", "banking_notification", _fp_legitimate_banking_notification),
        ("FP-002", "government_alert", _fp_government_alert),
        ("FP-003", "delivery_notification", _fp_delivery_notification),
        ("FP-004", "legitimate_otp", _fp_legitimate_otp),
        ("FP-005", "transaction_receipt", _fp_transaction_receipt),
        ("FP-006", "subscription_reminder", _fp_subscription_reminder),
        ("FP-007", "low_indicator_high_confidence", _fp_low_indicator_high_confidence),
        ("FP-008", "security_notification", _fp_security_notification),
        ("FP-009", "legitimate_marketing", _fp_legitimate_marketing),
    ]

    triggered_any = False
    for rule_id, name, cond_fn in rules:
        try:
            if cond_fn(analysis):
                triggered_any = True
                fp_rules_triggered.setdefault(rule_id, []).append({
                    "text": text[:100],
                    "category": cat,
                })
        except Exception as e:
            pass

    if not triggered_any:
        # Why didn't any rule trigger? Diagnose.
        text_lower = text.lower()
        has_bank = any(re.search(r"\b" + re.escape(b) + r"\b", text_lower) for b in _KNOWN_BANKS)
        has_govt = any(re.search(r"\b" + re.escape(g) + r"\b", text_lower) for g in _GOVT_ENTITIES)
        has_tracking = any(re.search(r"\b" + re.escape(t) + r"\b", text_lower) for t in _TRACKING_WORDS)
        has_txn = any(re.search(r"\b" + re.escape(t) + r"\b", text_lower) for t in _TRANSACTION_WORDS)
        has_legit_phrase = any(p in text_lower for p in _LEGITIMATE_BANK_PHRASES)
        has_url = _has_suspicious_url(analysis)
        has_acct_threat = _has_account_threat(analysis)
        has_pay_req = _has_payment_request(analysis)
        has_urg = _has_urgency(analysis)
        has_otp_ind = _has_otp_request(analysis)

        fp_rules_not_triggered.setdefault(cat, []).append({
            "text": text[:120],
            "has_bank": has_bank,
            "has_govt": has_govt,
            "has_tracking": has_tracking,
            "has_txn": has_txn,
            "has_legit_phrase": has_legit_phrase,
            "has_url": has_url,
            "has_acct_threat": has_acct_threat,
            "has_pay_req": has_pay_req,
            "has_urgency": has_urg,
            "has_otp_indicator": has_otp_ind,
            "indicators": analysis.get("detected_indicators", []),
            "reasons": analysis.get("reasons", []),
            "confidence": result.get("confidence", 0),
        })

print("=== FP RULES THAT TRIGGERED ===")
for rule_id, items in sorted(fp_rules_triggered.items()):
    print(f"  {rule_id}: {len(items)} FPs")
    for item in items[:2]:
        print(f"    [{item['category']}] {item['text']}")

print(f"\n=== FP RULES THAT DID NOT TRIGGER ({sum(len(v) for v in fp_rules_not_triggered.values())} FPs) ===")
for cat, items in sorted(fp_rules_not_triggered.items()):
    print(f"\n  {cat} ({len(items)} FPs):")
    for item in items[:3]:
        missing = []
        if not item["has_bank"] and not item["has_govt"] and not item["has_tracking"] and not item["has_txn"]:
            missing.append("no entity match (bank/govt/tracking/txn)")
        if item["has_url"]:
            missing.append("has suspicious URL")
        if item["has_acct_threat"]:
            missing.append("has account threat")
        if item["has_pay_req"]:
            missing.append("has payment request")
        print(f"    text: {item['text']}")
        print(f"    missing: {', '.join(missing) if missing else 'conditions not met'}")
        print(f"    indicators={item['indicators']} confidence={item['confidence']:.2f}")
