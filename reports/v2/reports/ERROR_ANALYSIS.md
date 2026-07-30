# Error Analysis Report

**Date:** 2026-07-30 14:29:50

## Overview

| Model | Correct | Incorrect | Accuracy | FP | FN | FNR | FPR |
| ----- | ------: | --------: | -------: | -: | -: | --: | --: |
| `embedding` | 470 | 88 | 84.23% | 88 | 0 | 0.00% | 100.00% |
| `tfidf_lr` | 471 | 87 | 84.41% | 84 | 3 | 0.64% | 95.45% |
| `tfidf_svm` | 472 | 86 | 84.59% | 83 | 3 | 0.64% | 94.32% |

## False Positive Analysis (Safe → Flagged as Scam)

### Model: `embedding` — 88 False Positives

- **Avg Confidence:** 0.9402
- **Top Categories:** LEGITIMATE_OTHER(50), LEGITIMATE_BANKING(9), LEGITIMATE_GOVERNMENT(8), LEGITIMATE_COURIER(7), LEGITIMATE_OTP(7)
- **Languages:** unknown(88)

### Model: `tfidf_lr` — 84 False Positives

- **Avg Confidence:** 0.6659
- **Top Categories:** LEGITIMATE_OTHER(47), LEGITIMATE_BANKING(9), LEGITIMATE_GOVERNMENT(8), LEGITIMATE_OTP(7), LEGITIMATE_UPI(7)
- **Languages:** unknown(84)

### Model: `tfidf_svm` — 83 False Positives

- **Avg Confidence:** 0.4057
- **Top Categories:** LEGITIMATE_OTHER(48), LEGITIMATE_BANKING(8), LEGITIMATE_COURIER(7), LEGITIMATE_GOVERNMENT(7), LEGITIMATE_OTP(7)
- **Languages:** unknown(83)

## False Negative Analysis (Scam → Flagged as Safe)

### Model: `embedding` — 0 False Negatives

No false negatives.

### Model: `tfidf_lr` — 3 False Negatives

- **Avg Confidence:** 0.5056
- **Top Categories:** FAKE_CUSTOMER_CARE(1), GOVERNMENT_IMPERSONATION(1), LOAN_SCAM(1)

### Model: `tfidf_svm` — 3 False Negatives

- **Avg Confidence:** 0.0124
- **Top Categories:** AADHAAR_SCAM(1), COURIER_SCAM(1), DIGITAL_ARREST(1)

## Ambiguous Predictions (Confidence near 0.5)

- **`embedding`:** 11 samples
- **`tfidf_lr`:** 88 samples
- **`tfidf_svm`:** 70 samples

## Category Confusion Analysis

See per-category F1 breakdown below for models that struggle with specific categories.

| Category | Samples | `embedding` F1 | `tfidf_lr` F1 | `tfidf_svm` F1 | Issue? |
| -------- | ------: | -------: | -------: | -------: | ----- |
| AADHAAR_SCAM | 15 | 1.0000 | 1.0000 | 0.9655 | ✅ Generally OK |
| BANKING_FRAUD | 78 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| COURIER_SCAM | 40 | 1.0000 | 1.0000 | 0.9873 | ✅ Generally OK |
| CRYPTO_SCAM | 7 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| DIGITAL_ARREST | 5 | 1.0000 | 1.0000 | 0.8889 | ✅ Generally OK |
| ELECTRICITY_BILL_SCAM | 24 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| FAKE_CUSTOMER_CARE | 18 | 1.0000 | 0.9714 | 1.0000 | ✅ Generally OK |
| GOVERNMENT_IMPERSONATION | 37 | 1.0000 | 0.9863 | 1.0000 | ✅ Generally OK |
| INCOME_TAX_SCAM | 4 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| INVESTMENT_SCAM | 18 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| JOB_SCAM | 44 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| KYC_SCAM | 46 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| LEGITIMATE_BANKING | 9 | 0.0000 | 0.0000 | 0.0000 | ⚠️ All models struggle |
| LEGITIMATE_COURIER | 7 | 0.0000 | 0.0000 | 0.0000 | ⚠️ All models struggle |
| LEGITIMATE_GOVERNMENT | 8 | 0.0000 | 0.0000 | 0.0000 | ⚠️ All models struggle |
| LEGITIMATE_OTHER | 50 | 0.0000 | 0.0000 | 0.0000 | ⚠️ All models struggle |
| LEGITIMATE_OTP | 7 | 0.0000 | 0.0000 | 0.0000 | ⚠️ All models struggle |
| LEGITIMATE_UPI | 7 | 0.0000 | 0.0000 | 0.0000 | ⚠️ All models struggle |
| LOAN_SCAM | 23 | 1.0000 | 0.9778 | 1.0000 | ✅ Generally OK |
| LOTTERY_SCAM | 27 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| PAN_SCAM | 2 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| QR_SCAM | 11 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| ROMANCE_SCAM | 7 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| TELECOM_SCAM | 15 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
| UPI_FRAUD | 49 | 1.0000 | 1.0000 | 1.0000 | ✅ Generally OK |
