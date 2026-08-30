"""Debug why FN rules don't fire for investment scam messages."""
import sys, os, json

sys.path.insert(0, r"D:\Developer\Desktop\ScamShield\backend")
os.chdir(r"D:\Developer\Desktop\ScamShield\backend")

from domains.reasoning.refinement import (
    _fn_investment_scam, _fn_obfuscated_url, _fn_unicode_spoofing,
    _fn_urgency_with_payment, _fn_credential_harvesting,
    _fn_social_engineering, _fn_fake_support, _fn_qr_payment_scam,
    _fn_obfuscated_contact, _text_lower
)
from services.orchestrator import analyze_text

test_msgs = [
    "Stock market tip: Midcap gem identified. 300% returns in 6 months. Join paid group Rs 12,999. Call 1800-258-3690.",
    "IPO allotment guaranteed for HNI category. Invest Rs 50,000 for 10x returns. Limited seats.",
    "Enforcement Directorate: Money laundering case PMLA 2026. Your assets will be attached. Digital custody ordered.",
    "Hey baby, I am Maria from Spain. I saw your profile and fell in love. I want to come to India but my father needs Rs 50,000 for visa.",
    "Call center jobs in Mumbai: Voice process. Salary Rs 35,000 + incentives. Training bond Rs 25,000.",
]

for msg in test_msgs:
    r = analyze_text(msg)
    print(f"Text: {msg[:80]}")
    print(f"  prediction={r.get('prediction')} confidence={r.get('confidence',0):.2f}")
    print(f"  _original_text in analysis: {'_original_text' in str(r.keys())}")
    
    # Check if _original_text is in the analysis dict passed to refinement
    analysis = {
        "prediction": r.get("prediction"),
        "confidence": r.get("confidence"),
        "_original_text": msg,
        "detected_indicators": r.get("detected_indicators", []),
        "entities": r.get("entities", []),
        "rule_score": r.get("rule_score", 0),
    }
    
    fn_funcs = [
        ("FN-001 obfuscated_url", _fn_obfuscated_url),
        ("FN-002 unicode_spoofing", _fn_unicode_spoofing),
        ("FN-003 urgency_payment", _fn_urgency_with_payment),
        ("FN-004 credential_harvest", _fn_credential_harvesting),
        ("FN-005 social_engineering", _fn_social_engineering),
        ("FN-006 fake_support", _fn_fake_support),
        ("FN-007 qr_payment", _fn_qr_payment_scam),
        ("FN-008 investment_scam", _fn_investment_scam),
        ("FN-009 obfuscated_contact", _fn_obfuscated_contact),
    ]
    for name, func in fn_funcs:
        try:
            result = func(analysis)
            if result:
                print(f"  {name}: FIRES")
        except Exception as e:
            print(f"  {name}: ERROR {e}")
    print()
