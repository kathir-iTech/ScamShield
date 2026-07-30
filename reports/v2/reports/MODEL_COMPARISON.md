# Model Comparison Report

**Date:** 2026-07-30 14:29:50
**Training Data:** `backend/data/scam_dataset.csv` (5,715 samples, 15.5% scam)
**Evaluation Data:** `datasets/v2/annotated/dataset_v2_alpha.csv` (558 samples, 470 scam, 88 legit)
**Seed:** 42

## Overall Metrics Comparison

|       Model        |      Accuracy      |     Precision      |       Recall       |         F1         |        Mcc         | Balanced Accuracy  |      Roc Auc       | False Positive Rate | False Negative Rate |     Train Time     |     Eval Time      |     Throughput     |
| :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: |
| `embedding`        |       0.8423       |       0.8423       |       1.0000       |       0.9144       |       0.0000       |       0.5000       |       0.5458       |       1.0000       |       0.0000       |       482.8s       |      238.647s      |       2.3/s        |
| `tfidf_lr`         |       0.8441       |       0.8475       |       0.9936       |       0.9148       |       0.1279       |       0.5195       |       0.7997       |       0.9545       |       0.0064       |        1.0s        |       1.294s       |      431.2/s       |
| `tfidf_svm`        |       0.8459       |       0.8491       |       0.9936       |       0.9157       |       0.1546       |       0.5252       |       0.7941       |       0.9432       |       0.0064       |        0.5s        |       1.786s       |      312.4/s       |

## Confusion Matrices

|       Model        |    TP    |    FN    |    FP    |    TN    |
| :------------------: | :------: | :------: | :------: | :------: |
| `embedding`        |   470    |    0     |    88    |    0     |
| `tfidf_lr`         |   467    |    3     |    84    |    4     |
| `tfidf_svm`        |   467    |    3     |    83    |    5     |

> **⚠️ Critical Finding:** All models exhibit **~95% false positive rate** because the training data (84.5% safe, old categories) and evaluation data (84.2% scam, 25 modern Indian categories) have **inverted class distributions and different scam vocabularies**. These results measure **cross-dataset generalization**, not absolute production performance. A model retrained on v2 data would perform significantly better.
>
> **`transformer` (DistilBERT):** Could not be evaluated due to PyTorch DLL compatibility issue with Python 3.14. Weights were loaded but `accelerate` integration failed. Requires Python 3.12 or earlier.

## Per-Category Performance (F1 Score)

|      Category      |    `embedding`     |     `tfidf_lr`     |    `tfidf_svm`     |     Best Model     |
| :------------------: | :------------------: | :------------------: | :------------------: | :------------------: |
| AADHAAR_SCAM       |       1.0000       |       1.0000       |       0.9655       |    `embedding`     |
| BANKING_FRAUD      |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| COURIER_SCAM       |       1.0000       |       1.0000       |       0.9873       |    `embedding`     |
| CRYPTO_SCAM        |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| DIGITAL_ARREST     |       1.0000       |       1.0000       |       0.8889       |    `embedding`     |
| ELECTRICITY_BILL_SCAM |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| FAKE_CUSTOMER_CARE |       1.0000       |       0.9714       |       1.0000       |    `embedding`     |
| GOVERNMENT_IMPERSONATION |       1.0000       |       0.9863       |       1.0000       |    `embedding`     |
| INCOME_TAX_SCAM    |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| INVESTMENT_SCAM    |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| JOB_SCAM           |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| KYC_SCAM           |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| LEGITIMATE_BANKING |       0.0000       |       0.0000       |       0.0000       |    `embedding`     |
| LEGITIMATE_COURIER |       0.0000       |       0.0000       |       0.0000       |    `embedding`     |
| LEGITIMATE_GOVERNMENT |       0.0000       |       0.0000       |       0.0000       |    `embedding`     |
| LEGITIMATE_OTHER   |       0.0000       |       0.0000       |       0.0000       |    `embedding`     |
| LEGITIMATE_OTP     |       0.0000       |       0.0000       |       0.0000       |    `embedding`     |
| LEGITIMATE_UPI     |       0.0000       |       0.0000       |       0.0000       |    `embedding`     |
| LOAN_SCAM          |       1.0000       |       0.9778       |       1.0000       |    `embedding`     |
| LOTTERY_SCAM       |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| PAN_SCAM           |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| QR_SCAM            |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| ROMANCE_SCAM       |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| TELECOM_SCAM       |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
| UPI_FRAUD          |       1.0000       |       1.0000       |       1.0000       |    `embedding`     |
