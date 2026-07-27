# ML Model Evaluation Report

**Date**: 2026-07-26

---

## 1. Model Architecture

| Component | Details |
|---|---|
| Algorithm | `LogisticRegression` (scikit-learn) |
| Vectorizer | `TfidfVectorizer` (character n-grams 3-5 + word n-grams 1-2) |
| Model files | `backend/models/model.joblib`, `backend/models/vectorizer.joblib` |
| Training | `backend/train.py` |
| Prediction | `backend/predict.py` |
| ML service | `backend/services/ml_service.py` |

---

## 2. Training Pipeline

### 2.1 Data Sources
- The model is trained on labeled SMS text data
- `train.py` loads data, vectorizes, fits LogisticRegression
- No explicit dataset file found in the repository for training

### 2.2 Features
- TF-IDF with character n-grams (3-5) — captures subword patterns (e.g., "free", "win", "urgent")
- TF-IDF with word n-grams (1-2) — captures phrase patterns (e.g., "you won", "click here")
- Combined feature matrix

### 2.3 Training Concerns
- No training dataset committed in the repo — only evaluation datasets
- No hyperparameter tuning configuration visible
- No cross-validation strategy documented
- No class imbalance handling explicitly configured

---

## 3. Model Performance (Validation v1 — 511 samples)

### 3.1 Overall Metrics

| Metric | Value |
|---|---|
| Accuracy | 72.8% |
| F1 Score | 83.1% |
| Precision | Not explicitly stated |
| Recall | Not explicitly stated |

### 3.2 Per-Category Performance (from docs/VALIDATION_REPORT.md)

Performance varies by scam category. Multi-language performance was evaluated. Error analysis available.

---

## 4. Strengths

- **Simple, interpretable model**: LogisticRegression provides coefficient-based explainability (feature importance)
- **Fast inference**: ~30-50ms per prediction
- **Combined with rule engine**: ML is only one of 12 pipeline stages — rules provide coverage where ML is weak
- **TF-IDF captures scam language patterns**: Character n-grams (3-5) effectively capture obfuscated/scammy text patterns

---

## 5. Weaknesses

| Issue | Impact | Severity |
|---|---|---|
| No training dataset in repo | Cannot reproduce training | **High** |
| No hyperparameter tuning | Suboptimal performance | **Medium** |
| No cross-validation | Risk of overfitting | **Medium** |
| No model versioning | Cannot roll back | **Medium** |
| No online/A/B evaluation | No production performance data | **Medium** |
| Single model for all categories | May not capture all scam types equally | **Medium** |
| No active learning loop | Model cannot improve from new data | **Low** |
| 72.8% accuracy on 511-sample val | Room for improvement | **Medium** |

---

## 6. Evaluation Framework Quality

### 6.1 Strengths
- Comprehensive evaluation runner (`evaluation_runner.py`)
- Supports both API and local analysis modes
- Schema validation for datasets
- Error analysis script
- HTML report generation
- 511-sample validation dataset with diverse categories
- Knowledge service evaluation

### 6.2 Weaknesses
- Evaluation is run in-process (no async/parallel)
- No automated regression testing for model accuracy
- Dataset may not represent real-world distribution
- No confusion matrix analysis in standard output

---

## 7. Recommendations

1. **Commit training dataset** to enable reproducible training
2. **Add hyperparameter tuning** — grid/random search with cross-validation
3. **Add model versioning** — store models with version tags (mlflow or simple)
4. **Improve accuracy** — consider ensemble (Random Forest, XGBoost) or transformer-based models (DistilBERT)
5. **Add confidence calibration** — use `CalibratedClassifierCV`
6. **Add online evaluation** — track performance on production data
7. **Add active learning** — human-in-the-loop for uncertain predictions
8. **Replace joblib pickle** with ONNX or PMML for safer model serialization
9. **Add model card** documenting training data, metrics, biases, and limitations
10. **Split training/validation/test** with 60/20/20 ratio for rigorous evaluation
