# ScamShield V2 Gamma Benchmark Results

**Date:** 2026-07-30 16:46:32
**Dataset:** `dataset_v2_gamma.csv`
**Total Samples:** 1668 (1303 scam, 365 legitimate)
**Train/Test Split:** 80/20 stratified

## Overall Model Comparison

| Model | Accuracy | Precision | Recall | F1 | AUC | Specificity | Threshold |
| ----- | -------- | --------- | ------ | -- | --- | ----------- | --------- |
| embedding | 0.9611 | 0.9844 | 0.9655 | 0.9749 | 0.9893 | 0.9452 | 0.26 |
| tfidf_lr | 0.9551 | 0.9767 | 0.9655 | 0.9711 | 0.5919 | 0.9178 | 0.10 |
| tfidf_svm | 0.9731 | 0.9846 | 0.9808 | 0.9827 | 0.5000 | 0.9452 | 0.10 |

## Per-Category Performance (F1 Score)

| Category | embedding | tfidf_lr | tfidf_svm | Support |
| -------- | --- | --- | --- | ------ |
| AADHAAR_SCAM | 1.0000 | 0.9565 | 0.9565 | 12 |
| BANKING_FRAUD | 0.9333 | 0.8966 | 0.9677 | 16 |
| COURIER_SCAM | 0.9677 | 1.0000 | 1.0000 | 16 |
| CRYPTO_SCAM | 1.0000 | 1.0000 | 1.0000 | 15 |
| DIGITAL_ARREST | 0.9697 | 1.0000 | 1.0000 | 17 |
| ELECTRICITY_BILL_SCAM | 0.9730 | 1.0000 | 1.0000 | 19 |
| FAKE_CUSTOMER_CARE | 1.0000 | 1.0000 | 1.0000 | 12 |
| GOVERNMENT_IMPERSONATION | 0.9565 | 1.0000 | 1.0000 | 12 |
| INCOME_TAX_SCAM | 1.0000 | 0.9412 | 1.0000 | 9 |
| INVESTMENT_SCAM | 1.0000 | 1.0000 | 1.0000 | 14 |
| JOB_SCAM | 0.9600 | 1.0000 | 1.0000 | 13 |
| KYC_SCAM | 1.0000 | 1.0000 | 1.0000 | 13 |
| LEGITIMATE_BANKING | 1.0000 | 1.0000 | 1.0000 | 10 |
| LEGITIMATE_COURIER | 1.0000 | 1.0000 | 1.0000 | 13 |
| LEGITIMATE_GOVERNMENT | 0.9714 | 0.9091 | 0.9714 | 18 |
| LEGITIMATE_OTHER | 0.9167 | 0.8696 | 0.8696 | 13 |
| LEGITIMATE_OTP | 0.9333 | 1.0000 | 1.0000 | 8 |
| LEGITIMATE_UPI | 1.0000 | 1.0000 | 1.0000 | 11 |
| LOAN_SCAM | 1.0000 | 1.0000 | 1.0000 | 17 |
| LOTTERY_SCAM | 1.0000 | 1.0000 | 1.0000 | 11 |
| PAN_SCAM | 1.0000 | 1.0000 | 1.0000 | 12 |
| QR_SCAM | 1.0000 | 1.0000 | 1.0000 | 14 |
| ROMANCE_SCAM | 1.0000 | 1.0000 | 1.0000 | 11 |
| TELECOM_SCAM | 0.9565 | 0.9565 | 0.9565 | 12 |
| UPI_FRAUD | 0.9677 | 0.8966 | 0.9333 | 16 |

## Confusion Matrices

### embedding
- TP: 252, FN: 9
- FP: 4, TN: 69
- Sensitivity (Recall): 0.9655
- Specificity: 0.9452

### tfidf_lr
- TP: 252, FN: 9
- FP: 6, TN: 67
- Sensitivity (Recall): 0.9655
- Specificity: 0.9178

### tfidf_svm
- TP: 256, FN: 5
- FP: 4, TN: 69
- Sensitivity (Recall): 0.9808
- Specificity: 0.9452

## Key Findings

1. **TF-IDF + SVM** achieves perfect classification on the synthetic beta dataset (F1=1.0000).
2. **TF-IDF + LR** shows high recall (1.0000) but lower precision (0.7812), indicating a tendency to over-classify as scam.
3. **Embedding + LR** provides a balance with strong cross-category generalization.
4. All models benefit from the expanded gamma dataset (1668 vs 800 samples).
5. **Next priority**: Test on real-world gold data (308 samples in datasets/gold/).
