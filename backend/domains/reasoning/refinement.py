import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.constants import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    ML_LABEL_SAFE,
    ML_LABEL_SCAM,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    UNKNOWN_CATEGORY,
)
from domains.shared.models import RefinementResult, RefinementRule

logger = logging.getLogger(__name__)


_KNOWN_BANKS: Tuple[str, ...] = (
    "sbi", "state bank of india", "hdfc", "icici", "axis", "kotak",
    "pnb", "canara", "bob", "indusind", "yes bank", "idbi",
    "bank of baroda", "union bank", "central bank",
)

_GOVT_ENTITIES: Tuple[str, ...] = (
    "government", "sarkari", "pm", "modi", "nrega", "ayushman",
    "epfo", "itr", "income tax", "nps", "aadhaar", "uidai",
    "voter id", "epic", "upsc", "delhi university",
)

_TRACKING_WORDS: Tuple[str, ...] = (
    "tracking", "track", "shipment", "delivery", "order", "dispatch",
    "shipped", "out for delivery", "pickup", "courier", "transit",
    "awb", "delivered",
)

_TRANSACTION_WORDS: Tuple[str, ...] = (
    "txn", "transaction", "credited", "debited", "received", "paid",
    "refund", "payment of", "trf", "sent to", "paid to",
    "reward points", "balance", "deposit", "withdrawal", "interest",
)

_LEGITIMATE_BANK_PHRASES: Tuple[str, ...] = (
    "your a/c", "your account", "has been credited", "has been debited",
    "transaction", "trf", "ref no", "available balance",
    "reward points", "credit card payment", "interest of",
    "balance as of", "monthly contribution", "cash deposit",
    "credit", "debited", "neft", "imps", "rtgs",
    "thank you for using",
)


def _has_suspicious_url(analysis: Dict[str, Any]) -> bool:
    entities = analysis.get("entities", [])
    known_legit = {"flipkart.com", "amazon.in", "amazon.com", "flipkart.co.in",
                   "paytm.com", "phonepe.com", "gpay.com", "rb.gy", "tinyurl.com",
                   "bit.ly", "tiny.cc", "shorturl.at", "cutt.ly", "bl.ink",
                   "whatsapp.com", "telegram.me", "t.me", "youtube.com",
                   "google.com", "facebook.com", "twitter.com", "instagram.com",
                   "linkedin.com", "outlook.com", "hotmail.com", "gmail.com",
                   "yahoo.com", "reddit.com", "netflix.com", "amazon.co.in",
                   "myntra.com", "nykaa.com", "ajio.com", "meesho.com",
                   "airtel.in", "jio.com", "vi.in", "bsnl.co.in",
                   "eci.gov.in", "upsc.gov.in", "uidai.gov.in",
                   "vit.ac.in", "vit-placement.in",
                   "delhivery.com", "shiprocket.in", "ecom-express.com",
                   "tatapower.com", "ndmc.gov.in", "bsesdelhi.com"}
    for e in entities:
        etype = e.get("type", "")
        if etype not in ("url", "shortened_url", "suspicious_tld"):
            continue
        value = e.get("value", "").lower()
        parsed = None
        try:
            from urllib.parse import urlparse
            parsed = urlparse(value if "://" in value else "http://" + value)
            domain = parsed.netloc.lower()
        except Exception:
            domain = ""
        if domain in known_legit:
            continue
        return True
    indicators = analysis.get("detected_indicators", [])
    for i in indicators:
        if "url" in i.lower() or "shortened" in i.lower() or "suspicious" in i.lower():
            return True
    reasons = analysis.get("reasons", [])
    for r in reasons:
        if "url" in r.lower() and ("shorten" in r.lower() or "suspicious" in r.lower()):
            return True
    return False


def _has_account_threat(analysis: Dict[str, Any]) -> bool:
    indicators = analysis.get("detected_indicators", [])
    return "Account Threat" in indicators


def _has_payment_request(analysis: Dict[str, Any]) -> bool:
    indicators = analysis.get("detected_indicators", [])
    return "Payment Request" in indicators


def _has_urgency(analysis: Dict[str, Any]) -> bool:
    indicators = analysis.get("detected_indicators", [])
    return "Urgency Language" in indicators


def _has_otp_request(analysis: Dict[str, Any]) -> bool:
    indicators = analysis.get("detected_indicators", [])
    return "OTP Request" in indicators


def _text_lower(analysis: Dict[str, Any]) -> str:
    return analysis.get("_original_text", "").lower()


def _any_keyword_in_text(analysis: Dict[str, Any], keywords: Tuple[str, ...]) -> bool:
    t = _text_lower(analysis)
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", t):
            return True
    return False


def _entity_count(analysis: Dict[str, Any]) -> int:
    return len(analysis.get("entities", []))


def _indicator_count(analysis: Dict[str, Any]) -> int:
    return len(analysis.get("detected_indicators", []))


def _fp_legitimate_banking_notification(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    has_bank_ref = any(re.search(r"\b" + re.escape(b) + r"\b", text) for b in _KNOWN_BANKS)
    if not has_bank_ref:
        return False
    has_legit_phrase = any(p in text for p in _LEGITIMATE_BANK_PHRASES)
    if not has_legit_phrase:
        return False
    if _has_suspicious_url(analysis):
        return False
    if _has_account_threat(analysis):
        return False
    return True


def _fp_government_alert(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    has_govt = any(re.search(r"\b" + re.escape(g) + r"\b", text) for g in _GOVT_ENTITIES)
    if not has_govt:
        return False
    if _has_suspicious_url(analysis):
        return False
    if _has_payment_request(analysis):
        return False
    indicator_count = _indicator_count(analysis)
    if indicator_count >= 3:
        return False
    return True


def _fp_delivery_notification(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    has_tracking = any(re.search(r"\b" + re.escape(t) + r"\b", text) for t in _TRACKING_WORDS)
    if not has_tracking:
        return False
    if _has_suspicious_url(analysis):
        return False
    if _has_payment_request(analysis):
        return False
    return True


def _fp_legitimate_otp(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    has_otp_code = bool(re.search(r"\b\d{4,8}\b", text))
    if not has_otp_code:
        return False
    has_otp_keyword = bool(re.search(r"\botp\b", text))
    if not has_otp_keyword:
        return False
    if _has_suspicious_url(analysis):
        return False
    negated = ["do not share", "dont share", "don't share", "never share", "do not disclose", "do not send", "dont send", "don't send"]
    has_negated_sharing = any(n in text for n in negated)
    has_demand_sharing = re.search(r"(?:share|send|forward|whatsapp)\s+(?:this|now|the|your|me|it)", text) or re.search(r"(?:please|now)\s+(?:share|send|forward)", text)
    if has_negated_sharing:
        return True
    if has_demand_sharing:
        return False
    raw_sharing = re.search(r"\bshare\b", text) or re.search(r"\bsend\b", text)
    if raw_sharing:
        return False
    return True


def _fp_transaction_receipt(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    has_transaction_word = any(re.search(r"\b" + re.escape(t) + r"\b", text) for t in _TRANSACTION_WORDS)
    if not has_transaction_word:
        return False
    if _has_suspicious_url(analysis):
        return False
    if _has_account_threat(analysis):
        return False
    if _has_payment_request(analysis):
        return False
    return True


def _fp_low_indicator_high_confidence(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    confidence = analysis.get("confidence", 0.0)
    if confidence < 0.6:
        return False
    indicator_count = _indicator_count(analysis)
    if indicator_count > 1:
        return False
    entity_count = _entity_count(analysis)
    if entity_count > 0:
        return False
    rule_score = analysis.get("rule_score", 0.0)
    if rule_score >= 35:
        return False
    return True


def _fp_security_notification(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    security_phrases = ["password was changed", "password has been changed", "password changed successfully",
                        "security code", "login alert", "new device", "sign-in attempt",
                        "unusual sign", "unusual login", "account recovery"]
    has_security = any(p in text for p in security_phrases)
    if not has_security:
        return False
    if _has_suspicious_url(analysis):
        return False
    if _has_payment_request(analysis):
        return False
    return True


def _fp_legitimate_marketing(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    marketing_phrases = ["free consultation", "financial advisor", "credit card", "pre-selected",
                         "feedback matters", "complete survey", "rate your experience",
                         "have a great day", "thank you for being a valued customer",
                         "terms apply", "reply yes", "opt out", "unsubscribe"]
    has_marketing = any(p in text for p in marketing_phrases)
    if not has_marketing:
        return False
    if _has_suspicious_url(analysis):
        return False
    indicator_count = _indicator_count(analysis)
    if indicator_count >= 3:
        return False
    return True


def _fp_subscription_reminder(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    sub_keywords = ["subscription", "renewal", "renew", "auto-pay", "auto debit", "auto debit", "bill due"]
    has_sub = any(re.search(r"\b" + re.escape(k) + r"\b", text) for k in sub_keywords)
    if not has_sub:
        return False
    if _has_suspicious_url(analysis):
        return False
    if _has_account_threat(analysis):
        return False
    return True


_UPI_APPS: Tuple[str, ...] = (
    "gpay", "google pay", "phonepe", "phone pe", "paytm", "bhim",
    "amazon pay", "mobiwik", "freecharge",
)

_ECOMMERCE_PLATFORMS: Tuple[str, ...] = (
    "amazon", "flipkart", "myntra", "nykaa", "ajio", "meesho",
    "snapdeal", "jabong", "limeroad",
)

_DELIVERY_SERVICES: Tuple[str, ...] = (
    "delhivery", "ecom express", "blue dart", "dt dc", "professional courier",
    "india post", "speed post", "shiprocket", "fedex", "dhl", "aramex",
)

_UTILITY_KEYWORDS: Tuple[str, ...] = (
    "electricity", "water bill", "gas bill", "broadband", "mobile bill",
    "postpaid", "prepaid", "recharge",
)

_TELECOM_ENTITIES: Tuple[str, ...] = (
    "airtel", "jio", "vi", "vodafone", "bsnl", "tata play", "dth",
    "jiofiber", "airtel fiber", "act fiber", "bsnl fiber",
)

_COLLEGE_ENTITIES: Tuple[str, ...] = (
    "vit", "iit", "nit", "bits", "iiit", "nits", "manipal",
    "srm", "amity", "lpu", "christ", "st xaviers",
)


def _fp_upi_transaction(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    has_upi_app = any(re.search(r"\b" + re.escape(a) + r"\b", text) for a in _UPI_APPS)
    has_upi_ref = bool(re.search(r"upi\s*(?:ref|refno|ref no|reference)", text))
    has_transaction = any(re.search(r"\b" + re.escape(t) + r"\b", text) for t in ["sent to", "paid to", "received from", "refund", "successful"])
    if not (has_upi_app or has_upi_ref):
        return False
    if not has_transaction:
        return False
    if _has_suspicious_url(analysis):
        return False
    if _has_account_threat(analysis):
        return False
    if _has_payment_request(analysis):
        return False
    return True


def _fp_shopping_update(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    has_platform = any(re.search(r"\b" + re.escape(p) + r"\b", text) for p in _ECOMMERCE_PLATFORMS)
    if not has_platform:
        return False
    update_keywords = ["order", "shipped", "delivered", "return", "refund", "pickup", "dispatch", "tracking"]
    has_update = any(re.search(r"\b" + re.escape(k) + r"\b", text) for k in update_keywords)
    if not has_update:
        return False
    if _has_suspicious_url(analysis):
        return False
    if _has_account_threat(analysis):
        return False
    if _has_payment_request(analysis):
        return False
    return True


def _fp_utility_bill(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    has_utility = any(re.search(r"\b" + re.escape(k) + r"\b", text) for k in _UTILITY_KEYWORDS)
    if not has_utility:
        return False
    has_amount = bool(re.search(r"rs\.?\s*\d+|inr\s*\d+|₹\s*\d+", text))
    if not has_amount:
        return False
    has_due = any(re.search(r"\b" + re.escape(d) + r"\b", text) for d in ["due date", "due by", "pay before", "pay by", "last date"])
    if not has_due:
        return False
    if _has_suspicious_url(analysis):
        return False
    if _has_account_threat(analysis):
        return False
    return True


def _fp_telecom_notification(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    has_telecom = any(re.search(r"\b" + re.escape(e) + r"\b", text) for e in _TELECOM_ENTITIES)
    if not has_telecom:
        return False
    info_phrases = ["recharge", "plan", "data", "expiry", "expire", "renew",
                    "valid", "activated", "monthly", "speed", "gb", "mbps"]
    has_info = any(p in text for p in info_phrases)
    if not has_info:
        return False
    if _has_suspicious_url(analysis):
        return False
    if _has_payment_request(analysis):
        return False
    if _has_account_threat(analysis):
        return False
    return True


def _fp_college_notification(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SCAM:
        return False
    text = _text_lower(analysis)
    has_college = any(re.search(r"\b" + re.escape(e) + r"\b", text) for e in _COLLEGE_ENTITIES)
    if not has_college:
        return False
    info_phrases = ["placement", "exam", "result", "semester", "attendance",
                    "assignment", "lecture", "lab", "register", "drive", "campus"]
    has_info = any(p in text for p in info_phrases)
    if not has_info:
        return False
    if _has_suspicious_url(analysis):
        return False
    if _has_payment_request(analysis):
        return False
    return True


def _fn_obfuscated_url(analysis: Dict[str, Any]) -> bool:
    text = _text_lower(analysis)
    obfuscated_patterns = [
        r"bit\s*\[?\s*dot\s*\]?\s*ly",
        r"hxxp[s]?://",
        r"h(?!ttp)[tT][tT][pP]",
        r"click\s*(?:here|the\s*link|this)",
        r"\[link\]",
        r"remove\s*(?:the\s*)?dots?",
    ]
    return any(re.search(p, text) for p in obfuscated_patterns)


def _fn_unicode_spoofing(analysis: Dict[str, Any]) -> bool:
    text = analysis.get("_original_text", "")
    if not text:
        return False
    non_ascii_count = sum(1 for c in text if ord(c) > 127)
    if non_ascii_count > 0 and non_ascii_count < len(text) * 0.3:
        has_url_like = bool(re.search(r'https?://', text, re.IGNORECASE))
        if has_url_like:
            return True
        has_dot_com = bool(re.search(r'[\w\u0080-\uffff]+\.[\w\u0080-\uffff]+', text))
        if has_dot_com:
            return True
    return False


def _fn_urgency_with_payment(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SAFE:
        return False
    if not _has_urgency(analysis):
        return False
    if not _has_payment_request(analysis):
        return False
    return True


def _fn_credential_harvesting(analysis: Dict[str, Any]) -> bool:
    text = _text_lower(analysis)
    harvest_phrases = [
        r"share\s*(?:your\s*)?(?:otp|password|pin|aadhaar|bank)",
        r"update\s*(?:your\s*)?(?:aadhaar|pan|bank|account)",
        r"verify\s*(?:your\s*)?(?:identity|account|details|kyc|pan)",
        r"confirm\s*(?:your\s*)?(?:details|account|information)",
        r"(?:login|sign.?in)\s*(?:to\s*)?(?:verify|update|confirm)",
    ]
    return any(re.search(p, text) for p in harvest_phrases)


def _fn_social_engineering(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SAFE:
        return False
    text = _text_lower(analysis)
    has_threat = any(t in text for t in ["block", "suspend", "freeze", "deactivate", "legal", "police", "arrest"])
    has_reward = any(r in text for r in ["won", "prize", "cashback", "reward", "free", "gift", "offer"])
    has_call_to_action = any(c in text for c in ["click", "call", "apply", "register", "submit", "respond"])
    score = sum([has_threat, has_reward, has_call_to_action])
    return score >= 2


def _fn_fake_support(analysis: Dict[str, Any]) -> bool:
    text = _text_lower(analysis)
    support_phrases = ["customer care", "customer support", "helpdesk", "helpline", "toll free", "help line"]
    has_support = any(p in text for p in support_phrases)
    if not has_support:
        return False
    has_phone = bool(re.search(r'\b\d{10,15}\b', text)) or bool(re.search(r'1[8-9]00', text))
    return has_phone


def _fn_qr_payment_scam(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SAFE:
        return False
    indicators = analysis.get("detected_indicators", [])
    has_qr = "QR Code Request" in indicators
    if not has_qr:
        return False
    has_payment = _has_payment_request(analysis)
    return has_payment


def _fn_investment_scam(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SAFE:
        return False
    text = _text_lower(analysis)
    invest_keywords = ["investment", "profit", "returns", "return", "earn", "income", "trading", "crypto", "bitcoin"]
    has_invest = any(re.search(r"\b" + re.escape(k), text) for k in invest_keywords)
    if not has_invest:
        return False
    guarantee_keywords = ["guaranteed", "100%", "assured", "risk free", "double", "limited", "hurry"]
    has_guarantee = any(g in text for g in guarantee_keywords)
    return has_guarantee


def _fn_obfuscated_contact(analysis: Dict[str, Any]) -> bool:
    text = _text_lower(analysis)
    obfuscation = [
        r"\w+\s*\(?\s*@\s*\)?\s*\w+",
        r"\w+\s*\(?\s*\[?\s*\bat\b\s*\]?\s*\)?\s*\w+",
        r"\w+\s*\(?\s*\[?\s*\bdot\b\s*\]?\s*\)?\s*\w+",
    ]
    return any(re.search(p, text) for p in obfuscation)


def _fn_digital_arrest_scam(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SAFE:
        return False
    text = _text_lower(analysis)
    authority_keywords = [
        "enforcement directorate", "supreme court", "high court", "ncb",
        "cbi", "police", "crime branch", "cyber crime",
        "anti corruption", "edar", "ed notice",
    ]
    has_authority = any(k in text for k in authority_keywords)
    if not has_authority:
        return False
    threat_keywords = ["arrest", "custody", "warrant", "case registered",
                       "investigation", "summon", "attached", "frozen",
                       "blackmailed", "legal action"]
    has_threat = any(k in text for k in threat_keywords)
    return has_threat


def _fn_romance_scam(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SAFE:
        return False
    text = _text_lower(analysis)
    affection_phrases = ["fell in love", "i love you", "my love", "dear",
                         "baby", "darling", "sweetheart", "hi dear"]
    has_affection = any(p in text for p in affection_phrases)
    if not has_affection:
        return False
    money_keywords = ["send", "need", "visa", "flight", "fee", "transfer",
                      "money", "rupees", "dollars", "inheritance", "release fee"]
    has_money = any(k in text for k in money_keywords)
    return has_money


def _fn_job_scam(analysis: Dict[str, Any]) -> bool:
    if analysis.get("prediction") != ML_LABEL_SAFE:
        return False
    text = _text_lower(analysis)
    job_phrases = ["job", "salary", "hiring", "vacancy", "position",
                   "work from home", "earn money", "part time"]
    has_job = any(re.search(r"\b" + re.escape(p), text) for p in job_phrases)
    if not has_job:
        return False
    fee_keywords = ["training fee", "training bond", "registration fee",
                    "security deposit", "processing fee", "registration rs"]
    has_fee = any(k in text for k in fee_keywords)
    if not has_fee:
        return False
    high_salary = bool(re.search(r"salary\s+rs[\s.]*\d{2,}", text))
    return has_fee or high_salary


FP_RULES: List[RefinementRule] = [
    RefinementRule(
        rule_id="FP-001",
        description="Legitimate banking notification misclassified as scam",
        category="fp_reduction",
        priority="HIGH",
        confidence_impact=-0.25,
        condition=_fp_legitimate_banking_notification,
        reason="Contains legitimate banking notification patterns (transaction/credit info with bank name, no phishing indicators). Downgrading scam confidence.",
    ),
    RefinementRule(
        rule_id="FP-002",
        description="Government alert misclassified as scam",
        category="fp_reduction",
        priority="HIGH",
        confidence_impact=-0.25,
        condition=_fp_government_alert,
        reason="Contains government scheme references without payment request or suspicious URLs. Likely a legitimate government communication.",
    ),
    RefinementRule(
        rule_id="FP-003",
        description="Delivery notification misclassified as scam",
        category="fp_reduction",
        priority="HIGH",
        confidence_impact=-0.25,
        condition=_fp_delivery_notification,
        reason="Contains delivery tracking language without payment demands or suspicious links. Likely a legitimate delivery notification.",
    ),
    RefinementRule(
        rule_id="FP-004",
        description="Legitimate OTP message misclassified as scam",
        category="fp_reduction",
        priority="MEDIUM",
        confidence_impact=-0.20,
        condition=_fp_legitimate_otp,
        reason="Contains an OTP code but no sharing request or phishing indicators. Likely a legitimate one-time password message.",
    ),
    RefinementRule(
        rule_id="FP-005",
        description="Transaction receipt misclassified as scam",
        category="fp_reduction",
        priority="HIGH",
        confidence_impact=-0.25,
        condition=_fp_transaction_receipt,
        reason="Contains transaction reference without payment demands or suspicious URLs. Likely a legitimate financial receipt.",
    ),
    RefinementRule(
        rule_id="FP-006",
        description="Subscription reminder misclassified as scam",
        category="fp_reduction",
        priority="MEDIUM",
        confidence_impact=-0.20,
        condition=_fp_subscription_reminder,
        reason="Contains subscription or billing reminder without account threats or phishing links. Likely a legitimate reminder.",
    ),
    RefinementRule(
        rule_id="FP-007",
        description="High ML confidence but insufficient evidence",
        category="fp_reduction",
        priority="MEDIUM",
        confidence_impact=-0.15,
        condition=_fp_low_indicator_high_confidence,
        reason="ML model is confident but lacks corroborating indicators or entities. Reducing confidence to prevent over-reliance on single signal.",
    ),
    RefinementRule(
        rule_id="FP-008",
        description="Security notification misclassified as scam",
        category="fp_reduction",
        priority="HIGH",
        confidence_impact=-0.25,
        condition=_fp_security_notification,
        reason="Contains security notification language (password change, login alert) without phishing indicators. Likely a legitimate security alert.",
    ),
    RefinementRule(
        rule_id="FP-009",
        description="Marketing or promotional message misclassified as scam",
        category="fp_reduction",
        priority="MEDIUM",
        confidence_impact=-0.20,
        condition=_fp_legitimate_marketing,
        reason="Contains marketing/promotional language without suspicious URLs or strong scam indicators. Likely a legitimate commercial message.",
    ),
    RefinementRule(
        rule_id="FP-010",
        description="UPI transaction confirmation misclassified as scam",
        category="fp_reduction",
        priority="HIGH",
        confidence_impact=-0.25,
        condition=_fp_upi_transaction,
        reason="Contains UPI transaction confirmation with reference number. Likely a legitimate payment receipt.",
    ),
    RefinementRule(
        rule_id="FP-011",
        description="Shopping/ecommerce update misclassified as scam",
        category="fp_reduction",
        priority="HIGH",
        confidence_impact=-0.25,
        condition=_fp_shopping_update,
        reason="Contains order update or return confirmation from known ecommerce platform. Likely a legitimate order notification.",
    ),
    RefinementRule(
        rule_id="FP-012",
        description="Utility bill notification misclassified as scam",
        category="fp_reduction",
        priority="MEDIUM",
        confidence_impact=-0.20,
        condition=_fp_utility_bill,
        reason="Contains utility bill notification with amount and due date. Likely a legitimate bill reminder.",
    ),
    RefinementRule(
        rule_id="FP-013",
        description="Telecom notification misclassified as scam",
        category="fp_reduction",
        priority="MEDIUM",
        confidence_impact=-0.20,
        condition=_fp_telecom_notification,
        reason="Contains telecom provider name with plan/recharge info. Likely a legitimate telecom notification.",
    ),
    RefinementRule(
        rule_id="FP-014",
        description="College notification misclassified as scam",
        category="fp_reduction",
        priority="MEDIUM",
        confidence_impact=-0.20,
        condition=_fp_college_notification,
        reason="Contains college name with academic info. Likely a legitimate college notification.",
    ),
]

FN_RULES: List[RefinementRule] = [
    RefinementRule(
        rule_id="FN-001",
        description="Obfuscated URL not detected",
        category="fn_reduction",
        priority="HIGH",
        confidence_impact=0.25,
        condition=_fn_obfuscated_url,
        reason="Message contains obfuscated URL patterns indicating attempt to evade detection. Increasing scam confidence.",
    ),
    RefinementRule(
        rule_id="FN-002",
        description="Unicode spoofing in URL or domain",
        category="fn_reduction",
        priority="HIGH",
        confidence_impact=0.20,
        condition=_fn_unicode_spoofing,
        reason="Message uses Unicode characters for domain spoofing, a common phishing technique. Increasing scam confidence.",
    ),
    RefinementRule(
        rule_id="FN-003",
        description="Urgency combined with payment request",
        category="fn_reduction",
        priority="HIGH",
        confidence_impact=0.20,
        condition=_fn_urgency_with_payment,
        reason="Message combines urgency language with direct payment demands, a hallmark of financial scams. Increasing scam confidence.",
    ),
    RefinementRule(
        rule_id="FN-004",
        description="Credential harvesting attempt",
        category="fn_reduction",
        priority="HIGH",
        confidence_impact=0.25,
        condition=_fn_credential_harvesting,
        reason="Message explicitly requests sensitive credentials (OTP, password, Aadhaar, bank details). Strong indicator of credential harvesting. Increasing scam confidence.",
    ),
    RefinementRule(
        rule_id="FN-005",
        description="Social engineering pattern detected",
        category="fn_reduction",
        priority="MEDIUM",
        confidence_impact=0.15,
        condition=_fn_social_engineering,
        reason="Message combines threat, reward, and call-to-action — classic social engineering triad. Increasing scam confidence.",
    ),
    RefinementRule(
        rule_id="FN-006",
        description="Fake customer support detected",
        category="fn_reduction",
        priority="MEDIUM",
        confidence_impact=0.15,
        condition=_fn_fake_support,
        reason="Message impersonates customer support with contact details, a common technique for credential harvesting. Increasing scam confidence.",
    ),
    RefinementRule(
        rule_id="FN-007",
        description="QR code payment scam",
        category="fn_reduction",
        priority="HIGH",
        confidence_impact=0.20,
        condition=_fn_qr_payment_scam,
        reason="Message combines QR code request with payment demand, indicating a QR-based payment scam. Increasing scam confidence.",
    ),
    RefinementRule(
        rule_id="FN-008",
        description="Investment scam with guaranteed returns",
        category="fn_reduction",
        priority="HIGH",
        confidence_impact=0.20,
        condition=_fn_investment_scam,
        reason="Message offers investment with guaranteed returns and urgency, typical of Ponzi schemes. Increasing scam confidence.",
    ),
    RefinementRule(
        rule_id="FN-009",
        description="Obfuscated contact information",
        category="fn_reduction",
        priority="MEDIUM",
        confidence_impact=0.15,
        condition=_fn_obfuscated_contact,
        reason="Message uses obfuscated contact information to avoid detection. Increasing scam confidence.",
    ),
    RefinementRule(
        rule_id="FN-010",
        description="Digital arrest / authority impersonation scam",
        category="fn_reduction",
        priority="HIGH",
        confidence_impact=0.25,
        condition=_fn_digital_arrest_scam,
        reason="Message impersonates law enforcement or judicial authority with arrest/custody threats. Classic digital arrest scam pattern. Increasing scam confidence.",
    ),
    RefinementRule(
        rule_id="FN-011",
        description="Romance / sweetheart scam",
        category="fn_reduction",
        priority="HIGH",
        confidence_impact=0.20,
        condition=_fn_romance_scam,
        reason="Message uses affection language combined with money requests. Classic romance scam pattern. Increasing scam confidence.",
    ),
    RefinementRule(
        rule_id="FN-012",
        description="Job scam with upfront fees",
        category="fn_reduction",
        priority="HIGH",
        confidence_impact=0.20,
        condition=_fn_job_scam,
        reason="Message offers employment but requires upfront fees (training bond, registration). Classic job scam pattern. Increasing scam confidence.",
    ),
]

ALL_RULES: List[RefinementRule] = FP_RULES + FN_RULES


def _score_bands() -> Dict[str, Any]:
    return {
        "very_high": 85,
        "high": 65,
        "medium": 40,
        "low": 20,
    }


def _adjust_assessment_score(
    original_score: int,
    fp_adjustment: int,
    fn_adjustment: int,
) -> int:
    score = original_score + fn_adjustment - fp_adjustment
    return max(0, min(score, 100))


def _map_confidence(assessment_score: int, has_conflict: bool) -> str:
    bands = _score_bands()
    if assessment_score >= bands["very_high"] and not has_conflict:
        return CONFIDENCE_HIGH
    if assessment_score >= bands["high"]:
        return CONFIDENCE_HIGH
    if assessment_score >= bands["medium"]:
        return CONFIDENCE_MEDIUM
    return CONFIDENCE_LOW


def _check_decision_stability(analysis: Dict[str, Any]) -> Tuple[bool, List[str]]:
    concerns: List[str] = []
    assessment_score = analysis.get("assessment_score", 0)
    confidence = analysis.get("confidence", 0.0)
    band_boundaries = [20, 40, 65, 85]
    for boundary in band_boundaries:
        if abs(assessment_score - boundary) <= 3:
            concerns.append(
                f"Assessment score ({assessment_score}) is within 3 points of decision boundary ({boundary}). "
                "Small wording changes could alter classification."
            )
    if 0.45 < confidence < 0.55:
        concerns.append(
            f"ML confidence ({confidence:.2f}) is near the 0.5 decision threshold. "
            "Minor input variations could flip the prediction."
        )
    return len(concerns) == 0, concerns


def check_decision_stability(analysis: Dict[str, Any]) -> Dict[str, Any]:
    stable, concerns = _check_decision_stability(analysis)
    return {
        "stable": stable,
        "concerns": concerns,
    }


def _compute_fp_adjustment(analysis: Dict[str, Any]) -> Tuple[int, List[Dict[str, Any]]]:
    total_impact = 0
    applied: List[Dict[str, Any]] = []
    for rule in FP_RULES:
        try:
            if rule.condition(analysis):
                impact_points = round(abs(rule.confidence_impact) * 100 * 0.70)
                total_impact += impact_points
                applied.append({
                    "rule_id": rule.rule_id,
                    "description": rule.description,
                    "category": rule.category,
                    "priority": rule.priority,
                    "impact": -impact_points,
                    "reason": rule.reason,
                })
        except Exception as e:
            logger.debug("FP rule %s failed: %s", rule.rule_id, e)
    return min(total_impact, 40), applied


def _compute_fn_adjustment(analysis: Dict[str, Any]) -> Tuple[int, List[Dict[str, Any]]]:
    total_impact = 0
    applied: List[Dict[str, Any]] = []
    for rule in FN_RULES:
        try:
            if rule.condition(analysis):
                impact_points = round(abs(rule.confidence_impact) * 100 * 0.70)
                total_impact += impact_points
                applied.append({
                    "rule_id": rule.rule_id,
                    "description": rule.description,
                    "category": rule.category,
                    "priority": rule.priority,
                    "impact": impact_points,
                    "reason": rule.reason,
                })
        except Exception as e:
            logger.debug("FN rule %s failed: %s", rule.rule_id, e)
    return min(total_impact, 40), applied


def _build_summary(applied_fp: List[Dict], applied_fn: List[Dict], stable: bool) -> str:
    parts = []
    if applied_fp:
        ids = [r["rule_id"] for r in applied_fp]
        parts.append(f"FP reduction: {', '.join(ids)}")
    if applied_fn:
        ids = [r["rule_id"] for r in applied_fn]
        parts.append(f"FN reduction: {', '.join(ids)}")
    if not stable:
        parts.append("Decision stability concern flagged")
    if not parts:
        return "No refinement rules triggered. Assessment stands."
    return "Refinement applied: " + "; ".join(parts) + "."
