# V2 Benchmark Results

**Date:** 2026-07-30 14:49:11
**Dataset:** `dataset_v2_alpha.csv` (558 samples, 470 scam, 88 legit)
**Test Set:** 112 samples

## Model Comparison

|       Model        |      Accuracy      |     Precision      |       Recall       |         F1         |        Mcc         | Balanced Accuracy  |      Roc Auc       | False Positive Rate | False Negative Rate |     Train Time     |     Inference      |     Throughput     |
| :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: | :------------------: |
| `embedding`        |       0.9554       |       0.9785       |       0.9681       |       0.9733       |       0.8386       |       0.9285       |       0.9379       |       0.1111       |       0.0319       |       317.4s       |      317.422s      |        0/s         |
| `tfidf_lr`         |       0.9375       |       0.9579       |       0.9681       |       0.9630       |       0.7634       |       0.8729       |       0.9716       |       0.2222       |       0.0319       |        0.6s        |       0.637s       |       176/s        |
| `tfidf_svm`        |       0.9554       |       0.9588       |       0.9894       |       0.9738       |       0.8273       |       0.8836       |       0.9657       |       0.2222       |       0.0106       |        0.6s        |       0.644s       |       174/s        |

## Cross-Validation Results (5-Fold Stratified F1)

| Model | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Mean | Std |
| ----- | -----: | -----: | -----: | -----: | -----: | ---: | --: |
| `embedding` | 0.9682 | 0.9530 | 0.9673 | 0.9669 | 0.9530 | **0.9617** | 0.0071 |
| `tfidf_lr` | 0.9740 | 0.9804 | 0.9801 | 0.9467 | 0.9669 | **0.9696** | 0.0125 |
| `tfidf_svm` | 0.9740 | 0.9677 | 0.9737 | 0.9804 | 0.9536 | **0.9699** | 0.0091 |

## Confusion Matrices

|       Model        |   TP   |   FN   |   FP   |   TN   |
| :------------------: | :----: | :----: | :----: | :----: |
| `embedding`        |   91   |   3    |   2    |   16   |
| `tfidf_lr`         |   91   |   3    |   4    |   14   |
| `tfidf_svm`        |   93   |   1    |   4    |   14   |

## Per-Category F1 Scores

|     Category     |     Samples      |  `embedding` F1  |  `tfidf_lr` F1   |  `tfidf_svm` F1  | `embedding` Recall | `tfidf_lr` Recall | `tfidf_svm` Recall |
| :----------------: | :----------------: | :----------------: | :----------------: | :----------------: | :----------------: | :----------------: | :----------------: |
| AADHAAR_SCAM     |        4         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| BANKING_FRAUD    |        17        |      0.9697      |      1.0000      |      1.0000      |      0.9412      |      1.0000      |      1.0000      |
| COURIER_SCAM     |        7         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| CRYPTO_SCAM      |        4         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| DIGITAL_ARREST   |        1         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| ELECTRICITY_BILL_SCAM |        3         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| FAKE_CUSTOMER_CARE |        5         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| GOVERNMENT_IMPERSONATION |        7         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| INCOME_TAX_SCAM  |        1         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| INVESTMENT_SCAM  |        4         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| JOB_SCAM         |        9         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| KYC_SCAM         |        5         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| LEGITIMATE_BANKING |        2         |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |
| LEGITIMATE_COURIER |        1         |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |
| LEGITIMATE_GOVERNMENT |        3         |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |
| LEGITIMATE_OTHER |        8         |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |
| LEGITIMATE_OTP   |        2         |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |
| LEGITIMATE_UPI   |        2         |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |      0.0000      |
| LOAN_SCAM        |        7         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| LOTTERY_SCAM     |        3         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| PAN_SCAM         |        1         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| QR_SCAM          |        4         |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |      1.0000      |
| TELECOM_SCAM     |        4         |      0.6667      |      0.6667      |      1.0000      |      0.5000      |      0.5000      |      1.0000      |
| UPI_FRAUD        |        8         |      1.0000      |      0.9333      |      0.9333      |      1.0000      |      0.8750      |      0.8750      |

## Per-Model Detailed Results

### `embedding`

- **CV F1:** 0.9617 ± 0.0071
- **Train Time:** 317.4s | **Inference:** 317.4221s (0/s)
- **Metrics:**
  - Accuracy: 0.9554
  - Precision: 0.9785
  - Recall: 0.9681
  - F1: 0.9733
  - Mcc: 0.8386
  - Balanced Accuracy: 0.9285
  - Roc Auc: 0.9379
  - False Positive Rate: 0.1111
  - False Negative Rate: 0.0319

#### Confusion Matrix
| | Pred Safe | Pred Scam |
| - | --------: | --------: |
| **Actual Safe** | 16 | 2 |
| **Actual Scam** | 3 | 91 |

### `tfidf_lr`

- **CV F1:** 0.9696 ± 0.0125
- **Train Time:** 0.6s | **Inference:** 0.6371s (176/s)
- **Metrics:**
  - Accuracy: 0.9375
  - Precision: 0.9579
  - Recall: 0.9681
  - F1: 0.9630
  - Mcc: 0.7634
  - Balanced Accuracy: 0.8729
  - Roc Auc: 0.9716
  - False Positive Rate: 0.2222
  - False Negative Rate: 0.0319

#### Confusion Matrix
| | Pred Safe | Pred Scam |
| - | --------: | --------: |
| **Actual Safe** | 14 | 4 |
| **Actual Scam** | 3 | 91 |

### `tfidf_svm`

- **CV F1:** 0.9699 ± 0.0091
- **Train Time:** 0.6s | **Inference:** 0.6443s (174/s)
- **Metrics:**
  - Accuracy: 0.9554
  - Precision: 0.9588
  - Recall: 0.9894
  - F1: 0.9738
  - Mcc: 0.8273
  - Balanced Accuracy: 0.8836
  - Roc Auc: 0.9657
  - False Positive Rate: 0.2222
  - False Negative Rate: 0.0106

#### Confusion Matrix
| | Pred Safe | Pred Scam |
| - | --------: | --------: |
| **Actual Safe** | 14 | 4 |
| **Actual Scam** | 1 | 93 |
