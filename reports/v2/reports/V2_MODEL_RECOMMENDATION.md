# V2 Model Recommendation

**Date:** 2026-07-30 14:49:11

## Recommendation

**→ Deploy `tfidf_svm`** as the v2 baseline model.

| Rank | Model | Composite | CV F1 | Test F1 | AUC | MCC | FPR | FNR | Train |
| ---: | ----- | --------: | ----: | ------: | --: | --: | --: | --: | ----: |
| 1 | `tfidf_svm` | 0.7935 | 0.9699 | 0.9738 | 0.9657 | 0.8273 | 0.2222 | 0.0106 | 0.6s |
| 2 | `embedding` | 0.5361 | 0.9617 | 0.9733 | 0.9379 | 0.8386 | 0.1111 | 0.0319 | 317.4s |
| 3 | `tfidf_lr` | 0.2725 | 0.9696 | 0.9630 | 0.9716 | 0.7634 | 0.2222 | 0.0319 | 0.6s |

## Cross-Benchmark Comparison: v1 Training vs v2 Training

The previous benchmark trained on `scam_dataset.csv` (5,715 rows, old categories) and evaluated on v2 alpha.
This benchmark trains and evaluates **both on v2 alpha** (558 rows, 25 modern Indian categories).

| Metric | v1→v2 `tfidf_svm` | v2→v2 `tfidf_svm` | Improvement |
| ------ | -----------------: | -----------------: | ----------: |
| F1 | 0.9157 | 0.9738 | ▲ 0.0581 |
| Precision | 0.8491 | 0.9588 | ▲ 0.1097 |
| Recall | 0.9936 | 0.9894 | ▼ 0.0043 |
| Roc Auc | 0.7941 | 0.9657 | ▲ 0.1716 |
| Mcc | 0.1546 | 0.8273 | ▲ 0.6726 |
| Balanced Accuracy | 0.5252 | 0.8836 | ▲ 0.3584 |
| False Positive Rate | 0.9432 | 0.2222 | ▲ 0.7210 |
| False Negative Rate | 0.0064 | 0.0106 | ▼ 0.0043 |

### Key Takeaway

- **Training on v2 data dramatically reduces false positive rate.** The previous benchmark had ~94% FPR because the v1 training data had no representative legitimate samples matching the v2 domain. Now the model sees both scam and legitimate messages from the same distribution.
- **FPR dropped from 94.32% to 22.22%** — massive improvement in legitimate message handling.
- **F1 improved from 0.9157 to 0.9738** — overall better scam detection.
- The v2-trained model is the **first true ScamShield baseline** for modern Indian scam detection.

## Model Strengths & Weaknesses

### `embedding`

**Strengths:**
- High recall (0.9681) — few scams missed
- Good precision (0.9785)
- Strong ROC-AUC (0.9379)

**Weaknesses:**
- Most FNs in: TELECOM_SCAM(2), BANKING_FRAUD(1)

### `tfidf_lr`

**Strengths:**
- High recall (0.9681) — few scams missed
- Good precision (0.9579)
- Strong ROC-AUC (0.9716)

**Weaknesses:**
- High FPR (0.2222) — legitimate messages flagged as scam
- Most FNs in: TELECOM_SCAM(2), UPI_FRAUD(1)

### `tfidf_svm`

**Strengths:**
- High recall (0.9894) — few scams missed
- Good precision (0.9588)
- Strong ROC-AUC (0.9657)

**Weaknesses:**
- High FPR (0.2222) — legitimate messages flagged as scam
- Most FNs in: UPI_FRAUD(1)

## Final Verdict

**Retraining on v2 significantly improves ScamShield.** The false positive rate drops from ~94% to ~22.2% — essentially fixing the core issue identified in the previous benchmark. The v2-trained model is now a credible baseline for real-world Indian scam detection.

### Next Steps

1. **Expand the dataset** — categories with <15 samples (PAN_SCAM, INCOME_TAX_SCAM, DIGITAL_ARREST) need more data.
2. **Fix PyTorch** — evaluate DistilBERT on v2 data once Python 3.14 compatibility is resolved.
3. **Deploy v2 model** to replace the current v1-based production model.
4. **Monitor FPR in production** — the v2 legit categories may not cover all production scenarios.
5. **Iterate** — use active learning to label the most uncertain production samples.
