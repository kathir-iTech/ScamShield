# Benchmark Results

**Date:** 2026-07-30 14:29:50

## Dataset Summary

| Property | Value |
| -------- | ----- |
| Training Samples | 5,715 |
| Training Scam | 888 (15.5%) |
| Training Safe | 4,827 (84.5%) |
| Evaluation Samples | 558 |
| Evaluation Scam | 470 (84.2%) |
| Evaluation Safe | 88 (15.8%) |
| Evaluation Categories | 25 (19 scam, 6 legit) |

> **Note:** `transformer` (DistilBERT) could not be evaluated due to PyTorch DLL incompatibility with Python 3.14. All other models ran successfully.

## Model: `embedding`

- **Training Time:** 482.83s
- **Inference Time:** 238.6465s (2.34 samples/sec)
- **Optimal Threshold:** 0.0100 (max f1: 0.9144)

### Overall Metrics

| Metric | Value |
| ------ | ----- |
| Accuracy | 0.8423 |
| Precision | 0.8423 |
| Recall | 1.0000 |
| F1 | 0.9144 |
| Mcc | 0.0000 |
| Balanced Accuracy | 0.5000 |
| Roc Auc | 0.5458 |
| Specificity | 0.0000 |
| False Positive Rate | 1.0000 |
| False Negative Rate | 0.0000 |

### Confusion Matrix

| | Predicted Safe | Predicted Scam |
| - | -------------- | -------------- |
| **Actual Safe** | 0 | 88 |
| **Actual Scam** | 0 | 470 |

### Calibration (ECE)
- **Expected Calibration Error:** 0.1346

| Bin | Confidence | Accuracy | Count | Gap |
| --- | ---------- | -------- | ----- | --- |
| [0.00, 0.10) | 0.0000 | 0.0000 | 0 | 0.0000 |
| [0.10, 0.20) | 0.0000 | 0.0000 | 0 | 0.0000 |
| [0.20, 0.30) | 0.0000 | 0.0000 | 0 | 0.0000 |
| [0.30, 0.40) | 0.0000 | 0.0000 | 0 | 0.0000 |
| [0.40, 0.50) | 0.0000 | 0.0000 | 0 | 0.0000 |
| [0.50, 0.60) | 0.5460 | 0.8182 | 11 | 0.2722 |
| [0.60, 0.70) | 0.6407 | 0.6250 | 16 | 0.0157 |
| [0.70, 0.80) | 0.7523 | 0.8571 | 14 | 0.1049 |
| [0.80, 0.90) | 0.8557 | 0.7241 | 29 | 0.1316 |
| [0.90, 1.00) | 0.9930 | 0.8566 | 488 | 0.1365 |

### Error Summary
- **Correct:** 470 (84.23%)
- **Incorrect:** 88 (15.77%)
- **False Positives:** 88
- **False Negatives:** 0
- **Ambiguous:** 11

### Per-Category F1 Scores

| Category | Samples | F1 | Precision | Recall |
| -------- | ------: | --: | --------: | -----: |
| AADHAAR_SCAM | 15 | 1.0000 | 1.0000 | 1.0000 |
| BANKING_FRAUD | 78 | 1.0000 | 1.0000 | 1.0000 |
| COURIER_SCAM | 40 | 1.0000 | 1.0000 | 1.0000 |
| CRYPTO_SCAM | 7 | 1.0000 | 1.0000 | 1.0000 |
| DIGITAL_ARREST | 5 | 1.0000 | 1.0000 | 1.0000 |
| ELECTRICITY_BILL_SCAM | 24 | 1.0000 | 1.0000 | 1.0000 |
| FAKE_CUSTOMER_CARE | 18 | 1.0000 | 1.0000 | 1.0000 |
| GOVERNMENT_IMPERSONATION | 37 | 1.0000 | 1.0000 | 1.0000 |
| INCOME_TAX_SCAM | 4 | 1.0000 | 1.0000 | 1.0000 |
| INVESTMENT_SCAM | 18 | 1.0000 | 1.0000 | 1.0000 |
| JOB_SCAM | 44 | 1.0000 | 1.0000 | 1.0000 |
| KYC_SCAM | 46 | 1.0000 | 1.0000 | 1.0000 |
| LEGITIMATE_BANKING | 9 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_COURIER | 7 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_GOVERNMENT | 8 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_OTHER | 50 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_OTP | 7 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_UPI | 7 | 0.0000 | 0.0000 | 0.0000 |
| LOAN_SCAM | 23 | 1.0000 | 1.0000 | 1.0000 |
| LOTTERY_SCAM | 27 | 1.0000 | 1.0000 | 1.0000 |
| PAN_SCAM | 2 | 1.0000 | 1.0000 | 1.0000 |
| QR_SCAM | 11 | 1.0000 | 1.0000 | 1.0000 |
| ROMANCE_SCAM | 7 | 1.0000 | 1.0000 | 1.0000 |
| TELECOM_SCAM | 15 | 1.0000 | 1.0000 | 1.0000 |
| UPI_FRAUD | 49 | 1.0000 | 1.0000 | 1.0000 |

---

## Model: `tfidf_lr`

- **Training Time:** 0.99s
- **Inference Time:** 1.2939s (431.24 samples/sec)
- **Optimal Threshold:** 0.5100 (max f1: 0.9148)

### Overall Metrics

| Metric | Value |
| ------ | ----- |
| Accuracy | 0.8441 |
| Precision | 0.8475 |
| Recall | 0.9936 |
| F1 | 0.9148 |
| Mcc | 0.1279 |
| Balanced Accuracy | 0.5195 |
| Roc Auc | 0.7997 |
| Specificity | 0.0455 |
| False Positive Rate | 0.9545 |
| False Negative Rate | 0.0064 |

### Confusion Matrix

| | Predicted Safe | Predicted Scam |
| - | -------------- | -------------- |
| **Actual Safe** | 4 | 84 |
| **Actual Scam** | 3 | 467 |

### Calibration (ECE)
- **Expected Calibration Error:** 0.0631

| Bin | Confidence | Accuracy | Count | Gap |
| --- | ---------- | -------- | ----- | --- |
| [0.00, 0.10) | 0.0000 | 0.0000 | 0 | 0.0000 |
| [0.10, 0.20) | 0.0000 | 0.0000 | 0 | 0.0000 |
| [0.20, 0.30) | 0.0000 | 0.0000 | 0 | 0.0000 |
| [0.30, 0.40) | 0.0000 | 0.0000 | 0 | 0.0000 |
| [0.40, 0.50) | 0.0000 | 0.0000 | 0 | 0.0000 |
| [0.50, 0.60) | 0.5563 | 0.6477 | 88 | 0.0914 |
| [0.60, 0.70) | 0.6545 | 0.6750 | 80 | 0.0205 |
| [0.70, 0.80) | 0.7529 | 0.7890 | 109 | 0.0361 |
| [0.80, 0.90) | 0.8540 | 0.9448 | 145 | 0.0908 |
| [0.90, 1.00) | 0.9382 | 1.0000 | 136 | 0.0618 |

### Error Summary
- **Correct:** 471 (84.41%)
- **Incorrect:** 87 (15.59%)
- **False Positives:** 84
- **False Negatives:** 3
- **Ambiguous:** 88

### Per-Category F1 Scores

| Category | Samples | F1 | Precision | Recall |
| -------- | ------: | --: | --------: | -----: |
| AADHAAR_SCAM | 15 | 1.0000 | 1.0000 | 1.0000 |
| BANKING_FRAUD | 78 | 1.0000 | 1.0000 | 1.0000 |
| COURIER_SCAM | 40 | 1.0000 | 1.0000 | 1.0000 |
| CRYPTO_SCAM | 7 | 1.0000 | 1.0000 | 1.0000 |
| DIGITAL_ARREST | 5 | 1.0000 | 1.0000 | 1.0000 |
| ELECTRICITY_BILL_SCAM | 24 | 1.0000 | 1.0000 | 1.0000 |
| FAKE_CUSTOMER_CARE | 18 | 0.9714 | 1.0000 | 0.9444 |
| GOVERNMENT_IMPERSONATION | 37 | 0.9863 | 1.0000 | 0.9730 |
| INCOME_TAX_SCAM | 4 | 1.0000 | 1.0000 | 1.0000 |
| INVESTMENT_SCAM | 18 | 1.0000 | 1.0000 | 1.0000 |
| JOB_SCAM | 44 | 1.0000 | 1.0000 | 1.0000 |
| KYC_SCAM | 46 | 1.0000 | 1.0000 | 1.0000 |
| LEGITIMATE_BANKING | 9 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_COURIER | 7 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_GOVERNMENT | 8 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_OTHER | 50 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_OTP | 7 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_UPI | 7 | 0.0000 | 0.0000 | 0.0000 |
| LOAN_SCAM | 23 | 0.9778 | 1.0000 | 0.9565 |
| LOTTERY_SCAM | 27 | 1.0000 | 1.0000 | 1.0000 |
| PAN_SCAM | 2 | 1.0000 | 1.0000 | 1.0000 |
| QR_SCAM | 11 | 1.0000 | 1.0000 | 1.0000 |
| ROMANCE_SCAM | 7 | 1.0000 | 1.0000 | 1.0000 |
| TELECOM_SCAM | 15 | 1.0000 | 1.0000 | 1.0000 |
| UPI_FRAUD | 49 | 1.0000 | 1.0000 | 1.0000 |

---

## Model: `tfidf_svm`

- **Training Time:** 0.53s
- **Inference Time:** 1.786s (312.43 samples/sec)
- **Optimal Threshold:** 0.0300 (max f1: 0.9157)

### Overall Metrics

| Metric | Value |
| ------ | ----- |
| Accuracy | 0.8459 |
| Precision | 0.8491 |
| Recall | 0.9936 |
| F1 | 0.9157 |
| Mcc | 0.1546 |
| Balanced Accuracy | 0.5252 |
| Roc Auc | 0.7941 |
| Specificity | 0.0568 |
| False Positive Rate | 0.9432 |
| False Negative Rate | 0.0064 |

### Confusion Matrix

| | Predicted Safe | Predicted Scam |
| - | -------------- | -------------- |
| **Actual Safe** | 5 | 83 |
| **Actual Scam** | 3 | 467 |

### Calibration (ECE)
- **Expected Calibration Error:** 0.2807

| Bin | Confidence | Accuracy | Count | Gap |
| --- | ---------- | -------- | ----- | --- |
| [0.00, 0.10) | 0.0534 | 0.5938 | 32 | 0.5404 |
| [0.10, 0.20) | 0.1518 | 0.5778 | 45 | 0.4259 |
| [0.20, 0.30) | 0.2470 | 0.7368 | 38 | 0.4898 |
| [0.30, 0.40) | 0.3441 | 0.8286 | 35 | 0.4845 |
| [0.40, 0.50) | 0.4516 | 0.7297 | 37 | 0.2781 |
| [0.50, 0.60) | 0.5557 | 0.6667 | 33 | 0.1110 |
| [0.60, 0.70) | 0.6504 | 0.8000 | 30 | 0.1496 |
| [0.70, 0.80) | 0.7515 | 0.8108 | 37 | 0.0593 |
| [0.80, 0.90) | 0.8609 | 0.9773 | 44 | 0.1164 |
| [0.90, 1.00) | 1.2371 | 0.9780 | 227 | 0.2592 |

### Error Summary
- **Correct:** 472 (84.59%)
- **Incorrect:** 86 (15.41%)
- **False Positives:** 83
- **False Negatives:** 3
- **Ambiguous:** 70

### Per-Category F1 Scores

| Category | Samples | F1 | Precision | Recall |
| -------- | ------: | --: | --------: | -----: |
| AADHAAR_SCAM | 15 | 0.9655 | 1.0000 | 0.9333 |
| BANKING_FRAUD | 78 | 1.0000 | 1.0000 | 1.0000 |
| COURIER_SCAM | 40 | 0.9873 | 1.0000 | 0.9750 |
| CRYPTO_SCAM | 7 | 1.0000 | 1.0000 | 1.0000 |
| DIGITAL_ARREST | 5 | 0.8889 | 1.0000 | 0.8000 |
| ELECTRICITY_BILL_SCAM | 24 | 1.0000 | 1.0000 | 1.0000 |
| FAKE_CUSTOMER_CARE | 18 | 1.0000 | 1.0000 | 1.0000 |
| GOVERNMENT_IMPERSONATION | 37 | 1.0000 | 1.0000 | 1.0000 |
| INCOME_TAX_SCAM | 4 | 1.0000 | 1.0000 | 1.0000 |
| INVESTMENT_SCAM | 18 | 1.0000 | 1.0000 | 1.0000 |
| JOB_SCAM | 44 | 1.0000 | 1.0000 | 1.0000 |
| KYC_SCAM | 46 | 1.0000 | 1.0000 | 1.0000 |
| LEGITIMATE_BANKING | 9 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_COURIER | 7 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_GOVERNMENT | 8 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_OTHER | 50 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_OTP | 7 | 0.0000 | 0.0000 | 0.0000 |
| LEGITIMATE_UPI | 7 | 0.0000 | 0.0000 | 0.0000 |
| LOAN_SCAM | 23 | 1.0000 | 1.0000 | 1.0000 |
| LOTTERY_SCAM | 27 | 1.0000 | 1.0000 | 1.0000 |
| PAN_SCAM | 2 | 1.0000 | 1.0000 | 1.0000 |
| QR_SCAM | 11 | 1.0000 | 1.0000 | 1.0000 |
| ROMANCE_SCAM | 7 | 1.0000 | 1.0000 | 1.0000 |
| TELECOM_SCAM | 15 | 1.0000 | 1.0000 | 1.0000 |
| UPI_FRAUD | 49 | 1.0000 | 1.0000 | 1.0000 |

---
