"""Test FN rules directly with proper analysis dict."""
import sys, os
sys.path.insert(0, r"D:\Developer\Desktop\ScamShield\backend")
os.chdir(r"D:\Developer\Desktop\ScamShield\backend")

from domains.reasoning.refinement import (
    _fn_investment_scam, _fn_obfuscated_url, _fn_urgency_with_payment,
    _fn_credential_harvesting, _fn_social_engineering, _fn_fake_support,
    _fn_qr_payment_scam, _fn_obfuscated_contact,
)
from core.constants import ML_LABEL_SAFE

test_msgs = [
    "Stock market tip: Midcap gem identified. 300% returns in 6 months. Join paid group Rs 12,999.",
    "IPO allotment guaranteed for HNI category. Invest Rs 50,000 for 10x returns. Limited seats.",
    "Enforcement Directorate: Money laundering case PMLA 2026. Your assets will be attached. Digital custody ordered.",
    "Hey baby, I am Maria from Spain. I saw your profile and fell in love. I want to come to India but my father needs Rs 50,000 for visa.",
    "Call center jobs in Mumbai: Voice process. Salary Rs 35,000 + incentives. Training bond Rs 25,000.",
    "HYIP: High yield investment program. 5% daily returns for 30 days. Minimum deposit Rs 5,000.",
]

for msg in test_msgs:
    analysis = {
        "prediction": ML_LABEL_SAFE,
        "confidence": 0.65,
        "_original_text": msg,
        "detected_indicators": [],
        "entities": [],
        "rule_score": 0,
    }
    
    fn_funcs = [
        ("FN-001 obf_url", _fn_obfuscated_url),
        ("FN-003 urgency_payment", _fn_urgency_with_payment),
        ("FN-004 credential", _fn_credential_harvesting),
        ("FN-005 social_eng", _fn_social_engineering),
        ("FN-006 fake_support", _fn_fake_support),
        ("FN-007 qr_payment", _fn_qr_payment_scam),
        ("FN-008 investment", _fn_investment_scam),
        ("FN-009 obf_contact", _fn_obfuscated_contact),
    ]
    
    print(f"Text: {msg[:80]}")
    fired = []
    for name, func in fn_funcs:
        try:
            if func(analysis):
                fired.append(name)
        except Exception as e:
            print(f"  {name}: ERROR {e}")
    if fired:
        print(f"  FIRES: {fired}")
    else:
        print(f"  NO FN RULES FIRE")
    print()
