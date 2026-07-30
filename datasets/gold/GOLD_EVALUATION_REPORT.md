# Gold Evaluation Report

**Date:** 2026-07-30
**Model:** TF-IDF + LogisticRegression (production)
**Gold dataset:** `gold_dataset.csv` (308 samples)

## Overall Metrics

| Metric | Value |
|--------|-------|
| Accuracy | 0.9091 |
| Precision | 0.9835 |
| Recall | 0.8775 |
| F1 | 0.9275 |
| MCC | 0.8162 |
| ROC-AUC | 0.9503 |
| FPR | 0.0288 |
| FNR | 0.1225 |
| Specificity | 0.9712 |

## Confusion Matrix

```
            Predicted
             Safe  Scam
Actual Safe   101     3
       Scam    25   179
```

TP=179 FP=3 FN=25 TN=101

## Per-Category Performance

| Category | Samples | F1 (Scam) | F1 (Legit) | Acc | TP | FP | FN | TN |
|----------|---------|-----------|------------|-----|----|----|----|----|
| AADHAAR_SCAM | 3 | 1.0000 | 0.0000 | 1.0000 | 3 | 0 | 0 | 0 |
| BANKING_FRAUD | 14 | 0.9231 | 0.0000 | 0.8571 | 12 | 0 | 2 | 0 |
| COURIER_SCAM | 8 | 1.0000 | 0.0000 | 1.0000 | 8 | 0 | 0 | 0 |
| CRYPTO_SCAM | 6 | 1.0000 | 0.0000 | 1.0000 | 6 | 0 | 0 | 0 |
| DIGITAL_ARREST | 12 | 1.0000 | 0.0000 | 1.0000 | 12 | 0 | 0 | 0 |
| ELECTRICITY_BILL_SCAM | 8 | 1.0000 | 0.0000 | 1.0000 | 8 | 0 | 0 | 0 |
| FAKE_CUSTOMER_CARE | 11 | 0.8421 | 0.0000 | 0.7273 | 8 | 0 | 3 | 0 |
| GOVERNMENT_IMPERSONATION | 9 | 1.0000 | 0.0000 | 1.0000 | 9 | 0 | 0 | 0 |
| INCOME_TAX_SCAM | 8 | 1.0000 | 0.0000 | 1.0000 | 8 | 0 | 0 | 0 |
| INVESTMENT_SCAM | 11 | 1.0000 | 0.0000 | 1.0000 | 11 | 0 | 0 | 0 |
| JOB_SCAM | 11 | 1.0000 | 0.0000 | 1.0000 | 11 | 0 | 0 | 0 |
| KYC_SCAM | 13 | 1.0000 | 0.0000 | 1.0000 | 13 | 0 | 0 | 0 |
| LEGITIMATE_BANKING | 19 | 1.0000 | 1.0000 | 1.0000 | 6 | 0 | 0 | 13 |
| LEGITIMATE_COLLEGE | 8 | 0.0000 | 1.0000 | 1.0000 | 0 | 0 | 0 | 8 |
| LEGITIMATE_COURIER | 9 | 0.0000 | 0.9412 | 0.8889 | 0 | 1 | 0 | 8 |
| LEGITIMATE_GOVERNMENT | 8 | 0.0000 | 1.0000 | 1.0000 | 0 | 0 | 0 | 8 |
| LEGITIMATE_OTP | 8 | 0.0000 | 0.9333 | 0.8750 | 0 | 1 | 0 | 7 |
| LEGITIMATE_PERSONAL | 20 | 0.0000 | 0.9189 | 0.8500 | 0 | 0 | 3 | 17 |
| LEGITIMATE_SHOPPING | 18 | 0.0000 | 0.8000 | 0.6667 | 0 | 0 | 6 | 12 |
| LEGITIMATE_TELECOM | 15 | 0.0000 | 0.7500 | 0.6000 | 0 | 0 | 6 | 9 |
| LEGITIMATE_UPI | 14 | 0.0000 | 0.8333 | 0.7143 | 0 | 1 | 3 | 10 |
| LEGITIMATE_UTILITY | 9 | 0.0000 | 1.0000 | 1.0000 | 0 | 0 | 0 | 9 |
| LOAN_SCAM | 9 | 1.0000 | 0.0000 | 1.0000 | 9 | 0 | 0 | 0 |
| LOTTERY_SCAM | 9 | 1.0000 | 0.0000 | 1.0000 | 9 | 0 | 0 | 0 |
| OTP_SCAM | 8 | 0.9333 | 0.0000 | 0.8750 | 7 | 0 | 1 | 0 |
| PAN_SCAM | 9 | 1.0000 | 0.0000 | 1.0000 | 9 | 0 | 0 | 0 |
| QR_SCAM | 6 | 1.0000 | 0.0000 | 1.0000 | 6 | 0 | 0 | 0 |
| ROMANCE_SCAM | 5 | 1.0000 | 0.0000 | 1.0000 | 5 | 0 | 0 | 0 |
| TELECOM_SCAM | 6 | 1.0000 | 0.0000 | 1.0000 | 6 | 0 | 0 | 0 |
| UPI_FRAUD | 14 | 0.9630 | 0.0000 | 0.9286 | 13 | 0 | 1 | 0 |

## Per-Language Performance

| Language | Samples | Accuracy | F1 |
|----------|---------|----------|----|
| en | 248 | 0.9677 | 0.9720 |
| hi-en | 21 | 0.6667 | 0.8000 |
| ta-en | 20 | 0.7000 | 0.8235 |
| te-en | 19 | 0.6316 | 0.7742 |
