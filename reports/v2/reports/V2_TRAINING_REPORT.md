# V2 Training Report

**Date:** 2026-07-30 14:49:11

## Dataset Overview

**Source:** `datasets/v2/annotated/dataset_v2_alpha.csv`
**Total Samples:** 446
**Scam:** 376
**Legitimate:** 70
**Categories:** 25 (19 scam, 6 legitimate)
**Languages:** en (533), ta-en (19), hi-en (6)
**Duplicates:** 0 | **Label Errors:** 0 | **Missing Values:** 0

## Data Splits

| Split | Samples | Scam | Legit | Scam % |
| ----- | ------: | ---: | ----: | -----: |
| Train | 334 | 282 | 52 | 84.4% |
| Val | 112 | 94 | 18 | 83.9% |
| Test | 112 | 94 | 18 | 83.9% |

## Category Distribution (Full Dataset)

| Category | Count | Type |
| -------- | ----: | ---- |
| BANKING_FRAUD | 78 | Scam |
| LEGITIMATE_OTHER | 50 | Legitimate |
| UPI_FRAUD | 49 | Scam |
| KYC_SCAM | 46 | Scam |
| JOB_SCAM | 44 | Scam |
| COURIER_SCAM | 40 | Scam |
| GOVERNMENT_IMPERSONATION | 37 | Scam |
| LOTTERY_SCAM | 27 | Scam |
| ELECTRICITY_BILL_SCAM | 24 | Scam |
| LOAN_SCAM | 23 | Scam |
| FAKE_CUSTOMER_CARE | 18 | Scam |
| INVESTMENT_SCAM | 18 | Scam |
| AADHAAR_SCAM | 15 | Scam |
| TELECOM_SCAM | 15 | Scam |
| QR_SCAM | 11 | Scam |
| LEGITIMATE_BANKING | 9 | Legitimate |
| LEGITIMATE_GOVERNMENT | 8 | Legitimate |
| ROMANCE_SCAM | 7 | Scam |
| LEGITIMATE_UPI | 7 | Legitimate |
| LEGITIMATE_COURIER | 7 | Legitimate |
| LEGITIMATE_OTP | 7 | Legitimate |
| CRYPTO_SCAM | 7 | Scam |
| DIGITAL_ARREST | 5 | Scam |
| INCOME_TAX_SCAM | 4 | Scam |
| PAN_SCAM | 2 | Scam |

## Training Configuration

- **Random Seed:** 42
- **Cross-Validation:** 5-fold Stratified
- **TF-IDF:** max_features=5000, ngram_range=(1,2), min_df=2, max_df=0.95
- **LR:** class_weight=balanced, C=1.0, max_iter=1000
- **SVM:** class_weight=balanced, C=1.0, max_iter=2000
- **Embedding:** all-MiniLM-L6-v2 + StandardScaler + LR
- **Test Split:** 20% | **Val Split:** 20% (of train)
