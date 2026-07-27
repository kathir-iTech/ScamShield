import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Disable rate limiting in tests by setting a very high limit
os.environ.setdefault("SCAMSHIELD_RATE_LIMIT_MAX", "1000000")


@pytest.fixture(autouse=True)
def _reset_globals():
    from core.abuse import get_rate_limiter
    get_rate_limiter().reset()
    from core.auth.jwt import _blacklisted_jti, _used_refresh_jti
    _blacklisted_jti.clear()
    _used_refresh_jti.clear()
    yield


@pytest.fixture
def scam_texts():
    return [
        "URGENT: Your SBI account will be deactivated. Update KYC immediately: https://sbi-kyc.xyz",
        "Congratulations! You won 50 Lakh in our mega lottery. Call +91-9876543210 now to claim your prize!",
        "Work from home job - earn 50000/month. Registration fee 500 required.",
        "Your UPI transaction of 15000 is pending. Confirm now to avoid penalty: https://paytm-upi.tk",
        "Double your investment in 30 days! Guaranteed returns.",
        "Your courier parcel from Dubai is held at customs. Pay 5000 release fee to clear it.",
        "PM Modi's new subsidy scheme: Get 50000 in your account.",
        "TNEB: Your electricity bill is overdue. Disconnection in 24 hours.",
        "Customs seized your parcel. Pay 25000 clearance fee.",
        "Personal loan approved! 10 Lakh at 2% interest. Pay 2000 processing fee.",
        "Your Amazon account compromised! Call our customer care at 1800-123-4567.",
        "Scan the QR code below to receive 5000 cashback from PhonePe.",
        "Bitcoin investment! Turn 10000 into 1 Lakh in one week.",
        "Your Aadhaar-linked account will be frozen. Update now: https://aadhaar-verify.cf",
        "ICICI Bank Alert: Your debit card blocked. Call 1800-XXX-XXXX.",
    ]


@pytest.fixture
def safe_texts():
    return [
        "Go until jurong point, crazy.. Available only in bugis n great world la e buffet",
        "Ok lar... Joking wif u oni...",
        "I'm gonna be home soon and i don't want to talk about this stuff anymore tonight, k?",
        "I've been searching for the right words to thank you for this breather.",
        "Fine if that the way u feel. That the way its gota b",
        "Sorry, I'll call later in meeting.",
        "Thanks a lot for your wishes on my birthday.",
        "Hello! How's you and how did saturday go?",
        "Good morning. Hope you have a nice day.",
        "Your meeting with HR is scheduled for 3 PM tomorrow.",
        "The project deadline has been extended to next Friday.",
        "Your OTP for login is 482916. Valid for 5 minutes. Do NOT share.",
        "Flight 6E-123 to Mumbai is boarding at Gate 12.",
        "Your Blinkit order #ORD789 has been delivered.",
        "Thanks for subscribing to our newsletter.",
    ]


@pytest.fixture
def sample_analysis():
    return {
        "prediction": "safe", "confidence": 0.1,
        "rule_score": 0, "rule_label": "low", "reasons": [],
        "detected_indicators": [], "scam_category": "Unknown Scam",
        "entities": [], "entity_summary": {"total_entities": 0, "by_type": {}, "threat_indicators": []},
        "entity_risk": {"high": [], "medium": [], "low": []},
        "decision_score": 0, "decision_level": "SAFE",
        "decision_reasoning": "",
        "supporting_evidence": [], "conflicting_evidence": [],
        "confidence_breakdown": {"ml": 0, "rules": 0, "entities": 0, "explanation": 0, "overall": 0},
        "risk_breakdown": {"credential_theft": 0, "financial_loss": 0, "identity_theft": 0, "malware": 0, "social_engineering": 0},
        "recommended_priority": "LOW", "recommended_action": "Ignore",
        "assessment_score": 0, "assessment_band": "Suitable for normal communication",
        "assessment_confidence": "LOW", "assessment_summary": "",
        "business_reason": "", "technical_reason": "",
        "review_required": False, "manual_review_reason": "",
        "investigation_report": {},
    }
