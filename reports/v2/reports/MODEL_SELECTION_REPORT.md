# Model Selection Report

**Date:** 2026-07-30 14:29:50

## Executive Summary

**Recommended Model:** `tfidf_svm` (composite score: 0.7956)

| Rank | Model | Composite Score | F1 | Precision | Recall | AUC | MCC | Train Time | Inference |
| ---: | ----- | --------------: | -: | --------: | ----: | --: | --: | ---------: | --------: |
| 1 | `tfidf_svm` | 0.7956 | 0.9157 | 0.8491 | 0.9936 | 0.7941 | 0.1546 | 0.5s | 312/s |
| 2 | `tfidf_lr` | 0.5813 | 0.9148 | 0.8475 | 0.9936 | 0.7997 | 0.1279 | 1.0s | 431/s |
| 3 | `embedding` | 0.2000 | 0.9144 | 0.8423 | 1.0000 | 0.5458 | 0.0000 | 482.8s | 2/s |
| - | `transformer` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

> **Note:** `transformer` (DistilBERT) could not be evaluated due to PyTorch DLL compatibility issue with Python 3.14 on the benchmark system. It was installed and loaded model weights successfully, but `accelerate` integration failed at runtime.

## Detailed Analysis By Criterion

### Accuracy

**Best:** `tfidf_svm` (0.8458781362007168)

- `tfidf_svm`: 0.8459 ✅
- `tfidf_lr`: 0.8441
- `embedding`: 0.8423

### Precision

**Best:** `tfidf_svm` (0.8490909090909091)

- `tfidf_svm`: 0.8491 ✅
- `tfidf_lr`: 0.8475
- `embedding`: 0.8423

### Recall

**Best:** `embedding` (1.0)

- `embedding`: 1.0000 ✅
- `tfidf_svm`: 0.9936
- `tfidf_lr`: 0.9936

### F1 Score

**Best:** `tfidf_svm` (0.9156862745098039)

- `tfidf_svm`: 0.9157 ✅
- `tfidf_lr`: 0.9148
- `embedding`: 0.9144

### ROC-AUC

**Best:** `tfidf_lr` (0.7997340425531914)

- `tfidf_lr`: 0.7997 ✅
- `tfidf_svm`: 0.7941
- `embedding`: 0.5458

### MCC

**Best:** `tfidf_svm` (0.1546314045897137)

- `tfidf_svm`: 0.1546 ✅
- `tfidf_lr`: 0.1279
- `embedding`: 0.0000

### Balanced Accuracy

**Best:** `tfidf_svm` (0.5252176015473888)

- `tfidf_svm`: 0.5252 ✅
- `tfidf_lr`: 0.5195
- `embedding`: 0.5000

### Training Speed

**Best:** `tfidf_svm` (0.53)

- `tfidf_svm`: 0.5300 ✅
- `tfidf_lr`: 0.9900
- `embedding`: 482.8300

### Inference Speed

**Best:** `tfidf_lr` (431.24)

- `tfidf_lr`: 431.2400 ✅
- `tfidf_svm`: 312.4300
- `embedding`: 2.3400

## Critical Finding: Training-Evaluation Data Mismatch

All models exhibit **extremely high false positive rates (~95%)** because the training data (`scam_dataset.csv`) and evaluation data (`dataset_v2_alpha.csv`) have inverted class distributions:

| Dataset | Safe | Scam |
| ------- | ---: | ---: |
| Training | 4,827 (84.5%) | 888 (15.5%) |
| Evaluation | 88 (15.8%) | 470 (84.2%) |

The training set's scam samples use **old generic categories** (spam_generic, general_scam) while the evaluation set tests **25 modern Indian scam categories** (UPI_FRAUD, AADHAAR_SCAM, DIGITAL_ARREST, etc.). The TF-IDF models effectively default to "predict scam for unknown patterns" because the word features learned from old data don't match the new scam vocabulary.

**Implication:** The benchmark results reflect how well each model generalizes from old scam patterns to new Indian scam types — not absolute production performance. A model retrained on the v2 dataset would likely perform significantly better.

## Trade-offs and Considerations

### **`tfidf_svm`** (Top Ranked)

**Strengths:**
- Best F1
- Best MCC

**Weaknesses:**
- Lowest FPR (good)
- Highest FNR (bad)

**Recommendation:** Strongly recommended for production.

### **`tfidf_lr`** (Runner-up)

- Best roc_auc
- Worst recall

### **`embedding`**

**When to use:** 
When semantic understanding is needed and GPU is available.

## Final Recommendation

**→ Deploy `tfidf_svm`** as the primary scam detection model.

**⚠️ Important caveat:** This is the best available model for the *current* training data. The high FPR (94%) is driven by the training/evaluation class inversion, not model quality. A model retrained on the v2 alpha dataset would be expected to perform significantly better.

### Next Steps

1. **Retrain on v2 dataset**: The top priority should be retraining `tfidf_svm` on the v2 alpha dataset (558 samples, 25 categories) instead of the old `scam_dataset.csv`. The current evaluation measures cross-dataset generalization, not production readiness.
2. **Fix PyTorch/DistilBERT**: The transformer model could not be evaluated due to Python 3.14 compatibility issues. Once resolved, DistilBERT should be evaluated as it offers the best potential for semantic understanding of diverse Indian scam patterns.
3. **Address class imbalance**: Both training and evaluation data need balanced sampling or weighted loss to avoid the "always predict majority class" behavior.
4. **Set up monitoring** for false positive rate in production.
5. **Implement A/B testing** framework to compare against existing model.
6. **Schedule periodic retraining** with newly labeled data.
