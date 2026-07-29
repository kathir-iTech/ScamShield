# ScamShield v2 – Indian Scam Intelligence Dataset

## Overview

The ScamShield v2 dataset is a curated collection of **5,000–10,000 labelled messages** spanning **25 categories** of Indian scam and legitimate communications. It replaces the v1 dataset (UCI SMS Spam 2005–2012, UK-centric) with a modern, India-focused corpus designed for production-grade scam detection.

## Dataset Statistics (Target)

| Metric | Target |
|--------|--------|
| Total samples | 5,000–10,000 |
| Scam categories | 19 |
| Legitimate categories | 6 |
| Minimum per category | 100 |
| Languages | English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Hinglish, Tanglish |
| Sources | CERT-In, RBI, NPCI, NCPC, academic, synthetic |

## Category Taxonomy

### Scam Categories (19)

| ID | Category | Examples |
|----|----------|---------|
| `UPI_FRAUD` | UPI Fraud | Fake UPI collect requests, UPI PIN reset, GPay/PhonePe impersonation |
| `BANKING_FRAUD` | Banking Fraud | Account blocked, debit card deactivated, fake bank alerts |
| `KYC_SCAM` | KYC Scam | KYC update requests, account suspension threats |
| `AADHAAR_SCAM` | Aadhaar Scam | Aadhaar deactivation, Aadhaar-PAN linking, fake UIDAI |
| `PAN_SCAM` | PAN Scam | PAN card blocked, income tax notice, fake IT department |
| `FAKE_CUSTOMER_CARE` | Fake Customer Care | Fake helpline numbers, refund/cancellation scams |
| `COURIER_SCAM` | Courier Scam | Customs clearance fees, package detention, fake courier alerts |
| `ELECTRICITY_BILL_SCAM` | Electricity Bill Scam | Disconnection threats, fake bill payment links |
| `QR_SCAM` | QR Scam | Fake QR code payments, scan-and-pay fraud |
| `LOTTERY_SCAM` | Lottery Scam | KBC winner, iPhone lottery, fake prize money |
| `INVESTMENT_SCAM` | Investment Scam | Get-rich-quick, stock tips, mutual fund fraud |
| `CRYPTO_SCAM` | Crypto Scam | Bitcoin investment, crypto trading, NFT fraud |
| `LOAN_SCAM` | Loan Scam | Instant loan approval, pre-approved loan, processing fee fraud |
| `JOB_SCAM` | Job Scam | Work-from-home, data entry, registration fee fraud |
| `ROMANCE_SCAM` | Romance Scam | US Army/NATO soldier, foreign lover, visa fee requests |
| `GOVERNMENT_IMPERSONATION` | Government Impersonation | PM Kisan, NREGA, Ayushman Bharat, government subsidy |
| `DIGITAL_ARREST` | Digital Arrest | Fake police/CBI notices, cyber crime threats, arrest warrant |
| `INCOME_TAX_SCAM` | Income Tax Scam | Tax evasion notice, refund processing, IT raid threats |
| `TELECOM_SCAM` | Telecom Scam | SIM card blocked, TRAI warning, fake call drops |

### Legitimate Categories (6)

| ID | Category | Examples |
|----|----------|---------|
| `LEGITIMATE_BANKING` | Legitimate Banking | Transaction alerts, bill payments, account credits |
| `LEGITIMATE_UPI` | Legitimate UPI | Money received, UPI payment confirmations |
| `LEGITIMATE_OTP` | Legitimate OTP | OTP for transactions, verification codes |
| `LEGITIMATE_COURIER` | Legitimate Courier | Delivery updates, tracking links (legit domains) |
| `LEGITIMATE_GOVERNMENT` | Legitimate Government | Genuine scheme updates, tax refunds, official notices |
| `LEGITIMATE_OTHER` | Other Legitimate | Appointments, order confirmations, promotional SMS |

## Dataset Schema

Each sample is a JSON object with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier (e.g., `UPI_FRAUD_001`) |
| `text` | string | yes | Original message verbatim |
| `text_clean` | string | yes | Cleaned/normalized message |
| `language` | string | yes | Language code |
| `category` | string | yes | Category from taxonomy |
| `is_scam` | boolean | yes | `true` for scam, `false` for legitimate |
| `risk_level` | string | yes | `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` / `NONE` |
| `extracted_entities` | object | yes | Dict with `urls`, `phones`, `upi_ids`, `banks`, `emails`, `aadhaar`, `pan` |
| `ground_truth_label` | string | yes | `scam` or `legitimate` |
| `source` | string | yes | Origin of the sample |
| `annotation_notes` | string | no | Notes from annotator |
| `annotator_id` | string | no | Annotator identifier |
| `version` | string | yes | Dataset version (e.g., `2.0.0`) |
| `created_at` | string | yes | ISO 8601 timestamp |
| `updated_at` | string | yes | ISO 8601 timestamp |

## Folder Structure

```
datasets/v2/
├── raw/                          # Unprocessed data from sources
│   ├── cert_in/                  # CERT-In advisories
│   ├── rbi/                      # RBI fraud alerts
│   ├── npci/                     # NPCI circulars
│   ├── ncpc/                     # National Cyber Crime Portal
│   ├── public_datasets/          # Academic/public datasets
│   └── synthetic/                # AI-generated templates
├── annotated/                    # Final labelled datasets
│   ├── v2.0.0/                   # Versioned releases
│   │   ├── dataset.json          # Full dataset
│   │   ├── dataset.csv           # CSV export
│   │   ├── train.json            # Training split
│   │   ├── test.json             # Test split
│   │   └── validation.json       # Validation split
│   └── latest -> v2.0.0          # Symlink to latest
├── benchmark/                    # Evaluation benchmark
│   ├── benchmark_v2.json         # Curated benchmark samples
│   └── categories/               # Per-category benchmark files
├── scripts/                      # Dataset utilities
│   ├── build_dataset.py          # Build from raw sources
│   ├── augment.py                # Data augmentation
│   ├── clean.py                  # Text cleaning pipeline
│   └── validate.py               # Schema validation
└── README.md                     # This file
```

## Versioning Strategy

| Version | Status | Date | Samples | Notes |
|---------|--------|------|---------|-------|
| v2.0.0-alpha | In progress | 2026-Q3 | 0 / 5000 | Seed dataset |
| v2.0.0-beta | Planned | 2026-Q4 | 2000 / 5000 | First review |
| v2.0.0-rc1 | Planned | 2027-Q1 | 3500 / 5000 | Coverage audit |
| v2.0.0 | Planned | 2027-Q2 | 5000+ | Production release |

Version format: `v<major>.<minor>.<patch>[-<pre-release>]`

- **Major**: Breaking schema changes
- **Minor**: New categories, significant size increase
- **Patch**: Bug fixes, additional samples within existing categories

## Quality Gates

1. **Deduplication**: No duplicate texts within or across categories
2. **Label consistency**: Random 10% audit by second annotator (κ ≥ 0.90)
3. **Coverage**: Each category ≥ 100 samples
4. **Balance**: Scam/legitimate ratio not worse than 80:20
5. **Language**: At least 10% non-English or code-mixed samples
6. **Temporal**: Samples represent 2023–2026 scam patterns