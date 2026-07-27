import re
import urllib.parse
from typing import List, Tuple, Dict

from core.constants import SCAM_KEYWORDS, KNOWN_SHORTENERS as _KNOWN_SHORTENERS, SUSPICIOUS_TLDS as _SUSPICIOUS_TLDS

SUSPICIOUS_TLD = set(_SUSPICIOUS_TLDS)
KNOWN_SHORTENERS = set(_KNOWN_SHORTENERS)


def check_otp(text: str) -> Tuple[int, List[str]]:
    t = text.lower()
    otp_patterns = [
        r"\botp\b", r"one[\s-]*time[\s-]*password", r"verification code",
        r"(?:otp|code)\s*[:\-]\s*\d{4,8}",
    ]
    score = 0
    reasons: List[str] = []
    for p in otp_patterns:
        if re.search(p, t):
            has_sharing_ref = (
                re.search(r"\bshare\b", t) and not re.search(r"\bdo\s+not\s+share\b", t)
            ) or (
                re.search(r"\bsend\b", t) and not re.search(r"\bdo\s+not\s+send\b", t)
            )
            if has_sharing_ref or "forward" in t or "whatsapp" in t:
                score += 20
                reasons.append("Message asks you to share OTP with someone")
            else:
                score += 5
                reasons.append("Contains OTP-sensitive keywords")
            break
    return score, reasons


def check_urgent_money(text: str) -> Tuple[int, List[str]]:
    t = text.lower()
    score = 0
    reasons: List[str] = []

    urgency_words = ["urgent", "immediately", "asap", "right away", "now", "hurry", "limited time", "expires", "expiring", "today only", "final notice", "last warning"]
    for w in urgency_words:
        if re.search(r"\b" + re.escape(w) + r"\b", t):
            score += 5
            reasons.append(f"Urgency keyword: '{w}'")
            break

    money_phrases = [
        (r"(?:rs|inr|₹)\s*[\d,]+", "Mentions a monetary amount"),
        (r"pay(?:\s*now|\s*immediately|\s*the)", "Payment demand detected"),
        (r"transfer\s*(?:money|funds|amount)", "Money transfer request"),
        (r"(?:fee|fine|penalty|payment)\s*(?:of\s*)?(?:rs|inr|₹)?\s*[\d,]+", "Specific monetary demand"),
        (r"credit\s*(?:card|score|limit)", "Credit-related mention"),
        (r"(?:loan|emi)", "Loan or EMI mentioned"),
    ]
    for pat, reason in money_phrases:
        if re.search(pat, t):
            score += 8
            reasons.append(reason)
            break

    if re.search(r"(?:block|suspend|freeze|deactiv|disconnect|cancel)\s*(?:ed|ing)?\s*(?:within|in|after)", t):
        score += 15
        reasons.append("Threat of account suspension/disconnection")

    return score, reasons


def check_suspicious_links(text: str) -> Tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []

    urls = re.findall(r"https?://(?:[-\w.]|%[\da-fA-F]{2})+[^\s]*", text)

    for url in urls:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()

        if any(s in domain for s in KNOWN_SHORTENERS):
            score += 15
            reasons.append(f"Use of URL shortener: {domain}")
            continue

        for tld in SUSPICIOUS_TLD:
            if domain.endswith(tld):
                score += 15
                reasons.append(f"Suspicious TLD in URL: {tld}")
                break
        else:
            suspicious_keywords_in_url = {"kyc", "update", "verify", "secure", "login", "account", "bank", "upi", "aadhaar", "aadhar", "otp", "confirm", "reset"}
            if any(kw in domain for kw in suspicious_keywords_in_url):
                score += 10
                reasons.append(f"URL contains suspicious keywords: {domain}")
                continue
            known_legit_domains = {"flipkart.com", "amazon.in", "amazon.com", "flipkart.co.in",
                                   "paytm.com", "phonepe.com", "whatsapp.com",
                                   "google.com", "facebook.com", "youtube.com",
                                   "instagram.com", "twitter.com", "linkedin.com",
                                   "outlook.com", "hotmail.com", "gmail.com",
                                   "yahoo.com", "reddit.com", "netflix.com", "amazon.co.in"}
            if domain not in known_legit_domains:
                score += 5
                reasons.append("Contains a URL link")

    if len(urls) > 1:
        score += 5
        reasons.append("Multiple URLs in message")

    return score, reasons


def check_service_keywords(text: str) -> Tuple[int, List[str]]:
    t = text.lower()
    score = 0
    reasons: List[str] = []

    india_banks = ["sbi", "hdfc", "icici", "axis", "kotak", "pnb", "canara", "bob", "indusind", "rbi", "sebi"]
    for bank in india_banks:
        if re.search(r"\b" + re.escape(bank) + r"\b", t):
            score += 3
            reasons.append(f"Bank/financial institution mentioned: '{bank}'")
            break
    if re.search(r"\byes\s+bank\b", t) or re.search(r"\bunion\s+bank\b", t):
        score += 3
        reasons.append("Bank/financial institution mentioned")

    payment_apps = ["gpay", "phonepe", "paytm", "bhim", "upi", "amazon pay"]
    for app in payment_apps:
        if re.search(r"\b" + re.escape(app) + r"\b", t):
            score += 3
            reasons.append(f"Payment app mentioned: '{app}'")
            break

    matched: List[str] = []
    for kw, pts in SCAM_KEYWORDS.items():
        pattern = r"\b" + re.escape(kw) + r"\b" if " " not in kw else re.escape(kw)
        if re.search(pattern, t):
            score += pts * 0.5
            matched.append(kw)
    if matched:
        reasons.append(f"Suspicious keywords: {', '.join(matched[:3])}")

    govt_refs = ["pm", "modi", "sarkari", "government of india", "central govt", "nrega", "ayushman"]
    for ref in govt_refs:
        if re.search(r"\b" + re.escape(ref) + r"\b", t):
            score += 5
            reasons.append(f"Government scheme reference: '{ref}'")
            break

    return score, reasons


def analyze_message(text: str) -> Dict[str, object]:
    score = 0
    all_reasons: List[str] = []

    for check_fn in [check_otp, check_urgent_money, check_suspicious_links, check_service_keywords]:
        s, reasons = check_fn(text)
        score += s
        all_reasons.extend(reasons)

    score = min(score, 100)

    if score >= 70:
        risk = "high"
    elif score >= 35:
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
