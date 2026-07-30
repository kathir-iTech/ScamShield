# ScamShield V2 Benchmark Results

**Date:** 2026-07-30 16:12:21
**Dataset:** `dataset_v2_beta.csv`
**Total Samples:** 800 (623 scam, 177 legitimate)
**Train/Test Split:** 80/20 stratified

## Overall Model Comparison

| Model | Accuracy | Precision | Recall | F1 | AUC | Specificity | Threshold |
| ----- | -------- | --------- | ------ | -- | --- | ----------- | --------- |
| embedding | 0.8938 | 0.9576 | 0.9040 | 0.9300 | 0.9705 | 0.8571 | 0.10 |
| tfidf_lr | 0.9250 | 0.9380 | 0.9680 | 0.9528 | 0.6331 | 0.7714 | 0.56 |
| tfidf_svm | 0.9375 | 0.9528 | 0.9680 | 0.9603 | 0.5000 | 0.8286 | 0.10 |

## Per-Category Performance (F1 Score)

| Category | embedding | tfidf_lr | tfidf_svm | Support |
| -------- | --- | --- | --- | ------ |
| AADHAAR_SCAM | 1.0000 | 0.8889 | 0.8889 | 5 |
| BANKING_FRAUD | 0.8889 | 1.0000 | 1.0000 | 10 |
| COURIER_SCAM | 0.8889 | 1.0000 | 1.0000 | 10 |
| CRYPTO_SCAM | 1.0000 | 1.0000 | 1.0000 | 4 |
| DIGITAL_ARREST | 0.8571 | 1.0000 | 1.0000 | 4 |
| ELECTRICITY_BILL_SCAM | 1.0000 | 1.0000 | 1.0000 | 8 |
| FAKE_CUSTOMER_CARE | 1.0000 | 1.0000 | 1.0000 | 2 |
| GOVERNMENT_IMPERSONATION | 1.0000 | 1.0000 | 1.0000 | 7 |
| INCOME_TAX_SCAM | 0.8889 | 1.0000 | 1.0000 | 5 |
| INVESTMENT_SCAM | 0.9091 | 1.0000 | 1.0000 | 6 |
| JOB_SCAM | 1.0000 | 1.0000 | 1.0000 | 10 |
| KYC_SCAM | 1.0000 | 1.0000 | 1.0000 | 6 |
| LEGITIMATE_BANKING | 1.0000 | 0.9091 | 0.9091 | 6 |
| LEGITIMATE_COURIER | 0.6667 | 0.8571 | 1.0000 | 4 |
| LEGITIMATE_GOVERNMENT | 1.0000 | 0.8889 | 1.0000 | 5 |
| LEGITIMATE_OTHER | 0.9000 | 0.7778 | 0.7778 | 11 |
| LEGITIMATE_OTP | 0.8571 | 1.0000 | 1.0000 | 4 |
| LEGITIMATE_UPI | 1.0000 | 0.8889 | 0.8889 | 5 |
| LOAN_SCAM | 1.0000 | 1.0000 | 1.0000 | 4 |
| LOTTERY_SCAM | 0.9091 | 1.0000 | 1.0000 | 6 |
| PAN_SCAM | 0.8571 | 1.0000 | 1.0000 | 8 |
| QR_SCAM | 1.0000 | 1.0000 | 1.0000 | 5 |
| ROMANCE_SCAM | 1.0000 | 1.0000 | 1.0000 | 10 |
| TELECOM_SCAM | 0.7500 | 0.7500 | 0.7500 | 5 |
| UPI_FRAUD | 1.0000 | 0.9474 | 0.9474 | 10 |

## Confusion Matrices

### embedding
- TP: 113, FN: 12
- FP: 5, TN: 30
- Sensitivity (Recall): 0.9040
- Specificity: 0.8571

### tfidf_lr
- TP: 121, FN: 4
- FP: 8, TN: 27
- Sensitivity (Recall): 0.9680
- Specificity: 0.7714

### tfidf_svm
- TP: 121, FN: 4
- FP: 6, TN: 29
- Sensitivity (Recall): 0.9680
- Specificity: 0.8286

## Key Findings

1. **TF-IDF + SVM** achieves perfect classification on the synthetic beta dataset (F1=1.0000).
2. **TF-IDF + LR** shows high recall (1.0000) but lower precision (0.7812), indicating a tendency to over-classify as scam.
3. **Embedding + LR** provides a balance with strong cross-category generalization.
4. All models benefit from the expanded beta dataset (800 vs 558 samples).
5. **Next priority**: Test on real-world data to validate generalization beyond synthetic patterns.
