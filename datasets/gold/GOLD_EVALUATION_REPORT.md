# Gold Evaluation Report

**Date:** 2026-07-30
**Model:** TF-IDF + LogisticRegression (production)
**Gold dataset:** `gold_dataset.csv` (308 samples)

## Overall Metrics

| Metric | Value |
|--------|-------|
| Accuracy | 0.8604 |
| Precision | 0.9045 |
| Recall | 0.8824 |
| F1 | 0.8933 |
| MCC | 0.6920 |
| ROC-AUC | 0.9260 |
| FPR | 0.1827 |
| FNR | 0.1176 |
| Specificity | 0.8173 |

## Confusion Matrix

```
            Predicted
             Safe  Scam
Actual Safe    85    19
       Scam    24   180
```

TP=180 FP=19 FN=24 TN=85

## Per-Category Performance

| Category | Samples | F1 (Scam) | F1 (Legit) | Acc | TP | FP | FN | TN |
|----------|---------|-----------|------------|-----|----|----|----|----|
| AADHAAR_SCAM | 3 | 1.0000 | 0.0000 | 1.0000 | 3 | 0 | 0 | 0 |
| BANKING_FRAUD | 14 | 0.9231 | 0.0000 | 0.8571 | 12 | 0 | 2 | 0 |
| COURIER_SCAM | 8 | 1.0000 | 0.0000 | 1.0000 | 8 | 0 | 0 | 0 |
| CRYPTO_SCAM | 6 | 1.0000 | 0.0000 | 1.0000 | 6 | 0 | 0 | 0 |
| DIGITAL_ARREST | 12 | 1.0000 | 0.0000 | 1.0000 | 12 | 0 | 0 | 0 |
| ELECTRICITY_BILL_SCAM | 8 | 1.0000 | 0.0000 | 1.0000 | 8 | 0 | 0 | 0 |
| FAKE_CUSTOMER_CARE | 11 | 0.9524 | 0.0000 | 0.9091 | 10 | 0 | 1 | 0 |
| GOVERNMENT_IMPERSONATION | 9 | 1.0000 | 0.0000 | 1.0000 | 9 | 0 | 0 | 0 |
| INCOME_TAX_SCAM | 8 | 1.0000 | 0.0000 | 1.0000 | 8 | 0 | 0 | 0 |
| INVESTMENT_SCAM | 11 | 1.0000 | 0.0000 | 1.0000 | 11 | 0 | 0 | 0 |
| JOB_SCAM | 11 | 1.0000 | 0.0000 | 1.0000 | 11 | 0 | 0 | 0 |
| KYC_SCAM | 13 | 1.0000 | 0.0000 | 1.0000 | 13 | 0 | 0 | 0 |
| LEGITIMATE_BANKING | 19 | 0.9231 | 0.9600 | 0.9474 | 6 | 1 | 0 | 12 |
| LEGITIMATE_COLLEGE | 8 | 0.0000 | 0.7692 | 0.6250 | 0 | 3 | 0 | 5 |
| LEGITIMATE_COURIER | 9 | 0.0000 | 0.9412 | 0.8889 | 0 | 1 | 0 | 8 |
| LEGITIMATE_GOVERNMENT | 8 | 0.0000 | 1.0000 | 1.0000 | 0 | 0 | 0 | 8 |
| LEGITIMATE_OTP | 8 | 0.0000 | 1.0000 | 1.0000 | 0 | 0 | 0 | 8 |
| LEGITIMATE_PERSONAL | 20 | 0.4286 | 0.6923 | 0.6000 | 3 | 8 | 0 | 9 |
| LEGITIMATE_SHOPPING | 18 | 0.0000 | 0.8000 | 0.6667 | 0 | 0 | 6 | 12 |
| LEGITIMATE_TELECOM | 15 | 0.5000 | 0.6667 | 0.6000 | 3 | 3 | 3 | 6 |
| LEGITIMATE_UPI | 14 | 0.0000 | 0.7826 | 0.6429 | 0 | 2 | 3 | 9 |
| LEGITIMATE_UTILITY | 9 | 0.0000 | 0.9412 | 0.8889 | 0 | 1 | 0 | 8 |
| LOAN_SCAM | 9 | 1.0000 | 0.0000 | 1.0000 | 9 | 0 | 0 | 0 |
| LOTTERY_SCAM | 9 | 1.0000 | 0.0000 | 1.0000 | 9 | 0 | 0 | 0 |
| OTP_SCAM | 8 | 0.5455 | 0.0000 | 0.3750 | 3 | 0 | 5 | 0 |
| PAN_SCAM | 9 | 1.0000 | 0.0000 | 1.0000 | 9 | 0 | 0 | 0 |
| QR_SCAM | 6 | 1.0000 | 0.0000 | 1.0000 | 6 | 0 | 0 | 0 |
| ROMANCE_SCAM | 5 | 1.0000 | 0.0000 | 1.0000 | 5 | 0 | 0 | 0 |
| TELECOM_SCAM | 6 | 1.0000 | 0.0000 | 1.0000 | 6 | 0 | 0 | 0 |
| UPI_FRAUD | 14 | 0.8333 | 0.0000 | 0.7143 | 10 | 0 | 4 | 0 |

## Per-Language Performance

| Language | Samples | Accuracy | F1 |
|----------|---------|----------|----|
| en | 248 | 0.8790 | 0.8986 |
| hi-en | 21 | 0.8095 | 0.8947 |
| ta-en | 20 | 0.8000 | 0.8889 |
| te-en | 19 | 0.7368 | 0.8485 |
