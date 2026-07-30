# ScamShield — Agent State

## Active Summary

## Current Best Model
- **Backend model:** TF-IDF + LogisticRegression, trained on v2 gamma dataset (1,668 samples)
- **Performance:** CV F1=0.9769, Test F1=0.9731, Test ROC-AUC=0.9855
- **Top scam indicators:** http, pay, kyc, verify, pan, update
- **Top safe indicators:** credited, ref, otp, successfully, delivered

## Dataset
- **v2 gamma** (1668 samples: 1303 scam, 365 legit, 25 categories)
- File: `datasets/v2/annotated/dataset_v2_gamma.csv`
- Backend copy: `backend/data/dataset_v2_gamma.csv`
- Generator: `datasets/v2/annotated/v2_expand_gamma.py`
- Categories with <60 samples: FAKE_CUSTOMER_CARE(61), LOTTERY_SCAM(63), PAN_SCAM(63), QR_SCAM(64), DIGITAL_ARREST(66), INCOME_TAX_SCAM(68), LEGITIMATE_COURIER(59), LEGITIMATE_OTP(57), LEGITIMATE_UPI(56), LEGITIMATE_BANKING(53)

## Key Fixed Bugs
1. **Per-category F1=0 for legit categories**: Added `f1_legit` metric using `pos_label=0`; updated benchmark report to use `f1_legit` for `LEGITIMATE_*` categories
2. **train.py load_data**: Added support for both `label` (v1) and `is_scam` (v2) CSV columns
3. **train.py NameError**: `X_test_vec` not defined — added `vectorizer.transform(X_test)` before the classification report
4. **benchmark_runner.py**: `load_training_data` and `load_benchmark_dataset` used `label` instead of `is_scam`
5. **SVM AUC=0.5000**: Known artifact — LinearSVC lacks `predict_proba`. Use `CalibratedClassifierCV` for probability estimates if needed

## Backend Config Additions
- `SCAMSHIELD_DATASET_PATH` env var to override dataset path
- `V2_DATASET_PATH`, `V2_MODEL_PATH`, `V2_VECTORIZER_PATH` for v2 assets
- Backend currently uses gamma dataset via env var (`backend/data/dataset_v2_gamma.csv`)

## Known Issues
1. Transformer model (DistilBERT) won't train: `module 'datasets' has no attribute 'Dataset'` — library compat
2. Embedding evaluation is slow (per-sample SentenceTransformer inference on CPU)
3. A few categories still below 60 samples (legitimate categories mostly)
4. No non-English samples yet (Tamil/Hindi/Telugu)
5. Benchmark/gamma still uses beta DATA_PATH in run_beta_benchmark.py — need separate gamma benchmark

## Gold Evaluation (2026-07-30)
- **Dataset:** 308 samples (204 scam, 104 legit), 30 categories, 4 languages
- **Location:** `datasets/gold/gold_dataset.csv`
- **Zero leakage:** 8327 training texts checked — exact, cleaned, near-duplicate, template variant
- **Production model performance:**
  - Accuracy: 0.8604 | F1: 0.8933 | ROC-AUC: 0.9260 | MCC: 0.6920
  - FPR: 0.1827 | FNR: 0.1176
  - English F1=0.8986, Hindi=0.8947, Tamil=0.8889, Telugu=0.8485
  - Scam strong (F1 0.83-1.00) except OTP_SCAM (0.55)
  - Legit strong: govt/OTP perfect; weak: personal(0.69), telecom(0.67)
- **Reports:** GOLD_DATASET_REPORT.md, LEAKAGE_REPORT.md, GOLD_EVALUATION_REPORT.md, ERROR_ANALYSIS_GOLD.md

## Next Priorities
1. Create gamma benchmark script (copy of run_beta_benchmark.py with gamma DATA_PATH)
2. Add non-English samples to fill legitimate categories (Tamil, Hindi, Telugu)
3. Expand OTP_SCAM training data (weakest scam category, F1=0.55 on gold)
4. Collect more real-world scam messages from social sources
5. Train SVM with CalibratedClassifierCV and compare to current LR backend model
6. Fix legitimate personal/telecom FP issue (FPR=18%)
7. Add REST API endpoint for model retraining
