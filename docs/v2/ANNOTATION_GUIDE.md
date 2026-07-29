# ScamShield v2 – Annotation Guide

## Purpose

This guide defines standards for annotating Indian scam and legitimate messages for the ScamShield v2 dataset. Consistent, high-quality annotation is critical for training reliable detection models.

## Annotation Workflow

```
Raw Message → Language Detection → Text Cleaning → Category Assignment
→ Scam/Legit Label → Risk Level → Entity Extraction → Quality Review
```

## 1. Language Detection

Identify the primary language of the message:

| Code | Language | Example |
|------|----------|---------|
| `en` | English | "Your account has been blocked" |
| `hi` | Hindi | "आपका खाता ब्लॉक कर दिया गया है" |
| `ta` | Tamil | "உங்கள் கணக்கு தடுக்கப்பட்டது" |
| `te` | Telugu | "మీ ఖాతా బ్లాక్ చేయబడింది" |
| `kn` | Kannada | "ನಿಮ್ಮ ಖಾತೆಯನ್ನು ನಿರ್ಬಂಧಿಸಲಾಗಿದೆ" |
| `ml` | Malayalam | "നിങ്ങളുടെ അക്കൗണ്ട് ബ്ലോക്ക് ചെയ്തു" |
| `bn` | Bengali | "আপনার অ্যাকাউন্ট ব্লক করা হয়েছে" |
| `mr` | Marathi | "तुमचे खाते ब्लॉक केले आहे" |
| `gu` | Gujarati | "તમારું એકાઉન્ટ બ્લોક કરવામાં આવ્યું છે" |
| `hi-en` | Hinglish | "Aapka account block kar diya gaya hai" |
| `ta-en` | Tanglish | "Unga account block aagirukku" |

When multiple languages are present, use the **dominant** language. For equal mix, use `hi-en` or `ta-en`.

## 2. Text Cleaning

Apply these transformations:

1. **Lowercase** the entire text
2. **Normalize whitespace** (collapse multiple spaces, trim)
3. **Redact PII** — replace with `[PHONE]`, `[EMAIL]`, `[UPI]`, `[URL]`, `[AADHAAR]`, `[PAN]`
   - Phone: `+91-9876543210` → `[PHONE]`
   - Email: `user@example.com` → `[EMAIL]`
   - URL: `https://bit.ly/xyz` → `[URL]`
   - UPI: `user@paytm` → `[UPI]`
   - Aadhaar: `1234 5678 9012` → `[AADHAAR]`
   - PAN: `ABCDE1234F` → `[PAN]`
4. **Do NOT** remove emoji, punctuation (may carry meaning)
5. **Do NOT** expand abbreviations

Store both original (`text`) and cleaned (`text_clean`) versions.

## 3. Category Classification

### Decision Tree for Category Assignment

```
Is the message requesting money/payment/fees?
├── YES → Is there a threat/urgency?
│   ├── YES → Check for specific theme:
│   │   ├── Bank account blocked/suspended → BANKING_FRAUD
│   │   ├── KYC update required → KYC_SCAM
│   │   ├── Aadhaar deactivation → AADHAAR_SCAM
│   │   ├── PAN blocked → PAN_SCAM
│   │   ├── Customs/courier fee → COURIER_SCAM
│   │   ├── Electricity disconnection → ELECTRICITY_BILL_SCAM
│   │   ├── Government scheme/subsidy → GOVERNMENT_IMPERSONATION
│   │   ├── Income tax/IT notice → INCOME_TAX_SCAM
│   │   ├── Digital arrest/police → DIGITAL_ARREST
│   │   ├── SIM block/TRAI → TELECOM_SCAM
│   │   └── Lottery/prize winnings → LOTTERY_SCAM
│   └── NO → Check for specific theme:
│       ├── UPI collect request → UPI_FRAUD
│       ├── QR code payment → QR_SCAM
│       ├── Job registration fee → JOB_SCAM
│       ├── Loan processing fee → LOAN_SCAM
│       ├── Investment/returns → INVESTMENT_SCAM
│       ├── Crypto trading → CRYPTO_SCAM
│       ├── Romance/relationship → ROMANCE_SCAM
│       └── Customer care helpline → FAKE_CUSTOMER_CARE
├── NO → Is this a legitimate transactional message?
│   ├── Bank transaction alert → LEGITIMATE_BANKING
│   ├── UPI payment confirmation → LEGITIMATE_UPI
│   ├── OTP/verification → LEGITIMATE_OTP
│   ├── Courier tracking → LEGITIMATE_COURIER
│   ├── Government notification → LEGITIMATE_GOVERNMENT
│   └── Other harmless message → LEGITIMATE_OTHER
```

## 4. Scam/Legitimate Label

| Label | When |
|-------|------|
| `scam` | Message is fraudulent, deceptive, or part of a social engineering attack |
| `legitimate` | Message is genuine, from a verified source, and non-deceptive |

**Tiebreaker rules:**
- When uncertain, check the URL domain (legit domains like `sbi.co.in` vs `sbi-verify.xyz`)
- When still uncertain, mark as the category but add `annotation_notes: "unclear"` and flag for review
- Do NOT mark promotional/marketing SMS as scam unless they involve upfront payment requests

## 5. Risk Level Assignment

| Level | Criteria |
|-------|----------|
| `CRITICAL` | Immediate financial loss likely. Requests OTP, UPI PIN, or bank details. Threats of arrest/account freeze within hours. |
| `HIGH` | High probability of fraud. Requests processing fees. Uses urgent language. Impersonates authority. |
| `MEDIUM` | Suspicious but not immediately threatening. Prize/lottery claims. Job offers with fees. Investment pitches. |
| `LOW` | Mildly suspicious. Generic spam. No direct money request but unusual sender. |
| `NONE` | Legitimate messages. Verified source. No risk. |

## 6. Entity Extraction

Extract these entities from each message:

| Entity | Regex Pattern | Example |
|--------|--------------|---------|
| `urls` | `https?://[^\s]+` | `https://bit.ly/xyz` |
| `phones` | `\+?\d{10,15}` | `+919876543210` |
| `upi_ids` | `\w+@\w+` | `user@paytm` |
| `banks` | SBI, HDFC, ICICI, Axis, PNB, etc. | `SBI` |
| `emails` | `\w+@\w+\.\w+` | `support@bank.com` |
| `aadhaar` | `\d{4}\s?\d{4}\s?\d{4}` | `1234 5678 9012` |
| `pan` | `[A-Z]{5}\d{4}[A-Z]` | `ABCDE1234F` |

## 7. Source Attribution

| Source Code | Description |
|-------------|-------------|
| `cert_in` | CERT-In advisories and alerts |
| `rbi` | RBI fraud alert database |
| `ncpc` | National Cyber Crime Portal reports |
| `npci` | NPCI circulars and fraud patterns |
| `public_dataset` | Academic or public SMS datasets |
| `synthetic` | AI-generated or template-based (must be reviewed) |
| `manual` | Hand-crafted by domain expert |
| `known_corpus` | Well-known public corpus (UCI, Kaggle, etc.) |

**Synthetic data** must be clearly marked and should not exceed 20% of any category.

## 8. Quality Control

### Inter-Annotator Agreement

A random 10% of samples must be double-annotated. Compute Cohen's κ:

| κ Value | Agreement | Action |
|---------|-----------|--------|
| κ ≥ 0.90 | Excellent | Accept |
| 0.80 ≤ κ < 0.90 | Good | Review disagreements |
| 0.70 ≤ κ < 0.80 | Fair | Retrain annotators |
| κ < 0.70 | Poor | Redo batch |

### Common Pitfalls

1. **Confusing LEGITIMATE_OTP with OTP scam**: Key difference — legitimate OTP texts say "Do NOT share this OTP". Scam OTP texts ask you to share/forward the OTP.
2. **Legitimate banking vs Banking fraud**: Verified short codes (like `SBIBANK`, `HDFCBK`) indicate legitimacy. Unknown numbers with bank logos are suspicious.
3. **Promotional SMS vs Scam**: Promotional SMS with opt-out (like "Reply STOP to unsubscribe") is generally legitimate. Scams rarely provide genuine opt-out.

## 9. Sample Annotations

### Example 1: KYC Scam

```json
{
  "id": "KYC_SCAM_001",
  "text": "Dear Customer, your SBI account will be blocked today. Update KYC immediately: http://bit.ly/kyc-update",
  "text_clean": "dear customer, your sbi account will be blocked today. update kyc immediately: [URL]",
  "language": "en",
  "category": "KYC_SCAM",
  "is_scam": true,
  "risk_level": "CRITICAL",
  "extracted_entities": {
    "urls": ["http://bit.ly/kyc-update"],
    "phones": [],
    "upi_ids": [],
    "banks": ["SBI"],
    "emails": [],
    "aadhaar": [],
    "pan": []
  },
  "ground_truth_label": "scam",
  "source": "synthetic",
  "annotation_notes": "Shortened URL, bank impersonation, urgent threat",
  "version": "2.0.0",
  "created_at": "2026-07-28T00:00:00Z",
  "updated_at": "2026-07-28T00:00:00Z"
}
```

### Example 2: Legitimate OTP

```json
{
  "id": "LEGITIMATE_OTP_001",
  "text": "Your SBI OTP for transaction of Rs 5,000 is 784512. Do not share this OTP with anyone.",
  "text_clean": "your sbi otp for transaction of rs 5,000 is [OTP]. do not share this otp with anyone.",
  "language": "en",
  "category": "LEGITIMATE_OTP",
  "is_scam": false,
  "risk_level": "NONE",
  "extracted_entities": {
    "urls": [],
    "phones": [],
    "upi_ids": [],
    "banks": ["SBI"],
    "emails": [],
    "aadhaar": [],
    "pan": []
  },
  "ground_truth_label": "legitimate",
  "source": "synthetic",
  "annotation_notes": "Standard OTP message with security warning",
  "version": "2.0.0",
  "created_at": "2026-07-28T00:00:00Z",
  "updated_at": "2026-07-28T00:00:00Z"
}
```

### Example 3: Digital Arrest

```json
{
  "id": "DIGITAL_ARREST_001",
  "text": "CBI has issued an arrest warrant against you. Call immediately to avoid arrest: +917890123456",
  "text_clean": "cbi has issued an arrest warrant against you. call immediately to avoid arrest: [PHONE]",
  "language": "en",
  "category": "DIGITAL_ARREST",
  "is_scam": true,
  "risk_level": "CRITICAL",
  "extracted_entities": {
    "urls": [],
    "phones": ["+917890123456"],
    "upi_ids": [],
    "banks": [],
    "emails": [],
    "aadhaar": [],
    "pan": []
  },
  "ground_truth_label": "scam",
  "source": "synthetic",
  "annotation_notes": "Fake CBI notice, no legitimate agency threatens arrest by SMS",
  "version": "2.0.0",
  "created_at": "2026-07-28T00:00:00Z",
  "updated_at": "2026-07-28T00:00:00Z"
}
```