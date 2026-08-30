import re
import urllib.parse
from typing import Dict, List, Tuple

from core.constants import SCAM_KEYWORDS, KNOWN_SHORTENERS as _KNOWN_SHORTENERS, SUSPICIOUS_TLDS as _SUSPICIOUS_TLDS

SUSPICIOUS_TLD = set(_SUSPICIOUS_TLDS)
KNOWN_SHORTENERS = set(_KNOWN_SHORTENERS)

RULE_WEIGHTS: Dict[str, float] = {
    "otp_request": 5.0,
    "otp_share_request": 20.0,
    "urgency_word": 5.0,
    "money_mention": 8.0,
    "suspension_threat": 15.0,
    "url_shortener": 15.0,
    "suspicious_tld": 15.0,
    "url_suspicious_keywords": 10.0,
    "url_present": 5.0,
    "multiple_urls": 5.0,
    "bank_mention": 3.0,
    "payment_app_mention": 3.0,
    "scam_keyword": 2.0,
    "govt_reference": 5.0,
}

THRESHOLDS: Dict[str, float] = {
    "high": 70.0,
    "medium": 35.0,
    "low": 0.0,
}


def _has_scam_context(t: str) -> bool:
    """Check if text has scam-like urgency/threats/requests beyond isolated keyword mentions."""
    urgency = ["urgent", "immediately", "asap", "right away", "hurry", "limited time",
               "expires", "expiring", "final notice", "last warning"]
    threats = ["block", "suspend", "freeze", "deactivate", "disconnect", "cancel",
               "legal", "police", "arrest", "case filed"]
    requests = ["click here", "call now", "reply", "confirm", "verify",
                "share", "send", "forward", "whatsapp"]
    for w in urgency:
        if re.search(r"\b" + re.escape(w) + r"\b", t):
            return True
    for w in threats:
        if re.search(r"\b" + re.escape(w) + r"\b", t):
            return True
    for w in requests:
        if re.search(r"\b" + re.escape(w) + r"\b", t):
            return True
    return False


def check_otp(text: str, weights: Dict[str, float] = RULE_WEIGHTS) -> Tuple[float, List[str]]:
    t = text.lower()
    score = 0.0
    reasons: List[str] = []

    otp_patterns = [
        r"\botp\b", r"one[\s-]*time[\s-]*password", r"verification code",
        r"(?:otp|code)\s*[:\-]\s*\d{4,8}",
    ]
    for p in otp_patterns:
        if re.search(p, t):
            sharing_ref = (
                re.search(r"\bshare\b", t) and not re.search(r"\bdo\s+not\s+share\b", t)
            ) or (
                re.search(r"\bsend\b", t) and not re.search(r"\bdo\s+not\s+send\b", t)
            )
            if sharing_ref or "forward" in t or "whatsapp" in t:
                score += weights["otp_share_request"]
                reasons.append("Message asks you to share OTP with someone")
            elif _has_scam_context(t):
                score += weights["otp_request"]
                reasons.append("Contains OTP-sensitive keywords with suspicious context")
            # Benign OTP mentions (e.g. "Your OTP is 123456") get no score
            break

    return score, reasons


def check_urgent_money(text: str, weights: Dict[str, float] = RULE_WEIGHTS) -> Tuple[float, List[str]]:
    t = text.lower()
    score = 0.0
    reasons: List[str] = []

    urgency_words = ["urgent", "immediately", "asap", "right away", "now", "hurry",
                     "limited time", "expires", "expiring", "today only",
                     "final notice", "last warning"]
    for w in urgency_words:
        if re.search(r"\b" + re.escape(w) + r"\b", t):
            score += weights["urgency_word"]
            reasons.append(f"Urgency keyword: '{w}'")
            break

    money_phrases_demand = [
        (r"pay(?:\s*now|\s*immediately|\s*the)", "Payment demand detected"),
        (r"transfer\s*(?:money|funds|amount)", "Money transfer request"),
        (r"(?:fee|fine|penalty|payment)\s*(?:of\s*)?(?:rs|inr|₹)?\s*[\d,]+", "Specific monetary demand"),
    ]
    for pat, reason in money_phrases_demand:
        if re.search(pat, t):
            score += weights["money_mention"]
            reasons.append(reason)
            break

    money_mention_only = [
        (r"(?:rs|inr|₹)\s*[\d,]+", "Mentions a monetary amount"),
        (r"credit\s*(?:card|score|limit)", "Credit-related mention"),
        (r"(?:loan|emi)", "Loan or EMI mentioned"),
    ]
    for pat, reason in money_mention_only:
        if re.search(pat, t):
            if _has_scam_context(t):
                score += weights["money_mention"]
                reasons.append(reason)
            # Informational monetary mentions without scam context get no score
            break

    if re.search(r"(?:block|suspend|freeze|deactiv|disconnect|cancel)\s*(?:ed|ing)?\s*(?:within|in|after)", t):
        score += weights["suspension_threat"]
        reasons.append("Threat of account suspension/disconnection")

    return score, reasons


def check_suspicious_links(text: str, weights: Dict[str, float] = RULE_WEIGHTS) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []

    urls = re.findall(r"https?://(?:[-\w.]|%[\da-fA-F]{2})+[^\s]*", text)

    for url in urls:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()

        if any(s in domain for s in KNOWN_SHORTENERS):
            score += weights["url_shortener"]
            reasons.append(f"Use of URL shortener: {domain}")
            continue

        for tld in SUSPICIOUS_TLD:
            if domain.endswith(tld):
                score += weights["suspicious_tld"]
                reasons.append(f"Suspicious TLD in URL: {tld}")
                break
        else:
            suspicious_keywords_in_url = {"kyc", "update", "verify", "secure", "login",
                                          "account", "bank", "upi", "aadhaar", "aadhar",
                                          "otp", "confirm", "reset"}
            if any(kw in domain for kw in suspicious_keywords_in_url):
                score += weights["url_suspicious_keywords"]
                reasons.append(f"URL contains suspicious keywords: {domain}")
                continue
            known_legit_domains = {
                "flipkart.com", "amazon.in", "amazon.com", "flipkart.co.in",
                "paytm.com", "phonepe.com", "whatsapp.com",
                "google.com", "facebook.com", "youtube.com",
                "instagram.com", "twitter.com", "linkedin.com",
                "outlook.com", "hotmail.com", "gmail.com",
                "yahoo.com", "reddit.com", "netflix.com", "amazon.co.in",
            }
            if domain not in known_legit_domains:
                score += weights["url_present"]
                reasons.append("Contains a URL link")

    if len(urls) > 1:
        score += weights["multiple_urls"]
        reasons.append("Multiple URLs in message")

    return score, reasons


def check_service_keywords(text: str, weights: Dict[str, float] = RULE_WEIGHTS) -> Tuple[float, List[str]]:
    t = text.lower()
    score = 0.0
    reasons: List[str] = []

    india_banks = ["sbi", "hdfc", "icici", "axis", "kotak", "pnb",
                    "canara", "bob", "indusind", "rbi", "sebi"]
    for bank in india_banks:
        if re.search(r"\b" + re.escape(bank) + r"\b", t):
            if _has_scam_context(t):
                score += weights["bank_mention"]
                reasons.append(f"Bank/financial institution mentioned: '{bank}'")
            break
    if re.search(r"\byes\s+bank\b", t) or re.search(r"\bunion\s+bank\b", t):
        if _has_scam_context(t):
            score += weights["bank_mention"]
            reasons.append("Bank/financial institution mentioned")

    payment_apps = ["gpay", "phonepe", "paytm", "bhim", "upi", "amazon pay"]
    for app in payment_apps:
        if re.search(r"\b" + re.escape(app) + r"\b", t):
            if _has_scam_context(t):
                score += weights["payment_app_mention"]
                reasons.append(f"Payment app mentioned: '{app}'")
            break

    matched: List[str] = []
    for kw, pts in SCAM_KEYWORDS.items():
        pattern = r"\b" + re.escape(kw) + r"\b" if " " not in kw else re.escape(kw)
        if re.search(pattern, t):
            if _has_scam_context(t):
                score += pts * weights["scam_keyword"]
                matched.append(kw)
    if matched:
        reasons.append(f"Suspicious keywords: {', '.join(matched[:3])}")

    govt_refs = ["pm", "modi", "sarkari", "government of india", "central govt",
                  "nrega", "ayushman"]
    for ref in govt_refs:
        if re.search(r"\b" + re.escape(ref) + r"\b", t):
            if _has_scam_context(t):
                score += weights["govt_reference"]
                reasons.append(f"Government scheme reference: '{ref}'")
            break

    return score, reasons


def analyze_message(
    text: str,
    weights: Dict[str, float] = RULE_WEIGHTS,
    thresholds: Dict[str, float] = THRESHOLDS,
) -> Dict[str, object]:
    score = 0.0
    all_reasons: List[str] = []

    for check_fn in [check_otp, check_urgent_money, check_suspicious_links, check_service_keywords]:
        s, reasons = check_fn(text, weights)
        score += s
        all_reasons.extend(reasons)

    score = min(score, 100.0)

    if score >= thresholds["high"]:
        risk = "high"
    elif score >= thresholds["medium"]:
        risk = "medium"
    else:
        risk = "low"

    return {
        "risk_score": round(score, 1),
        "risk_label": risk,
        "reasons": all_reasons[:5],
    }


def get_suggested_action(risk_label: str) -> str:
    actions = {
        "high": "This message appears highly suspicious. Do NOT click any links, reply, or share any personal information. Report to the Cyber Crime portal (https://cybercrime.gov.in) or forward to 1930.",
        "medium": "This message has several suspicious indicators. Verify the sender independently before taking any action. Do not share OTPs or banking details.",
        "low": "This message appears safe, but always exercise caution. Never share OTPs, passwords, or PINs with anyone.",
    }
    return actions.get(risk_label, actions["low"])
