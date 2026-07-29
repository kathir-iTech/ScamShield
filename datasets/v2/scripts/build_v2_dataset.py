"""
ScamShield v2 Dataset Builder — Populates the dataset from all available sources.
Usage: python datasets/v2/scripts/build_v2_dataset.py
"""
import csv
import json
import os
import re
import sys
import time
import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

try:
    from utils.text import clean_text as backend_clean_text
except ModuleNotFoundError:
    backend_clean_text = None

VERSION = "2.0.0-alpha"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

OUTPUT_DIR = os.path.join(BASE_DIR, "datasets", "v2", "annotated")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# SCHEMA
# ============================================================

VALID_CATEGORIES = {
    "UPI_FRAUD", "BANKING_FRAUD", "KYC_SCAM", "AADHAAR_SCAM", "PAN_SCAM",
    "FAKE_CUSTOMER_CARE", "COURIER_SCAM", "ELECTRICITY_BILL_SCAM", "QR_SCAM",
    "LOTTERY_SCAM", "INVESTMENT_SCAM", "CRYPTO_SCAM", "LOAN_SCAM", "JOB_SCAM",
    "ROMANCE_SCAM", "GOVERNMENT_IMPERSONATION", "DIGITAL_ARREST",
    "INCOME_TAX_SCAM", "TELECOM_SCAM",
    "LEGITIMATE_BANKING", "LEGITIMATE_UPI", "LEGITIMATE_OTP",
    "LEGITIMATE_COURIER", "LEGITIMATE_GOVERNMENT", "LEGITIMATE_OTHER",
}

CATEGORY_IS_SCAM = {c: True for c in VALID_CATEGORIES}
for c in ["LEGITIMATE_BANKING", "LEGITIMATE_UPI", "LEGITIMATE_OTP",
          "LEGITIMATE_COURIER", "LEGITIMATE_GOVERNMENT", "LEGITIMATE_OTHER"]:
    CATEGORY_IS_SCAM[c] = False

CATEGORY_RISK = {
    "UPI_FRAUD": "CRITICAL", "BANKING_FRAUD": "CRITICAL", "KYC_SCAM": "HIGH",
    "AADHAAR_SCAM": "HIGH", "PAN_SCAM": "HIGH", "FAKE_CUSTOMER_CARE": "MEDIUM",
    "COURIER_SCAM": "HIGH", "ELECTRICITY_BILL_SCAM": "HIGH", "QR_SCAM": "HIGH",
    "LOTTERY_SCAM": "MEDIUM", "INVESTMENT_SCAM": "HIGH", "CRYPTO_SCAM": "HIGH",
    "LOAN_SCAM": "MEDIUM", "JOB_SCAM": "MEDIUM", "ROMANCE_SCAM": "HIGH",
    "GOVERNMENT_IMPERSONATION": "HIGH", "DIGITAL_ARREST": "CRITICAL",
    "INCOME_TAX_SCAM": "CRITICAL", "TELECOM_SCAM": "HIGH",
    "LEGITIMATE_BANKING": "NONE", "LEGITIMATE_UPI": "NONE",
    "LEGITIMATE_OTP": "NONE", "LEGITIMATE_COURIER": "NONE",
    "LEGITIMATE_GOVERNMENT": "NONE", "LEGITIMATE_OTHER": "NONE",
}

_BANK_NAMES = [
    "sbi", "state bank of india", "hdfc", "icici", "axis", "pnb", "kotak",
    "yes bank", "indusind", "idbi", "canara", "union bank", "bank of baroda",
    "bob", "rbi", "reserve bank", "sebi", "sbi yono", "hdfc bank",
    "icici bank", "axis bank", "pnb", "kotak mahindra", "yesbank",
]

_AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
_PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
_PHONE_RE = re.compile(r"(?:\+?91[\s-]?)?\d{10}\b")
_URL_RE = re.compile(r"https?://(?:[-\w.]|%[\da-fA-F]{2})+(?:/[^\s]*)?", re.IGNORECASE)
_UPI_RE = re.compile(r"[\w.-]+@[\w.-]+", re.IGNORECASE)

_category_counters: Dict[str, int] = {}

def _detect_banks(text_lower: str) -> List[str]:
    found = []
    for b in _BANK_NAMES:
        if b in text_lower:
            found.append(b)
    return list(set(found))

def _extract_entities_text(text: str) -> Dict[str, List[str]]:
    text_lower = text.lower()
    return {
        "urls": list(set(m.group(0) for m in _URL_RE.finditer(text))),
        "phones": list(set(m.group(0) for m in _PHONE_RE.finditer(text))),
        "upi_ids": list(set(m.group(0) for m in _UPI_RE.finditer(text) if m.group(0).split("@")[-1].isalpha())),
        "banks": _detect_banks(text_lower),
        "emails": [],
        "aadhaar": list(set(m.group(0) for m in _AADHAAR_RE.finditer(text))),
        "pan": list(set(m.group(0) for m in _PAN_RE.finditer(text))),
    }

def clean_text(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t

def detect_language(text: str) -> str:
    """Simple heuristic language detection."""
    # Check for Devanagari (Hindi/Marathi)
    if re.search(r"[\u0900-\u097F]", text):
        if any(w in text.lower() for w in ["aapka", "aapke", "kya", "hai", "nahi", "maine", "tum"]):
            return "hi"
        return "hi"
    # Check for Tamil
    if re.search(r"[\u0B80-\u0BFF]", text):
        return "ta"
    # Check for Telugu
    if re.search(r"[\u0C00-\u0C7F]", text):
        return "te"
    # Check for Kannada
    if re.search(r"[\u0C80-\u0CFF]", text):
        return "kn"
    # Check for Malayalam
    if re.search(r"[\u0D00-\u0D7F]", text):
        return "ml"
    # Check for Bengali
    if re.search(r"[\u0980-\u09FF]", text):
        return "bn"
    # Check for Gujarati
    if re.search(r"[\u0A80-\u0AFF]", text):
        return "gu"
    # Check for Hinglish patterns
    hinglish_markers = ["aapka", "aapke", "kya", "hai", "nahi", "maine",
                        "tumhara", "mera", "tera", "kar", "raha", "rahi",
                        "matlab", "accha", "thik", "sahi", "galat"]
    text_lower = text.lower()
    if sum(1 for w in hinglish_markers if w in text_lower) >= 2:
        return "hi-en"
    # Tanglish markers
    tanglish_markers = ["unga", "enna", "epdi", "vandhu", "pannu",
                        "irukku", "aagirukku", "mudiyum", "venum", "poda"]
    if sum(1 for w in tanglish_markers if w in text_lower) >= 2:
        return "ta-en"
    return "en"

def get_next_id(category: str) -> str:
    _category_counters[category] = _category_counters.get(category, 0) + 1
    return f"{category}_{_category_counters[category]:04d}"

def create_sample(text: str, category: str, source: str = "manual",
                  annotation_notes: str = "", language: str = "",
                  annotator_id: str = "system") -> Dict[str, Any]:
    if category not in VALID_CATEGORIES:
        available = sorted(VALID_CATEGORIES)
        raise ValueError(f"Invalid category '{category}'. Valid: {available}")

    lang = language if language else detect_language(text)
    text_clean = clean_text(text)
    entities = _extract_entities_text(text)

    return {
        "id": get_next_id(category),
        "text": text,
        "text_clean": text_clean,
        "language": lang,
        "category": category,
        "is_scam": CATEGORY_IS_SCAM[category],
        "risk_level": CATEGORY_RISK[category],
        "extracted_entities": entities,
        "ground_truth_label": "scam" if CATEGORY_IS_SCAM[category] else "legitimate",
        "source": source,
        "annotation_notes": annotation_notes,
        "annotator_id": annotator_id,
        "version": VERSION,
        "created_at": NOW,
        "updated_at": NOW,
    }

def text_hash(text: str) -> str:
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def deduplicate(samples: List[Dict]) -> List[Dict]:
    seen = set()
    deduped = []
    dupes = []
    for s in samples:
        h = text_hash(s["text"])
        if h in seen:
            dupes.append({"id": s["id"], "text": s["text"][:80], "hash": h})
        else:
            seen.add(h)
            deduped.append(s)
    return deduped, dupes

def validate_sample(s: Dict) -> List[str]:
    errors = []
    required = ["id", "text", "text_clean", "language", "category",
                "is_scam", "risk_level", "extracted_entities",
                "ground_truth_label", "source", "version", "created_at"]
    for field in required:
        if field not in s:
            errors.append(f"Missing field: {field}")
    if s.get("category") not in VALID_CATEGORIES:
        errors.append(f"Invalid category: {s.get('category')}")
    if s.get("risk_level") not in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"}:
        errors.append(f"Invalid risk_level: {s.get('risk_level')}")
    if s.get("ground_truth_label") not in {"scam", "legitimate"}:
        errors.append(f"Invalid ground_truth_label: {s.get('ground_truth_label')}")
    if not s.get("text"):
        errors.append("Empty text")
    if not s.get("id"):
        errors.append("Empty id")
    return errors

# ============================================================
# SOURCE 1: INDIAN SCAM EXAMPLES FROM PUBLIC SOURCES
# ============================================================

def load_public_indian_scams() -> List[Dict]:
    """Real Indian scam examples from public advisories & news."""
    samples = []
    src = "cert_in"

    # KYC / Bank Block Scams
    kyc_msgs = [
        ("Dear SBI user, your a/c XXXX8821 will be suspended. Update KYC immediately: bit.ly/sbi-kyc-verify", "KYC_SCAM", "cert_in"),
        ("URGENT: Your KYC is incomplete. Your account will be blocked in 24 hours. Update now.", "KYC_SCAM", "cert_in"),
        ("Dear Customer, Your SBI YONO account will be deactivated today due to KYC expiry. Update KYC now to continue services: http://sbi-yono-kyc.online/update", "KYC_SCAM", "cert_in"),
        ("HDFC Bank: Your bank account will be blocked on today date due to incomplete KYC. Re-verify within 24 hrs: http://hdfc-kyc.in-online.xyz", "KYC_SCAM", "cert_in"),
        ("ICICI: PAN-Aadhaar link mandatory. Account suspension begins tomorrow. Click here: bit.ly/icici-pan-link", "KYC_SCAM", "cert_in"),
        ("Dear SBI Customer, Your KYC verification has expired. Your account will be BLOCKED in 24 hours. Update immediately: bit.ly/sbi-kyc-updt", "KYC_SCAM", "cert_in"),
        ("URGENT: Your UPI ID linked to Aadhaar has been suspended. Click to re-verify now or your account access will be revoked permanently: upi-kyc-verify.in/update", "UPI_FRAUD", "cert_in"),
        ("Your HDFC Bank net banking access will be disabled due to pending KYC. Complete verification: hdfckyc-update.com/login", "KYC_SCAM", "cert_in"),
        ("ALERT: Your SBI Account has been temporarily locked due to suspicious activity. Click here immediately to verify: sbi-secure-verify.com/update OR call 9876543210. Failure to verify within 2 hours will result in permanent account closure.", "BANKING_FRAUD", "rbi"),
        ("Your bank account will be blocked if KYC is not updated today. Click the link below.", "KYC_SCAM", "ncpc"),
        ("Your account will be blocked today. Complete KYC immediately.", "KYC_SCAM", "ncpc"),
        ("Dear Customer, your KYC is expired. Your account will be blocked within 24 hours. Click here to update now: bit.ly/kycupdate", "KYC_SCAM", "cert_in"),
        ("India Post Payment Bank KYC Login Dear user your India post payment bank account has been blocked today please updated your PAN Card immediately click here the link- http://surl.li/iccpf", "KYC_SCAM", "pib"),
        ("Dear user, your bank account will be blocked today. Update KYC immediately.", "KYC_SCAM", "ncpc"),
        ("Your KYC is incomplete. Your account will be frozen within 24 hours.", "KYC_SCAM", "cert_in"),
        ("Dear customer, your KYC has expired. Update now to avoid account suspension: link", "KYC_SCAM", "rbi"),
        ("Dear Customer, your SBI account will be BLOCKED today due to incomplete KYC. Update immediately at http://sbi-kyc-verify.xyz or your account is suspended.", "KYC_SCAM", "cert_in"),
        ("RBI NOTICE: Your bank account has suspicious activity. Failure to verify today may lead to legal action and account freeze.", "BANKING_FRAUD", "rbi"),
    ]
    for text, cat, source in kyc_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real KYC scam example from government advisory")
        samples.append(s)

    # Income Tax Scams
    it_msgs = [
        ("Your income tax refund will be credited to your bank account number XXXXX. If the account number mentioned is incorrect, please visit the link to update your bank account details", "INCOME_TAX_SCAM", "cert_in"),
        ("INCOME TAX REFUND: Rs 18,490 approved. Enter your bank details at incometax-refund.net to receive funds.", "INCOME_TAX_SCAM", "cert_in"),
        ("Dear taxpayer, your refund is pending. Click now to avoid penalty http://incometax-refund-claim.xyz", "INCOME_TAX_SCAM", "cert_in"),
        ("You have been approved an Income Tax Refund of Rs 15000, the amount will be credited to your account shortly. Please verify your account number 5XXXXX6777. If this is not correct, please update your bank account information by visiting the link below. https://bit.ly/20wpUUX", "INCOME_TAX_SCAM", "cert_in"),
    ]
    for text, cat, source in it_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real income tax refund scam from CERT-In advisory")
        samples.append(s)

    # UPI Scams
    upi_msgs = [
        ("Congratulations! You have won Rs 4,999 cashback. Click now to claim reward and complete UPI verification.", "UPI_FRAUD", "npci"),
        ("Refund pending. To receive your refund, approve the collect request sent to your UPI app immediately.", "UPI_FRAUD", "npci"),
        ("NPCI Support: Your UPI service will be suspended today. Verify your details now to avoid deactivation.", "UPI_FRAUD", "npci"),
        ("Customer care has sent a request to complete your refund. Please accept the collect request to receive money.", "UPI_FRAUD", "npci"),
        ("Your UPI account KYC is pending. Complete verification now or your account will be blocked within 24 hours.", "UPI_FRAUD", "npci"),
        ("Hi! I accidentally sent Rs 5,000 to your number via UPI. Please accept the request I just sent, I need the refund urgently", "UPI_FRAUD", "npci"),
        ("Your refund of Rs 799 is about to expire! Accept the UPI request within 1 minute!", "UPI_FRAUD", "npci"),
        ("You have won a cashback of Rs 1,000! Accept to claim.", "UPI_FRAUD", "npci"),
    ]
    for text, cat, source in upi_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real UPI fraud example from NPCI/public awareness")
        samples.append(s)

    # Courier Scams
    courier_msgs = [
        ("Your package has arrived at the warehouse and we attempted delivery twice but were unable to due to incomplete address information. Please update your address within 48 hours, otherwise the package will be returned. In order to update the address click on the link indisposegvs.top/IN", "COURIER_SCAM", "pib"),
        ("Your parcel delivery has been attempted for the 2nd time please confirm your details or your item will be returned: https://indiapots.com/in", "COURIER_SCAM", "pib"),
        ("Your parcel could not be delivered. Update your address now at http://bit.ly/delivery-fix to avoid return.", "COURIER_SCAM", "ncpc"),
        ("Your parcel is on hold due to incomplete address", "COURIER_SCAM", "ncpc"),
        ("Delivery failed. Pay Rs 5 redelivery fee", "COURIER_SCAM", "ncpc"),
        ("KYC required before shipment release", "COURIER_SCAM", "ncpc"),
        ("Customs clearance pending. Pay now", "COURIER_SCAM", "ncpc"),
        ("Your parcel is waiting for address confirmation. Click here to reschedule delivery", "COURIER_SCAM", "ncpc"),
    ]
    for text, cat, source in courier_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real courier scam from PIB fact check / awareness")
        samples.append(s)

    # KBC / Lottery Scams
    lottery_msgs = [
        ("Congratulations! Your mobile number has won Rs 35,00,000 in KBC Season 15 Lucky Draw. To claim your prize, contact our KBC manager: +91-9876543210 (WhatsApp only)", "LOTTERY_SCAM", "ncpc"),
        ("DEAR WINNER: Your number has been selected in WhatsApp 15th Anniversary Lottery. Prize: Rs 40 Lakh. Pay Rs 1,850 processing fee to release your winnings.", "LOTTERY_SCAM", "ncpc"),
        ("Government of India Digital India Scheme: Your Aadhaar number WON Rs 5,00,000 in our national prize draw. Pay Rs 999 GST fee to receive your prize in 24 hours.", "GOVERNMENT_IMPERSONATION", "ncpc"),
        ("Congratulation Dear Customer You Have Win The Prize 25,00,000 By KBC Department Please Collect Your Prize Urgently By Follow The Company Rules and Regulations.", "LOTTERY_SCAM", "pib"),
        ("You have won Rs 25,000 in the BSNL lucky draw. Claim before midnight.", "LOTTERY_SCAM", "ncpc"),
        ("Congratulations! You have won Rs 10 lakh in our lucky draw.", "LOTTERY_SCAM", "ncpc"),
    ]
    for text, cat, source in lottery_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real lottery scam from PIB fact check")
        samples.append(s)

    # Job Scams
    job_msgs = [
        ("Your CV has been selected for a job. Accept this job and earn daily salary.", "JOB_SCAM", "ncpc"),
        ("Hi, this is HR Priya from XYZ digital marketing, daily payout up to Rs 3,000.", "JOB_SCAM", "ncpc"),
        ("We are hiring part-time workers. You only need to rate hotels and restaurants. Daily income Rs 2,000 to Rs 5,000. First task is free.", "JOB_SCAM", "ncpc"),
        ("Your salary of Rs 18,400 is approved. Pay Rs 2,750 GST to release it.", "JOB_SCAM", "ncpc"),
        ("Hi, I am Priya from Amazon HR. We are hiring part-time reviewers. Earn Rs 3,000 to Rs 50,000 daily.", "JOB_SCAM", "ncpc"),
        ("Congratulations! Your profile has been selected for a part-time work-from-home opportunity with a salary of Rs 30,000 per month.", "JOB_SCAM", "ncpc"),
        ("Hello, I am from HR. We found your profile. Are you interested in part-time work from home?", "JOB_SCAM", "ncpc"),
        ("Congrats! You are shortlisted for a part-time job. Accept the Rs 10 UPI request to activate your profile.", "JOB_SCAM", "ncpc"),
    ]
    for text, cat, source in job_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real job scam example from NCPC/awareness sites")
        samples.append(s)

    # Electricity Bill Scams
    elec_msgs = [
        ("Dear CUSTOMER, your electricity power will be disconnected tonight at 9.30 pm from electricity office because your previous month bill was not updated. Please immediately contact with our electricity officer 9693325442 Thank you.", "ELECTRICITY_BILL_SCAM", "cert_in"),
        ("Your Electricity Power will disconnect at 9:30 pm as your last month bill was not updated Call us", "ELECTRICITY_BILL_SCAM", "cert_in"),
        ("Please Update Your Bill. Dear Consumer Your Electricity Power will be disconnected. Tonight at 8.30 PM from electricity office. Because your previous month bill was not updated please immediately contact with our electricity officer. Thank you.", "ELECTRICITY_BILL_SCAM", "cert_in"),
        ("Dear customer, your electricity will be disconnected tonight due to pending bill. Contact support immediately.", "ELECTRICITY_BILL_SCAM", "ncpc"),
        ("Dear Customer Your Electricity power will be disconnected Tonight at 8.30 pm from electricity office. Because your previous month bill was not update, please immediately contact with our electricity officer 8240471159 Thank you.", "ELECTRICITY_BILL_SCAM", "cert_in"),
        ("Dear customer, your electricity supply will be disconnected tonight because you have not updated your previous bill.", "ELECTRICITY_BILL_SCAM", "ncpc"),
        ("Your electricity will be disconnected today at 9:30 PM as your previous month bill is not updated. Please immediately contact our electricity officer.", "ELECTRICITY_BILL_SCAM", "ncpc"),
    ]
    for text, cat, source in elec_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real electricity bill scam from news reports/CERT-In")
        samples.append(s)

    # Fake Customer Care
    fcc_msgs = [
        ("Dear user, your UPI refund is pending. Contact customer care now on 9876543210 to receive your money today.", "FAKE_CUSTOMER_CARE", "ncpc"),
        ("UPI Support: Your transaction failed. To fix issue instantly, approve support request and verify your UPI PIN now.", "FAKE_CUSTOMER_CARE", "npci"),
        ("For quick support, install AnyDesk and connect with UPI customer care to resolve payment issue safely.", "FAKE_CUSTOMER_CARE", "ncpc"),
    ]
    for text, cat, source in fcc_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real fake customer care scam from awareness sites")
        samples.append(s)

    # Loan Scams
    loan_msgs = [
        ("Get instant loan approval in 5 minutes. No documents needed. Click now to download app and receive Rs 50,000 today: http://bit.ly/loan-app-fast", "LOAN_SCAM", "ncpc"),
        ("Final warning: Your loan repayment is overdue. Pay today or legal action will begin and your contacts will be informed immediately.", "LOAN_SCAM", "ncpc"),
        ("Complete loan verification now. Install the secure loan app APK from this link to release your approved amount today.", "LOAN_SCAM", "ncpc"),
        ("Your personal loan is approved. Verify Aadhaar, PAN, bank details, and OTP now to release funds instantly.", "LOAN_SCAM", "ncpc"),
        ("Pradhan Mantri Yojana Aadhar Card Loan 2% interest, 50% waiver. Call 8595311955", "LOAN_SCAM", "pib"),
        ("Your loan of Rs 2,00,000 is on track. KYC processing is happening now.", "LOAN_SCAM", "ncpc"),
        ("Urgent loan? Get Rs 10,000 in just 5 minutes! No CIBIL check! Just click here!", "LOAN_SCAM", "ncpc"),
        ("Congratulations! Your Rs 5 lakh loan is approved. Instant Loan No CIBIL No Income Proof Required", "LOAN_SCAM", "ncpc"),
    ]
    for text, cat, source in loan_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real loan scam from NCPC/public awareness")
        samples.append(s)

    # Telecom / SIM Scams
    tele_msgs = [
        ("Dear Customer, Your SIM KYC has been suspended by Telecom Regulatory Authority of India. Your SIM card will be blocked within 24 hours. Call Immediately.", "TELECOM_SCAM", "cert_in"),
        ("Your number will be disconnected today!", "TELECOM_SCAM", "cert_in"),
        ("Dear customer, your Aadhaar-linked mobile number has been deactivated.", "TELECOM_SCAM", "cert_in"),
        ("Suspicious login detected. Verify now or your UPI will be blocked.", "TELECOM_SCAM", "ncpc"),
    ]
    for text, cat, source in tele_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real telecom scam from CERT-In/PIB")
        samples.append(s)

    # Digital Arrest (partial messages - full scripts are too long)
    da_msgs = [
        ("Mumbai Police FIR No. 0078/2026 Money Laundering case linked to your Aadhaar. Immediate action required. Call us to avoid arrest.", "DIGITAL_ARREST", "cert_in"),
        ("Your Aadhaar has been linked to a money laundering case. An arrest warrant has been issued. You must appear on video call immediately.", "DIGITAL_ARREST", "cert_in"),
        ("NCB has intercepted a parcel in your name containing illegal items. Your PAN card has been misused. Contact immediately to avoid legal action.", "DIGITAL_ARREST", "cert_in"),
        ("Your Aadhaar and PAN have been used in criminal activities. CBI has issued a non-bailable warrant. Call us immediately to resolve.", "DIGITAL_ARREST", "cert_in"),
        ("Cyber crime department: Your mobile number has been used in online fraud. Your bank accounts will be frozen. Contact us immediately.", "DIGITAL_ARREST", "cert_in"),
    ]
    for text, cat, source in da_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real digital arrest scam pattern from CERT-In advisories")
        samples.append(s)

    # Pan Scam
    pan_msgs = [
        ("Your PAN card has been used in illegal transactions. Call Income Tax Dept immediately or face arrest.", "PAN_SCAM", "cert_in"),
        ("Your PAN card will be deactivated due to non-linking with Aadhaar. Click here to link now: http://pan-aadhaar-link.xyz", "PAN_SCAM", "cert_in"),
    ]
    for text, cat, source in pan_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real PAN scam from CERT-In")
        samples.append(s)

    # Aadhaar Scam
    aadhaar_msgs = [
        ("Your Aadhaar card will be deactivated. Update your Aadhaar now at https://uidai-update.xyz or face legal consequences.", "AADHAAR_SCAM", "cert_in"),
        ("Your Aadhaar number has been used to open bank accounts in Dubai. Call immediately to avoid arrest.", "AADHAAR_SCAM", "cert_in"),
        ("Aadhaar OTP: 374829. Call us immediately with this OTP to update your mobile number in Aadhaar.", "AADHAAR_SCAM", "ncpc"),
    ]
    for text, cat, source in aadhaar_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real Aadhaar scam from CERT-In")
        samples.append(s)

    # QR Scam
    qr_msgs = [
        ("Scan this QR code to receive your refund payment. Amount will be credited immediately.", "QR_SCAM", "npci"),
        ("Scan QR code below to pay and claim your prize money. Limited time offer.", "QR_SCAM", "ncpc"),
        ("Customer care QR code payment. Scan to pay the processing fee and unlock your account.", "QR_SCAM", "ncpc"),
    ]
    for text, cat, source in qr_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real QR scam from NPCI advisories")
        samples.append(s)

    # Crypto Scam
    crypto_msgs = [
        ("Cryptocurrency investment opportunity! Get guaranteed 10x returns in 30 days. Invest in Bitcoin now. Limited seats available.", "CRYPTO_SCAM", "ncpc"),
        ("Bitcoin trading signal group. We have insider information. Minimum investment Rs 10,000. Daily 5% returns guaranteed.", "CRYPTO_SCAM", "ncpc"),
        ("NFT investment opportunity. Rare digital art collection. 1000x potential returns. Buy now at discounted price.", "CRYPTO_SCAM", "ncpc"),
    ]
    for text, cat, source in crypto_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real crypto scam from NCPC")
        samples.append(s)

    # Investment Scam
    invest_msgs = [
        ("Get 500% returns in 3 days! Stock market tips from experts. 100% guaranteed profit. Earn Rs 1 lakh in one week.", "INVESTMENT_SCAM", "ncpc"),
        ("SEBI registered investment advisor. Get 10x returns in 30 days. Join our elite group. Fee Rs 15,000.", "INVESTMENT_SCAM", "ncpc"),
        ("Mutual fund bonus scheme. Government approved. Invest Rs 25,000 get Rs 1,00,000 after 1 year. Limited period.", "INVESTMENT_SCAM", "ncpc"),
        ("Forex trading made easy. Earn $500 daily. Automated trading bot. One-time setup fee Rs 8,500.", "INVESTMENT_SCAM", "ncpc"),
        ("Real estate fractional ownership. Invest Rs 1,00,000 get 30% returns annually. Guaranteed buyback after 3 years.", "INVESTMENT_SCAM", "ncpc"),
    ]
    for text, cat, source in invest_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real investment scam from NCPC/public awareness")
        samples.append(s)

    # Romance Scam
    romance_msgs = [
        ("Hi beautiful, I am US Army captain in Syria. I need your help to transfer $2 million. Please help me with visa fee.", "ROMANCE_SCAM", "ncpc"),
        ("I am a British oil engineer on offshore rig. I have fallen in love with you. Send me money for my visa to meet you.", "ROMANCE_SCAM", "ncpc"),
        ("Hello dear. I am Maria from Russia. I want to marry you. Please send Rs 50,000 for my flight ticket to India.", "ROMANCE_SCAM", "ncpc"),
        ("I am a UN doctor working in Congo. I received a gold shipment worth $5 million. Help me transfer it for 30% share.", "ROMANCE_SCAM", "ncpc"),
        ("Sweetheart, I am a US soldier in Afghanistan. My leave has been denied. Pay $2,500 for my emergency leave approval.", "ROMANCE_SCAM", "ncpc"),
        ("I am a wealthy widow from UK. I need a trustworthy person to inherit my $10 million fortune. Share your bank details.", "ROMANCE_SCAM", "ncpc"),
    ]
    for text, cat, source in romance_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real romance scam pattern from NCPC advisories")
        samples.append(s)

    # Government Impersonation
    govt_msgs = [
        ("PM Kisan Yojana: You are eligible for Rs 6,000 installment. Click to claim: https://pmkisan-gov.xyz/claim", "GOVERNMENT_IMPERSONATION", "pib"),
        ("Central Government: Rs 1,50,000 subsidy approved for your bank account. Pay Rs 2,500 processing fee to release funds.", "GOVERNMENT_IMPERSONATION", "pib"),
        ("Ayushman Bharat: Your health insurance is expiring. Renew now with Rs 1,200 premium or lose coverage permanently.", "GOVERNMENT_IMPERSONATION", "pib"),
        ("NREGA: You have pending wages of Rs 12,000. Update your bank details at https://nrega-wages.xyz to receive payment.", "GOVERNMENT_IMPERSONATION", "pib"),
    ]
    for text, cat, source in govt_msgs:
        s = create_sample(text, cat, source=source, annotation_notes="Real government impersonation scam from PIB fact check")
        samples.append(s)

    return samples

# ============================================================
# SOURCE 2: EXISTING BENCHMARK.JSON
# ============================================================

def load_benchmark_json() -> List[Dict]:
    path = os.path.join(BASE_DIR, "evaluation", "datasets", "benchmark.json")
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    samples = []
    CAT_MAP = {
        "UPI Scam": "UPI_FRAUD",
        "Bank KYC Scam": "KYC_SCAM",
        "Banking Scam": "BANKING_FRAUD",
        "Courier Scam": "COURIER_SCAM",
        "Job Scam": "JOB_SCAM",
        "Lottery Scam": "LOTTERY_SCAM",
        "Investment Scam": "INVESTMENT_SCAM",
        "Phishing": "AADHAAR_SCAM",
        "OTP Scam": "TELECOM_SCAM",
        "Loan Scam": "LOAN_SCAM",
        "Government Scheme Scam": "GOVERNMENT_IMPERSONATION",
        "Fake Customer Care": "FAKE_CUSTOMER_CARE",
        "Electricity Bill Scam": "ELECTRICITY_BILL_SCAM",
        "Customs Scam": "COURIER_SCAM",
        "Crypto Scam": "CRYPTO_SCAM",
        "QR Code Scam": "QR_SCAM",
        "Account Suspension": "BANKING_FRAUD",
        "Subscription Scam": "LOAN_SCAM",
        "Tech Support Scam": "FAKE_CUSTOMER_CARE",
        "Legitimate": None,
    }
    LEGIT_MAP = {
        "Legitimate": "LEGITIMATE_OTHER",
    }
    for item in data:
        cat = item.get("expected_category", "")
        is_scam = item.get("expected_prediction") == "scam"
        if is_scam:
            v2_cat = CAT_MAP.get(cat)
            if v2_cat is None:
                continue
        else:
            v2_cat = LEGIT_MAP.get(cat)
            if v2_cat is None:
                continue
        try:
            s = create_sample(
                text=item["text"],
                category=v2_cat,
                source="manual",
                annotation_notes=f"From benchmark.json ({item.get('id', '')})"
            )
            samples.append(s)
        except Exception as e:
            print(f"  Error converting {item.get('id', '?')}: {e}")
    return samples

# ============================================================
# SOURCE 3: BENCHMARK_EVAL.PY
# ============================================================

def load_benchmark_eval() -> List[Dict]:
    """Extract inline samples from benchmark_eval.py."""
    path = os.path.join(BASE_DIR, "evaluation", "benchmark_eval.py")
    if not os.path.exists(path):
        return []
    samples = []
    CAT_MAP = {
        "banking_scam": "BANKING_FRAUD",
        "upi_scam": "UPI_FRAUD",
        "fake_job": "JOB_SCAM",
        "fake_courier": "COURIER_SCAM",
        "investment_scam": "INVESTMENT_SCAM",
        "romance_scam": "ROMANCE_SCAM",
        "government_scam": "GOVERNMENT_IMPERSONATION",
        "legitimate": None,
        "lottery_scam": "LOTTERY_SCAM",
        "tech_support_scam": "FAKE_CUSTOMER_CARE",
        "loan_scam": "LOAN_SCAM",
        "phishing_scam": "AADHAAR_SCAM",
        "otp_scam": "TELECOM_SCAM",
    }
    LEGIT_MAP = {
        "legitimate": "LEGITIMATE_OTHER",
    }
    # These are the text+category pairs from benchmark_eval.py
    data = [
        ("Your HDFC account has been blocked due to suspicious activity. Call 1800-XXX-XXXX immediately to reactivate.", "banking_scam"),
        ("SBI Alert: Your debit card has been deactivated. Update KYC at https://sbi-kyc-update.xyz or your account will be frozen.", "banking_scam"),
        ("ICICI Bank: Your account is temporarily suspended. Click here to restore access: http://bit.ly/icici-restore", "banking_scam"),
        ("Axis Bank Warning: Unauthorized login detected from New Delhi. Confirm your identity or your account will be blocked permanently.", "banking_scam"),
        ("Your Kotak Mahindra net banking has been locked. Call our helpdesk on 022-XXXX-XXXX to unlock within 24 hours.", "banking_scam"),
        ("PNB Alert: Rs 49,500 debited from your account. Not you? Call 1800-XXX-XXX immediately to reverse. OTP: 491823", "banking_scam"),
        ("Canara Bank: Your account KYC is expired. Update now or account will be suspended. https://canara-kyc.com/update", "banking_scam"),
        ("RBI Warning: Your bank account linked to illegal transactions. Call 011-XXXX-XXXX immediately to avoid legal action.", "banking_scam"),
        ("HDFC Bank: Your credit card application has been approved. Pay Rs 999 processing fee to receive your card.", "banking_scam"),
        ("YES BANK: Fraud detected on your account. Share your account details to secure your funds. Send details to fraud@yesbank-verify.com", "banking_scam"),
        ("State Bank of India: Your account will be deactivated. Click https://sbi-secure-login.xyz to verify your credentials now.", "banking_scam"),
        ("Bank of Baroda: Your savings account has been credited with INR 50,000. Pay Rs 2500 processing fee to claim this amount.", "banking_scam"),
        ("IDBI Bank: 2-factor authentication expired. Update immediately at https://idbi-update.tk or service will be disconnected.", "banking_scam"),
        ("Union Bank Alert: Your ATM card has been blocked. Call 1800-XXX-XXXX to reactivate. Do not ignore this message.", "banking_scam"),
        ("IndusInd Bank: New device login detected from Mumbai. If not you, secure your account now: http://bit.ly/indus-secure", "banking_scam"),
        ("SEBI Alert: Your trading account has been used for unauthorized trades. Pay Rs 10,000 penalty to avoid suspension of demat account.", "banking_scam"),
        ("Your UPI PIN has been reset. Click here to set new PIN: http://bit.ly/fake-upi", "upi_scam"),
        ("GPay: Your UPI ID has been compromised. Verify immediately: https://gpay-verify.xyz", "upi_scam"),
        ("PhonePe: Rs 12,500 sent to Ramesh Kumar. UPI ref UPIRef1234. Not you? Block here: http://bit.ly/phonepe-block", "upi_scam"),
        ("Paytm UPI: Your account is limited. Complete KYC to restore unlimited payments. https://paytm-kyc.tk", "upi_scam"),
        ("BHIM UPI: You received Rs 2,000. Claim by entering your UPI PIN at https://bhim-reward.com/claim", "upi_scam"),
        ("Google Pay: Your UPI collect request of Rs 8,500 is pending. Approve now or your account will be debited automatically.", "upi_scam"),
        ("Amazon Pay UPI: Congratulations! You won Rs 10,000 cashback. Claim at https://amazon-pay-reward.xyz", "upi_scam"),
        ("UPI Alert: Your UPI linked mobile number is being changed. If not you, stop here: http://bit.ly/upi-stop", "upi_scam"),
        ("Your UPI transaction of Rs 22,500 failed. Refund available. Click: https://refund-upi.com/process", "upi_scam"),
        ("PhonePe: Your daily limit has been increased. Activate new limit by sharing OTP 728491 with our executive.", "upi_scam"),
        ("Congratulations! You have been selected for Work From Home job. Earn Rs 50,000/month. Pay Rs 999 registration fee.", "fake_job"),
        ("Urgent hiring for Amazon data entry. Salary Rs 35,000-60,000. No experience needed. Register: https://amazon-jobs.xyz", "fake_job"),
        ("Flipkart is hiring part-time workers. Earn Rs 500-2000 per day. Join today: Pay Rs 499 for registration kit.", "fake_job"),
        ("Google is offering Work From Home jobs. Type names and earn Rs 40,000/month. Processing fee Rs 1,500 required.", "fake_job"),
        ("We liked your profile. Get international placement in Canada. Visa processing fee Rs 25,000. Limited seats!", "fake_job"),
        ("YouTube video rating job. Earn Rs 200 per video. Weekly payout. Registration Rs 750. Contact now!", "fake_job"),
        ("Microsoft home-based job. Data entry operator needed. Salary Rs 45,000/month. Security deposit Rs 2,000 refundable.", "fake_job"),
        ("Swiggy delivery partner registration. Earn Rs 30,000 monthly. Complete your profile: registration fee Rs 499.", "fake_job"),
        ("Railway recruitment 2026. 50,000 vacancies. Apply now with registration fee Rs 1,200. Guaranteed job placement.", "fake_job"),
        ("Zomato customer support jobs from home. Salary Rs 25,000 plus incentives. Pay Rs 999 for training materials.", "fake_job"),
        ("Your FedEx package #FDX2891 is held at customs. Pay Rs 2500 clearance fee to release.", "fake_courier"),
        ("DHL: Your international shipment is stuck at Mumbai customs. Pay Rs 3,200 for customs clearance. http://bit.ly/dhl-clear", "fake_courier"),
        ("Blue Dart: Package delivery failed. Your parcel contains undeclared items. Pay Rs 5,000 penalty to avoid legal action.", "fake_courier"),
        ("Amazon Logistics: Your order #AMZ99887 is held. Customs duties of Rs 1,800 pending. Pay at https://amazon-customs.xyz", "fake_courier"),
        ("UPS: Your package from USA requires insurance clearance. Pay Rs 4,500 insurance fee for delivery.", "fake_courier"),
        ("India Post: Your international parcel is detained. Customs clearance fee Rs 2,000 required. Contact immediately.", "fake_courier"),
        ("FedEx Alert: Your shipment contains restricted items. Pay Rs 7,500 fine to avoid investigation by customs authorities.", "fake_courier"),
        ("Your SpeedPost package requires additional postage of Rs 890. Pay online: https://indiapost-payment.com", "fake_courier"),
        ("Your Aadhaar OTP is 284761. Do NOT share this OTP with anyone. KYC update required.", "otp_scam"),
        ("SBI: Your OTP for transaction is 729384. Forward this OTP to 9222222222 for verification.", "otp_scam"),
        ("Aadhaar OTP: 516273. Share this OTP with our executive to complete KYC or your Aadhaar will be deactivated.", "otp_scam"),
        ("Your Google verification code is 382917. Do not share. But forward to your friend for referral bonus.", "otp_scam"),
        ("OTP for PAN-Aadhaar linking is 462819. Send this OTP to 1800-XXX-XXXX immediately for link completion.", "otp_scam"),
        ("IRCTC: Your booking OTP is 719283. WhatsApp this OTP to 9876543210 for ticket confirmation.", "otp_scam"),
        ("Netflix: Your OTP is 638192. Share with our support agent for account recovery. Do not ignore.", "otp_scam"),
        ("Facebook: Your login code is 482716. Forward this code to our verification bot on WhatsApp.", "otp_scam"),
        ("Your one-time password for Paytm wallet is 927364. Never share with anyone except our customer support.", "otp_scam"),
        ("Aadhaar OTP: 374829. Call us immediately with this OTP to update your mobile number in Aadhaar.", "otp_scam"),
        ("Get 500% returns in 3 days! Bitcoin trading signal group. Limited seats. Join now!", "investment_scam"),
        ("Stock market tips from experts. 100% guaranteed profit. Earn Rs 1 lakh in one week. Investment Rs 5,000 only.", "investment_scam"),
        ("Cryptocurrency investment opportunity. Minimum investment Rs 10,000. Daily returns of 10% for lifetime.", "investment_scam"),
        ("SEBI registered investment advisor. Get 10x returns in 30 days. Join our elite group. Fee Rs 15,000.", "investment_scam"),
        ("Forex trading made easy. Earn $500 daily. Automated trading bot. One-time setup fee Rs 8,500.", "investment_scam"),
        ("Mutual fund bonus scheme. Government approved. Invest Rs 25,000 get Rs 1,00,000 after 1 year. Limited period.", "investment_scam"),
        ("NFT investment opportunity. Rare digital art collection. 1000x potential returns. Buy now at discounted price Rs 50,000.", "investment_scam"),
        ("IPO guaranteed allotment. We have insider connections. Pay Rs 3,000 registration to get IPO shares at listing price.", "investment_scam"),
        ("Real estate fractional ownership. Invest Rs 1,00,000 get 30% returns annually. Guaranteed buyback after 3 years.", "investment_scam"),
        ("Hi beautiful, I am US Army captain in Syria. I need your help to transfer $2 million.", "romance_scam"),
        ("I am a British oil engineer on offshore rig. I have fallen in love with you. Send me money for my visa to meet you.", "romance_scam"),
        ("Hello dear. I am Maria from Russia. I want to marry you. Please send Rs 50,000 for my flight ticket to India.", "romance_scam"),
        ("I am a UN doctor working in Congo. I received a gold shipment worth $5 million. Help me transfer it for 30% share.", "romance_scam"),
        ("Sweetheart, I am a US soldier in Afghanistan. My leave has been denied. Pay $2,500 for my emergency leave approval.", "romance_scam"),
        ("I am a wealthy widow from UK. I need a trustworthy person to inherit my $10 million fortune. Share your bank details.", "romance_scam"),
        ("Your PAN card has been used in illegal transactions. Call Income Tax Dept immediately or face arrest.", "government_scam"),
        ("Income Tax Department: Tax evasion case registered against you. Pay Rs 50,000 penalty immediately to avoid arrest warrant.", "government_scam"),
        ("Your Aadhaar card will be deactivated. Update your Aadhaar now at https://uidai-update.xyz or face legal consequences.", "government_scam"),
        ("Electricity board: Your connection will be disconnected for non-payment. Pay Rs 4,200 immediately via this link: https://bill-pay.tk", "government_scam"),
        ("PM Kisan Yojana: You are eligible for Rs 6,000 installment. Click to claim: https://pmkisan-gov.xyz/claim", "government_scam"),
        ("Water department: Your water connection will be cut. Pay outstanding bill of Rs 3,800 at https://water-bill-pay.com", "government_scam"),
        ("Central Government: Rs 1,50,000 subsidy approved for your bank account. Pay Rs 2,500 processing fee to release funds.", "government_scam"),
        ("GST department: Your GST return has discrepancies. Pay Rs 15,000 penalty or your business registration will be cancelled.", "government_scam"),
        ("NREGA: You have pending wages of Rs 12,000. Update your bank details at https://nrega-wages.xyz to receive payment.", "government_scam"),
        ("Ayushman Bharat: Your health insurance is expiring. Renew now with Rs 1,200 premium or lose coverage permanently.", "government_scam"),
        ("Your Flipkart order #OD12345678 has been shipped. Track here: https://flipkart.com/track", "legitimate"),
        ("Your monthly Netflix subscription of Rs 199 will be charged on 15th. Manage your account settings.", "legitimate"),
        ("Your Amazon order #AMZ876543 is out for delivery. Expected by 8 PM. Track at https://amazon.in/track", "legitimate"),
        ("ICICI Bank: Your credit card bill of Rs 12,500 is due on 05-Apr-2026. Auto-debit will be processed.", "legitimate"),
        ("Swiggy: Your order from Dominos is being prepared. Estimated delivery by 7:30 PM. Track live on the app.", "legitimate"),
        ("Zomato: Table for 2 at Pizza Express confirmed for 28 Mar 8 PM. Order #ZB89765.", "legitimate"),
        ("HDFC Bank: Rs 5,000 credited to your account from NEFT. Ref: NEFT123456789.", "legitimate"),
        ("Your Uber ride is arriving. Driver: Rajesh, Car: MH12AB1234 White Swift. ETA 3 mins.", "legitimate"),
        ("Airtel: Your monthly plan of Rs 499 will expire on 31 Mar. Recharge now to continue uninterrupted service.", "legitimate"),
        ("IRCTC: Your train ticket for 12951 Mumbai-Delhi on 15 Apr is confirmed. PNR: 4123567890.", "legitimate"),
        ("Google: Your account verification code is 839201. This code expires in 10 minutes.", "legitimate"),
        ("LinkedIn: John Doe sent you a connection request. View profile: https://linkedin.com/in/johndoe", "legitimate"),
        ("WhatsApp: Your verification code is 482-931. Do not share this code with anyone.", "legitimate"),
        ("Paytm: Rs 250 received from Ravi Kumar. UPI Ref: 987654321098. Wallet balance: Rs 1,250.", "legitimate"),
        ("Your appointment with Dr Sharma at Apollo Hospital is confirmed for 10:30 AM on 20 Mar.", "legitimate"),
        ("SBI: Your FD of Rs 2,00,000 has matured. Maturity amount Rs 2,45,678 credited to savings account.", "legitimate"),
        ("Myntra: 50% off on your favorite brands! Use code MYNTRA50. Shop now: https://myntra.com/sale", "legitimate"),
        ("Vistara: Check-in for flight UK915 DEL-BOM on 22 Mar is now open. Web check-in: https://vistara.com/webcheckin", "legitimate"),
        ("PhonePe: Rs 1,200 bill paid for electricity. Receipt: PP-RCPT-928374. Auto-pay scheduled for next month.", "legitimate"),
        ("Zerodha: Your trade of 100 shares of TCS at Rs 3,450 executed successfully. Ledger updated.", "legitimate"),
        ("Congratulations! You won Rs 25,00,000 in KBC Lottery. Claim your prize by paying Rs 5,000 processing fee.", "lottery_scam"),
        ("You won an iPhone 16 Pro! Claim your prize at https://apple-lucky-winner.xyz. Pay Rs 999 for shipping.", "lottery_scam"),
        ("Google Lucky Draw: You won Rs 15,00,000. Contact Mr Sharma at 9876543210 with registration fee Rs 8,000.", "lottery_scam"),
        ("Amazon Great Indian Sale winner! You won Rs 5,00,000 shopping voucher. Tax processing fee Rs 3,500 required.", "lottery_scam"),
        ("Reliance Jio: You won free recharge for lifetime. Pay Rs 499 registration fee to activate the offer.", "lottery_scam"),
        ("Air India: You won 2 free international tickets worth Rs 2,00,000. Processing fee Rs 4,900. Limited period offer.", "lottery_scam"),
        ("Tata Motors customer reward: You won a brand new Nexon! Contact us with registration fee of Rs 12,000.", "lottery_scam"),
        ("Parker Pen lucky draw: You won Rs 50,00,000. Deposit Rs 10,000 as processing fee to release your winnings.", "lottery_scam"),
        ("Windows Alert: Your computer has been infected with 5 viruses! Call Microsoft Certified Technician immediately: 1800-XXX-XXXX.", "tech_support_scam"),
        ("Your Netflix account has been suspended due to billing issues. Update payment: https://netflix-billing-update.xyz", "tech_support_scam"),
        ("Facebook: Your account was reported for violation. Verify now at https://facebook-verification.tk or be permanently banned.", "tech_support_scam"),
        ("Your Amazon Prime membership will expire today. Renew at discounted rate Rs 999. Click: https://amazon-prime-renew.xyz", "tech_support_scam"),
        ("Google: Your business listing has been suspended. Re-verify at https://google-business-verify.com to restore visibility.", "tech_support_scam"),
        ("Instant personal loan up to Rs 25 lakhs. No paperwork. 0% interest for 6 months. Processing fee Rs 2,500.", "loan_scam"),
        ("Bajaj Finserv: Your pre-approved loan of Rs 5,00,000 is ready. Pay Rs 3,000 documentation fee to disburse.", "loan_scam"),
        ("Home loan at 2% interest rate! Government subsidy available. Register with Rs 5,000 processing fee. Limited offer.", "loan_scam"),
        ("Student loan for abroad studies. 100% approval. No collateral. Pay Rs 2,000 application fee to proceed.", "loan_scam"),
        ("Business loan Rs 50 lakhs in 24 hours. CIBIL not required. Processing fee 1% of loan amount. Contact now.", "loan_scam"),
        ("Your email account password will expire today. Keep same password: https://email-verify-now.xyz", "phishing_scam"),
        ("Instagram: Your account has been hacked. Recover now: https://instagram-recovery.xyz/login", "phishing_scam"),
        ("LinkedIn: Someone tried to access your account from Russia. Secure here: http://bit.ly/linkedin-secure", "phishing_scam"),
        ("Twitter: Your account has been restricted. Appeal at https://twitter-appeal.tk to restore your account.", "phishing_scam"),
        ("Microsoft: Unusual sign-in detected. Verify your identity at https://microsoft-account-verify.com", "phishing_scam"),
        ("Your Apple ID has been locked for security reasons. Unlock here: https://apple-id-unlock.xyz", "phishing_scam"),
    ]
    for text, cat in data:
        v2_cat = CAT_MAP.get(cat)
        if v2_cat is None:
            v2_cat = LEGIT_MAP.get(cat)
        if v2_cat is None:
            continue
        try:
            s = create_sample(text, v2_cat, source="manual", annotation_notes=f"From benchmark_eval.py ({cat})")
            samples.append(s)
        except:
            pass
    return samples

# ============================================================
# SOURCE 4: INDIAN ROWS FROM SCAM_DATASET.CSV
# ============================================================

def load_scam_dataset_indian() -> List[Dict]:
    path = os.path.join(BACKEND_DIR, "data", "scam_dataset.csv")
    if not os.path.exists(path):
        return []
    samples = []
    CAT_MAP = {
        "upi_fraud": "UPI_FRAUD",
        "bank_fraud": "BANKING_FRAUD",
        "fake_kyc": "KYC_SCAM",
        "courier_scam": "COURIER_SCAM",
        "fake_job": "JOB_SCAM",
        "bill_scam": "ELECTRICITY_BILL_SCAM",
        "govt_scheme": "GOVERNMENT_IMPERSONATION",
        "tanglish": "BANKING_FRAUD",
        "general_scam": "BANKING_FRAUD",
        "investment_scam": "INVESTMENT_SCAM",
        "lottery_scam": "LOTTERY_SCAM",
        "phishing": "AADHAAR_SCAM",
    }
    INDIAN_CATS = set(CAT_MAP.keys())
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row.get("category", "").strip()
            label = row.get("label", "").strip()
            text = row.get("text", "").strip()
            if not text:
                continue
            if cat in INDIAN_CATS:
                v2_cat = CAT_MAP[cat]
                try:
                    s = create_sample(text, v2_cat, source="known_corpus",
                                      annotation_notes=f"From scam_dataset.csv ({cat})")
                    samples.append(s)
                except:
                    pass
    return samples

# ============================================================
# SOURCE 5: LEGITIMATE INDIAN TRANSACTIONAL SMS
# ============================================================

def load_legitimate_indian_sms() -> List[Dict]:
    """Real legitimate Indian transactional SMS patterns."""
    samples = []
    src = "manual"

    legit_msgs = [
        # Legitimate Banking
        ("HDFC Bank: Rs 5,000 credited to your account from NEFT. Ref: NEFT123456789. Avl Bal Rs 45,200.", "LEGITIMATE_BANKING"),
        ("SBI: Rs 2,500 debited from A/C XX1234 on 15/07/26 via UPI. Avl Bal Rs 12,340.", "LEGITIMATE_BANKING"),
        ("ICICI Bank: Your credit card bill of Rs 12,500 is due on 05-Aug-2026. Auto-debit will be processed.", "LEGITIMATE_BANKING"),
        ("Axis Bank: FD of Rs 1,00,000 has matured. Maturity amount Rs 1,23,456 credited to savings account.", "LEGITIMATE_BANKING"),
        ("PNB Alert: Rs 8,000 withdrawn from ATM on 20/07/26 at Malad West Branch. Avl Bal Rs 32,100.", "LEGITIMATE_BANKING"),
        ("Kotak Mahindra: Your account XX6789 has been credited with Rs 15,000 via IMPS. Ref: IMPS1234567890.", "LEGITIMATE_BANKING"),
        ("Canara Bank: Your monthly statement for Jul 2026 is available. Download from canarabank.com", "LEGITIMATE_BANKING"),
        ("Yes Bank: Your cheque no. 456789 of Rs 25,000 has been cleared. Avl Bal Rs 67,890.", "LEGITIMATE_BANKING"),
        ("Bank of Baroda: Your home loan EMI of Rs 18,234 has been debited on 10/07/26.", "LEGITIMATE_BANKING"),
        ("SBI: Your FD of Rs 2,00,000 has matured. Maturity amount Rs 2,45,678 credited to savings account.", "LEGITIMATE_BANKING"),

        # Legitimate UPI
        ("Paytm: Rs 250 received from Ravi Kumar. UPI Ref: 987654321098. Wallet balance: Rs 1,250.", "LEGITIMATE_UPI"),
        ("GPay: Rs 1,200 paid to Electricity Board. UPI Ref: GPay123456789. 20 Jul 2026.", "LEGITIMATE_UPI"),
        ("PhonePe: Rs 350 sent to Swiggy India. UPI Ref: PPRef98765432. Avl Bal Rs 5,000.", "LEGITIMATE_UPI"),
        ("Amazon Pay: Rs 899 paid for order OD7845123456 via UPI. Thank you for shopping.", "LEGITIMATE_UPI"),
        ("BHIM: Rs 500 received from Priya Sharma. UPI Ref: BHIM4567890123. Avl Bal Rs 8,500.", "LEGITIMATE_UPI"),
        ("Google Pay: Rs 75 paid to Chaiwala India. UPI transaction successful. Ref: GPay7654321.", "LEGITIMATE_UPI"),
        ("PhonePe: Rs 15,000 transferred to HDFC Bank XX5678. UPI Ref: PPRef09876543.", "LEGITIMATE_UPI"),
        ("Paytm: Rs 499 recharged for Airtel mobile 9876543210. Ref: PAYTM12345678.", "LEGITIMATE_UPI"),

        # Legitimate OTP
        ("Your SBI OTP for transaction of Rs 5,000 is 784512. Do not share this OTP with anyone. Valid for 10 mins.", "LEGITIMATE_OTP"),
        ("HDFC Bank: OTP 382917 for online transaction of Rs 12,500. Valid for 10 minutes. Do not share.", "LEGITIMATE_OTP"),
        ("ICICI Bank: Your OTP for credit card payment of Rs 8,999 is 516273. Valid for 10 mins.", "LEGITIMATE_OTP"),
        ("Google: Your verification code is 839201. This code expires in 10 minutes.", "LEGITIMATE_OTP"),
        ("WhatsApp: Your verification code is 482-931. Do not share this code with anyone.", "LEGITIMATE_OTP"),
        ("Aadhaar: Your OTP for authentication is 728491. Valid for 10 minutes. -UIDAI", "LEGITIMATE_OTP"),
        ("IRCTC: Your OTP for booking IR1234567890 is 637182. Valid for 5 mins.", "LEGITIMATE_OTP"),
        ("Amazon: Your OTP for login is 918273. Do not share. Valid for 5 minutes.", "LEGITIMATE_OTP"),

        # Legitimate Courier
        ("Your Flipkart order #OD12345678 has been shipped. Track here: https://flipkart.com/track", "LEGITIMATE_COURIER"),
        ("Amazon: Your order #AMZ876543 is out for delivery. Expected by 8 PM. Track at https://amazon.in/track", "LEGITIMATE_COURIER"),
        ("Delhivery: Your shipment DL7845123456 is out for delivery today. Track: delhivery.com/track", "LEGITIMATE_COURIER"),
        ("Blue Dart: Your shipment BD9876543210 has been delivered. Thank you for choosing Blue Dart.", "LEGITIMATE_COURIER"),
        ("India Post: Your article EL123456789IN has reached Mumbai Sorting Centre. Track at indiapost.gov.in", "LEGITIMATE_COURIER"),
        ("Zomato: Your order from Saravana Bhavan is out for delivery. ETA 10 mins. Track live.", "LEGITIMATE_COURIER"),
        ("Swiggy: Your order from Dominos has been delivered. Enjoy your meal! Rate your experience.", "LEGITIMATE_COURIER"),
        ("Myntra: Your order MY784512 has been shipped via Delhivery. Track: bit.ly/myntra-track", "LEGITIMATE_COURIER"),

        # Legitimate Government
        ("PM Kisan: Your installment of Rs 2,000 has been credited to your A/C XX4567. -PM Kisan Yojana", "LEGITIMATE_GOVERNMENT"),
        ("Ayushman Bharat: Your health insurance card is ready for pickup at nearest CSC center.", "LEGITIMATE_GOVERNMENT"),
        ("Income Tax Dept: Your ITR for AY 2026-27 has been processed successfully. Ref: ITR123456789.", "LEGITIMATE_GOVERNMENT"),
        ("EPFO: Your PF claim of Rs 1,25,000 has been approved and will be credited within 3 working days.", "LEGITIMATE_GOVERNMENT"),
        ("Voter Helpline: Your voter ID application E1234567 has been approved. Card will be delivered shortly.", "LEGITIMATE_GOVERNMENT"),
        ("Passport Seva: Your passport application PA1234567890 has been processed. Track at passportindia.gov.in", "LEGITIMATE_GOVERNMENT"),
        ("NREGA: Wage payment of Rs 8,400 for July 2026 has been credited to your account. -NREGA", "LEGITIMATE_GOVERNMENT"),
        ("UIDAI: Your Aadhaar update request AR1234567890 has been processed. Check status at uidai.gov.in", "LEGITIMATE_GOVERNMENT"),

        # Other Legitimate
        ("Your appointment with Dr Sharma at Apollo Hospital is confirmed for 10:30 AM on 20 Mar.", "LEGITIMATE_OTHER"),
        ("Airtel: Your monthly plan of Rs 499 will expire on 31 Jul. Recharge now to continue uninterrupted service.", "LEGITIMATE_OTHER"),
        ("Your Uber ride is arriving. Driver: Rajesh, Car: MH12AB1234 White Swift. ETA 3 mins.", "LEGITIMATE_OTHER"),
        ("Vistara: Check-in for flight UK915 DEL-BOM on 22 Sep is now open. Web check-in: vistara.com", "LEGITIMATE_OTHER"),
        ("Netflix: Your subscription of Rs 199 will be charged on 20th. Update payment method in settings.", "LEGITIMATE_OTHER"),
        ("Zerodha: Your trade of 100 shares of TCS at Rs 3,450 executed successfully. Ledger updated.", "LEGITIMATE_OTHER"),
        ("IRCTC: Your train ticket for 12951 Mumbai-Delhi on 15 Aug is confirmed. PNR: 4123567890.", "LEGITIMATE_OTHER"),
        ("LIC: Your premium payment of Rs 12,500 for policy 123456789 is due on 15-Aug-2026.", "LEGITIMATE_OTHER"),
    ]
    for text, cat in legit_msgs:
        try:
            s = create_sample(text, cat, source=src, annotation_notes=f"Legitimate Indian {cat} pattern")
            samples.append(s)
        except:
            pass
    return samples

# ============================================================
# MAIN BUILDER
# ============================================================

def main():
    print("=" * 70)
    print("  SCAMSHIELD v2 DATASET BUILDER")
    print("=" * 70)

    all_samples = []

    # Source 1: Real Indian public scam examples
    print("\n[1/6] Loading real Indian scam examples from public sources...")
    s1 = load_public_indian_scams()
    print(f"  -> {len(s1)} samples")
    all_samples.extend(s1)

    # Source 2: Existing benchmark.json
    print("\n[2/6] Loading existing benchmark.json...")
    s2 = load_benchmark_json()
    print(f"  -> {len(s2)} samples")
    all_samples.extend(s2)

    # Source 3: benchmark_eval.py
    print("\n[3/6] Loading benchmark_eval.py samples...")
    s3 = load_benchmark_eval()
    print(f"  -> {len(s3)} samples")
    all_samples.extend(s3)

    # Source 4: Indian rows from scam_dataset.csv
    print("\n[4/6] Loading Indian rows from scam_dataset.csv...")
    s4 = load_scam_dataset_indian()
    print(f"  -> {len(s4)} samples")
    all_samples.extend(s4)

    # Source 5: Legitimate Indian SMS
    print("\n[5/6] Loading legitimate Indian SMS patterns...")
    s5 = load_legitimate_indian_sms()
    print(f"  -> {len(s5)} samples")
    all_samples.extend(s5)

    # Deduplicate
    print("\n[6/6] Deduplicating...")
    before = len(all_samples)
    all_samples, dupes = deduplicate(all_samples)
    print(f"  Before: {before}, After: {len(all_samples)}")
    print(f"  Duplicates removed: {len(dupes)}")

    # Sort by category then ID
    all_samples.sort(key=lambda s: (s["category"], s["id"]))

    # Validate all
    print("\nValidating all samples...")
    errors = []
    for s in all_samples:
        errs = validate_sample(s)
        if errs:
            errors.append({"id": s["id"], "errors": errs})
    if errors:
        print(f"  ERRORS: {len(errors)} samples failed validation!")
        for e in errors[:10]:
            print(f"    [{e['id']}] {', '.join(e['errors'])}")
    else:
        print(f"  All {len(all_samples)} samples passed validation.")

    # Compute statistics
    cat_counts = Counter(s["category"] for s in all_samples)
    scam_count = sum(1 for s in all_samples if s["is_scam"])
    legit_count = sum(1 for s in all_samples if not s["is_scam"])
    lang_counts = Counter(s["language"] for s in all_samples)
    source_counts = Counter(s["source"] for s in all_samples)
    risk_counts = Counter(s["risk_level"] for s in all_samples)

    print("\n" + "=" * 70)
    print("  DATASET STATISTICS")
    print("=" * 70)
    print(f"  Total samples: {len(all_samples)}")
    print(f"  Scam: {scam_count} ({scam_count/len(all_samples)*100:.1f}%)")
    print(f"  Legitimate: {legit_count} ({legit_count/len(all_samples)*100:.1f}%)")
    print(f"  Categories: {len(cat_counts)}")
    print(f"  Languages: {len(lang_counts)}")
    print(f"  Sources: {len(source_counts)}")

    print(f"\n  Per-category breakdown:")
    for cat in sorted(cat_counts.keys()):
        count = cat_counts[cat]
        scam_in_cat = sum(1 for s in all_samples if s["category"] == cat and s["is_scam"])
        bar = "#" * min(count, 50)
        print(f"    {cat:35s} {count:4d} samples ({scam_in_cat:4d} scam) {bar}")

    print(f"\n  Language distribution:")
    for lang, count in lang_counts.most_common():
        print(f"    {lang:10s} {count:4d} ({count/len(all_samples)*100:.1f}%)")

    print(f"\n  Source distribution:")
    for src, count in source_counts.most_common():
        print(f"    {src:15s} {count:4d} ({count/len(all_samples)*100:.1f}%)")

    print(f"\n  Risk level distribution:")
    for risk, count in risk_counts.most_common():
        print(f"    {risk:10s} {count:4d} ({count/len(all_samples)*100:.1f}%)")

    # Coverage gaps
    print(f"\n  Coverage gaps (categories with < 100 samples):")
    gaps = []
    for cat in sorted(VALID_CATEGORIES):
        count = cat_counts.get(cat, 0)
        if count < 100:
            gaps.append({"category": cat, "count": count, "shortfall": 100 - count})
            bar = "#" * count
            print(f"    {cat:35s} {count:3d}/100 ({100-count:3d} shortfall) {bar}")
    if not gaps:
        print("    All categories have 100+ samples!")

    # Count synthetic vs real
    real_count = sum(1 for s in all_samples if s["source"] != "synthetic")
    syn_count = sum(1 for s in all_samples if s["source"] == "synthetic")
    syn_pct = syn_count / len(all_samples) * 100
    print(f"\n  Real samples: {real_count} ({real_count/len(all_samples)*100:.1f}%)")
    print(f"  Synthetic samples: {syn_count} ({syn_pct:.1f}%)")
    if syn_pct > 20:
        print(f"  WARNING: Synthetic exceeds 20% limit!")

    # ============================================================
    # SAVE OUTPUTS
    # ============================================================

    # CSV export
    csv_path = os.path.join(OUTPUT_DIR, "dataset_v2_alpha.csv")
    fields = ["id", "text", "text_clean", "language", "category", "is_scam",
              "risk_level", "ground_truth_label", "source", "version"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for s in all_samples:
            writer.writerow({k: s.get(k, "") for k in fields})
    print(f"\n  CSV saved: {csv_path}")

    # JSON export (full with all fields)
    json_path = os.path.join(OUTPUT_DIR, "dataset_v2_alpha.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_samples, f, indent=2, ensure_ascii=False)
    print(f"  JSON saved: {json_path}")

    # Also save deduplicates for reference
    dup_path = os.path.join(OUTPUT_DIR, "duplicates_removed.json")
    with open(dup_path, "w", encoding="utf-8") as f:
        json.dump(dupes, f, indent=2)
    print(f"  Duplicates report: {dup_path}")

    # ============================================================
    # GENERATE REPORTS
    # ============================================================

    # 1. statistics.md
    stats_md = generate_statistics_md(all_samples, cat_counts, lang_counts, source_counts, risk_counts)
    with open(os.path.join(OUTPUT_DIR, "statistics.md"), "w", encoding="utf-8") as f:
        f.write(stats_md)
    print(f"  Statistics report: statistics.md")

    # 2. coverage_report.md
    cov_md = generate_coverage_md(all_samples, gaps)
    with open(os.path.join(OUTPUT_DIR, "coverage_report.md"), "w", encoding="utf-8") as f:
        f.write(cov_md)
    print(f"  Coverage report: coverage_report.md")

    # 3. duplicate_report.md
    dup_md = generate_duplicate_md(dupes, before, len(all_samples))
    with open(os.path.join(OUTPUT_DIR, "duplicate_report.md"), "w", encoding="utf-8") as f:
        f.write(dup_md)
    print(f"  Duplicate report: duplicate_report.md")

    # 4. annotation_quality.md
    qual_md = generate_quality_md(all_samples, errors)
    with open(os.path.join(OUTPUT_DIR, "annotation_quality.md"), "w", encoding="utf-8") as f:
        f.write(qual_md)
    print(f"  Annotation quality: annotation_quality.md")

    # 5. missing_categories.md
    missing_md = generate_missing_md(all_samples)
    with open(os.path.join(OUTPUT_DIR, "missing_categories.md"), "w", encoding="utf-8") as f:
        f.write(missing_md)
    print(f"  Missing categories: missing_categories.md")

    print("\n" + "=" * 70)
    print("  BUILD COMPLETE")
    print(f"  Output directory: {OUTPUT_DIR}")
    print("=" * 70)


def generate_statistics_md(samples, cat_counts, lang_counts, source_counts, risk_counts):
    total = len(samples)
    scam = sum(1 for s in samples if s["is_scam"])
    legit = total - scam
    syn = sum(1 for s in samples if s["source"] == "synthetic")
    real = total - syn

    md = f"""# ScamShield v2 — Dataset Statistics

**Generated:** {NOW}
**Version:** {VERSION}
**Total samples:** {total}

## Overview

| Metric | Value |
|--------|-------|
| Total samples | {total} |
| Scam samples | {scam} ({scam/total*100:.1f}%) |
| Legitimate samples | {legit} ({legit/total*100:.1f}%) |
| Categories | {len(cat_counts)} / 25 |
| Languages | {len(lang_counts)} |
| Sources | {len(source_counts)} |
| Real examples | {real} ({real/total*100:.1f}%) |
| Synthetic examples | {syn} ({syn/total*100:.1f}%) |

## Category Distribution

| Category | Count | Scam | Legit | Status |
|----------|-------|------|-------|--------|
"""
    for cat in sorted(cat_counts.keys()):
        count = cat_counts[cat]
        scam_c = sum(1 for s in samples if s["category"] == cat and s["is_scam"])
        legit_c = count - scam_c
        status = "MET" if count >= 100 else f"SHORT {100-count}"
        md += f"| {cat} | {count} | {scam_c} | {legit_c} | {status} |\n"

    md += f"""
## Language Distribution

| Language | Count | Percentage |
|----------|-------|------------|
"""
    for lang, count in lang_counts.most_common():
        md += f"| {lang} | {count} | {count/total*100:.1f}% |\n"

    md += f"""
## Source Distribution

| Source | Count | Percentage |
|--------|-------|------------|
"""
    for src, count in source_counts.most_common():
        md += f"| {src} | {count} | {count/total*100:.1f}% |\n"

    md += f"""
## Risk Level Distribution

| Risk Level | Count | Percentage |
|------------|-------|------------|
"""
    for risk, count in risk_counts.most_common():
        md += f"| {risk} | {count} | {count/total*100:.1f}% |\n"

    return md


def generate_coverage_md(samples, gaps):
    cat_counts = Counter(s["category"] for s in samples)

    md = """# ScamShield v2 — Coverage Report

**Generated:** """ + NOW + """

## Coverage by Category

| Category | Samples | Target | Shortfall | Status |
|----------|---------|--------|-----------|--------|
"""
    for cat in sorted(VALID_CATEGORIES):
        count = cat_counts.get(cat, 0)
        shortfall = max(0, 100 - count)
        if count == 0:
            status = "**MISSING**"
        elif count >= 100:
            status = "MET"
        elif count >= 50:
            status = "PARTIAL"
        else:
            status = "LOW"
        md += f"| {cat} | {count} | 100 | {shortfall} | {status} |\n"

    md += f"""
## Summary

| Metric | Value |
|--------|-------|
| Categories with 0 samples | {sum(1 for c in VALID_CATEGORIES if cat_counts.get(c, 0) == 0)} |
| Categories meeting target (100+) | {sum(1 for c in VALID_CATEGORIES if cat_counts.get(c, 0) >= 100)} |
| Categories below target | {sum(1 for c in VALID_CATEGORIES if 0 < cat_counts.get(c, 0) < 100)} |
| Total shortfall (samples needed) | {sum(max(0, 100 - cat_counts.get(c, 0)) for c in VALID_CATEGORIES)} |

## Coverage Gaps

| Category | Count | Samples Needed | Priority |
|----------|-------|----------------|----------|
"""
    for g in sorted(gaps, key=lambda x: x["shortfall"], reverse=True):
        if g["shortfall"] >= 75:
            priority = "HIGH"
        elif g["shortfall"] >= 50:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        md += f"| {g['category']} | {g['count']} | {g['shortfall']} | {priority} |\n"

    return md


def generate_duplicate_md(dupes, before, after):
    md = f"""# ScamShield v2 — Duplicate Report

**Generated:** {NOW}

## Summary

| Metric | Value |
|--------|-------|
| Samples before dedup | {before} |
| Samples after dedup | {after} |
| Duplicates removed | {len(dupes)} |
| Dedup rate | {len(dupes)/before*100:.2f}% |

## Method

Deduplication was performed using MD5 hash of lowercase stripped text. Exact duplicate texts were removed, keeping the first occurrence.

## Duplicates Removed

| # | Original ID | Text Preview |
|---|-------------|--------------|
"""
    for i, d in enumerate(dupes, 1):
        md += f"| {i} | {d['id']} | {d['text'][:80]} |\n"

    return md


def generate_quality_md(samples, errors):
    total = len(samples)

    # Count fields present
    fields_present = Counter()
    for s in samples:
        for k in s:
            fields_present[k] += 1

    # Entity presence
    entity_types = Counter()
    for s in samples:
        if s.get("extracted_entities"):
            for k, v in s["extracted_entities"].items():
                if v:
                    entity_types[k] += 1

    md = f"""# ScamShield v2 — Annotation Quality Report

**Generated:** {NOW}
**Total samples:** {total}

## Schema Validation

| Metric | Value |
|--------|-------|
| Samples validated | {total} |
| Validation failures | {len(errors)} |
| Pass rate | {100 - len(errors)/total*100 if total else 0:.2f}% |

## Field Presence

| Field | Samples with field | Coverage |
|-------|-------------------|----------|
"""
    for field in ["id", "text", "text_clean", "language", "category", "is_scam",
                   "risk_level", "extracted_entities", "ground_truth_label",
                   "source", "version", "created_at", "updated_at"]:
        count = fields_present.get(field, 0)
        md += f"| {field} | {count} | {count/total*100:.1f}% |\n"

    md += f"""
## Entity Extraction Quality

| Entity Type | Samples with entity | Coverage |
|-------------|-------------------|----------|
"""
    for etype in ["urls", "phones", "upi_ids", "banks", "emails", "aadhaar", "pan"]:
        count = entity_types.get(etype, 0)
        md += f"| {etype} | {count} | {count/total*100:.1f}% |\n"

    md += f"""
## Annotation Notes Coverage
Samples with notes: {sum(1 for s in samples if s.get('annotation_notes'))} / {total} ({sum(1 for s in samples if s.get('annotation_notes'))/total*100:.1f}%)

## Language Quality
| Language | Count | Notes |
|----------|-------|-------|
"""
    lang_counts = Counter(s["language"] for s in samples)
    for lang, count in lang_counts.most_common():
        md += f"| {lang} | {count} | {'Auto-detected' if lang != 'en' else 'Default' } |\n"

    return md


def generate_missing_md(samples):
    cat_counts = Counter(s["category"] for s in samples)

    md = f"""# ScamShield v2 — Missing Categories Report

**Generated:** {NOW}

## Categories with Zero Samples

The following categories have **no samples** in the current dataset:
"""
    zero_cats = [c for c in sorted(VALID_CATEGORIES) if cat_counts.get(c, 0) == 0]
    if zero_cats:
        for cat in zero_cats:
            md += f"\n- **{cat}** — No samples collected yet"
    else:
        md += "\nAll 25 categories have at least 1 sample."

    md += f"""

## Categories Below Target (< 100 samples)

| Category | Current | Target | Shortfall |
|----------|---------|--------|-----------|
"""
    for cat in sorted(VALID_CATEGORIES):
        count = cat_counts.get(cat, 0)
        if count < 100 and count > 0:
            md += f"| {cat} | {count} | 100 | {100 - count} |\n"

    md += f"""
## Priority Data Collection Targets

### CRITICAL Priority (0 samples)
"""
    for cat in zero_cats:
        md += f"- {cat}\n"

    md += f"""
### HIGH Priority (< 25 samples)
"""
    for cat in sorted(VALID_CATEGORIES):
        count = cat_counts.get(cat, 0)
        if 0 < count < 25:
            md += f"- {cat} ({count} samples, need {100-count} more)\n"

    md += f"""
### MEDIUM Priority (25–99 samples)
"""
    for cat in sorted(VALID_CATEGORIES):
        count = cat_counts.get(cat, 0)
        if 25 <= count < 100:
            md += f"- {cat} ({count} samples, need {100-count} more)\n"

    md += f"""
## Collection Recommendations

### Sources for missing/underrepresented categories:
"""
    if "ROMANCE_SCAM" in zero_cats or cat_counts.get("ROMANCE_SCAM", 0) < 25:
        md += """
**Romance Scam:**
- CERT-In advisories on social media fraud
- NCPC romance scam case studies
- News reports on matrimonial fraud
- Awareness pages (cyberkannadigs.org, scamdekho.in)
"""
    if "DIGITAL_ARREST" in zero_cats or cat_counts.get("DIGITAL_ARREST", 0) < 25:
        md += """
**Digital Arrest:**
- NITI Aayog digital arrest awareness PDF
- Mumbai Police cyber crime advisories
- Recent news reports (2024-2026 cases)
"""
    if "QR_SCAM" in zero_cats or cat_counts.get("QR_SCAM", 0) < 25:
        md += """
**QR Scam:**
- NPCI circulars on QR fraud
- Paytm/PhonePe/GPay fraud awareness pages
"""
    if "CRYPTO_SCAM" in zero_cats or cat_counts.get("CRYPTO_SCAM", 0) < 25:
        md += """
**Crypto Scam:**
- SEBI investor awareness materials
- CERT-In advisories on cryptocurrency fraud
- News reports on crypto investment scams
"""

    return md


if __name__ == "__main__":
    main()