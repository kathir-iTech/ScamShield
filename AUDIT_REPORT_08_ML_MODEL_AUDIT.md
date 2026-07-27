# REPORT 8: ML MODEL AUDIT

## 1. Model Overview

| Property | Value |
|---|---|
| Algorithm | Logistic Regression |
| Vectorizer | TF-IDF (unigrams + bigrams) |
| Max features | 5000 |
| Framework | scikit-learn 1.5+ |
| File size | ~850 KB (model.joblib) + ~250 KB (vectorizer.joblib) |
| Training date | Unknown (not embedded in model metadata) |
| Training environment | Unknown (not documented) |
| Python version | Unknown (not documented) |

## 2. Training Process

`train.py` shows:
1. Loads CSV from `dataset/` directory
2. Splits into train/test (80/20)
3. TF-IDF vectorization (max_features=5000, ngram_range=(1,2))
4. LogisticRegression(C=1.0, max_iter=1000, random_state=42)
5. Exports model + vectorizer as .joblib files
6. Exports ~50 most important features per class to `dataset/features.json`

**Issues:**
- No hyperparameter tuning (grid search, random search, Bayesian optimization)
- No cross-validation
- No class weighting (despite 2.5:1 imbalance)
- No feature selection beyond TF-IDF threshold
- No baseline comparison (dummy classifier, simple heuristic)
- Random state is fixed (42) but this is not documented
- No experiment tracking (MLflow, Weights & Biases, etc.)
- No versioning of training runs

## 3. Model Evaluation

The `evaluate_pipeline.py` script computes:
- Accuracy, precision, recall, F1
- Confusion matrix
- ROC curve

**But:** It is not wired into the CI pipeline, not run automatically, and no baseline metrics are published.

## 4. Interpretability

| Technique | Present? | Notes |
|---|---|---|
| Feature importance | ✅ | Top 50 features exported to features.json |
| Coefficients | ✅ | LogisticRegression coefficients accessible |
| TF-IDF terms | ✅ | Top-weighted terms per class extracted |
| SHAP/LIME | ❌ | Not integrated |
| Partial dependence | ❌ | Not implemented |
| Counterfactual explanations | ❌ | Not implemented |

**Top features for scam class** (from features.json): `free`, `claim`, `prize`, `urgent`, `winner`, `congratulations`, `lottery`, `cash`, `gift`, `bank`, `account`, `verify`, `update`, `otp`, `limited`, `offer`, `exclusive`, `click`, `link`, `won`

**Top features for safe class:** `thanks`, `ok`, `will`, `let`, `know`, `meeting`, `see`, `tomorrow`, `home`, `work`, `talk`, `call`, `later`, `time`, `day`, `night`, `morning`, `yes`, `no`, `sorry`

## 5. Model Risks

| Risk | Severity | Explanation |
|---|---|---|
| Adversarial examples | High | Small perturbations (adding "thanks" or "ok") could flip prediction |
| Distribution shift | High | Model trained on static dataset; scam tactics evolve |
| Spurious correlations | Medium | Model may rely on surface features (length, punctuation count) |
| Calibration | Medium | LogisticRegression probabilities are poorly calibrated; no Platt scaling |
| Overconfidence | Medium | High-confidence predictions on OOD inputs |
| Bias amplification | Medium | May over-flag messages with scam-like vocabulary (e.g., "free pizza") |
| Feedback loops | Low | No online learning; no self-reinforcing bias |

## 6. Reproducibility

| Prerequisite | Status |
|---|---|
| Training data versioned | ❌ Not tracked |
| Training script versioned | ✅ In repo |
| Random seed documented | ✅ (42) |
| Environment documented | ❌ No conda/pip freeze captured |
| Hardware documented | ❌ Not captured |
| Training duration | ❌ Not captured |
| Model metadata | ❌ Not embedded in model file |

## 7. Model Operations (MLOps)

| Practice | Status |
|---|---|
| Model versioning | ❌ Not implemented |
| Model registry | ❌ Not implemented |
| A/B testing framework | ❌ Not implemented |
| Shadow deployment | ❌ Not implemented |
| Automated retraining | ❌ Not implemented |
| Drift detection | ❌ Not implemented |
| Model monitoring | ❌ Not implemented |
| Rollback capability | ❌ Model file overwritten on update |
| Canary deployment | ❌ Not implemented |
