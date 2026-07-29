# ScamShield v2 – Benchmark Design

## Overview

The v2 benchmark is a curated evaluation dataset of **500+ samples** covering all 25 categories. Every future model must be evaluated against this benchmark before release.

## Benchmark Dataset

### Structure

| Property | Value |
|----------|-------|
| Total samples | 500+ (target) |
| Scam samples | 380+ (19 categories × 20 samples each) |
| Legitimate samples | 120+ (6 categories × 20 samples each) |
| Difficulty distribution | 40% easy, 35% medium, 25% hard |
| Language distribution | 70% English, 20% Hinglish, 10% other Indian languages |

### Categories

| Category | Samples | Difficulty |
|----------|---------|------------|
| UPI_FRAUD | 20 | Easy-Medium |
| BANKING_FRAUD | 20 | Easy |
| KYC_SCAM | 20 | Easy |
| AADHAAR_SCAM | 20 | Medium |
| PAN_SCAM | 20 | Medium |
| FAKE_CUSTOMER_CARE | 20 | Medium-Hard |
| COURIER_SCAM | 20 | Easy-Medium |
| ELECTRICITY_BILL_SCAM | 20 | Medium |
| QR_SCAM | 20 | Medium |
| LOTTERY_SCAM | 20 | Easy |
| INVESTMENT_SCAM | 20 | Medium |
| CRYPTO_SCAM | 20 | Medium-Hard |
| LOAN_SCAM | 20 | Easy-Medium |
| JOB_SCAM | 20 | Easy-Medium |
| ROMANCE_SCAM | 20 | Hard |
| GOVERNMENT_IMPERSONATION | 20 | Medium |
| DIGITAL_ARREST | 20 | Hard |
| INCOME_TAX_SCAM | 20 | Medium |
| TELECOM_SCAM | 20 | Medium |
| LEGITIMATE_BANKING | 20 | Medium |
| LEGITIMATE_UPI | 20 | Medium |
| LEGITIMATE_OTP | 20 | Hard |
| LEGITIMATE_COURIER | 20 | Medium |
| LEGITIMATE_GOVERNMENT | 20 | Hard |
| LEGITIMATE_OTHER | 20 | Easy |

### Difficulty Definitions

| Difficulty | Criteria |
|------------|----------|
| **Easy** | Clear scam signals (URL, urgency, money request, known scam phrases). Model should detect with >95% confidence. |
| **Medium** | Subtle signals. May use legitimate-like language. Model confidence 80–95%. |
| **Hard** | Adversarial. Uses social engineering without obvious signals. No URLs, no urgency. Requires deep semantic understanding. |

## Evaluation Metrics

### Primary Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Accuracy | ≥ 92% | Overall correct predictions |
| Precision | ≥ 95% | Of scam predictions, how many are correct |
| Recall | ≥ 90% | Of actual scams, how many are detected |
| F1 Score | ≥ 92% | Harmonic mean of precision and recall |
| FPR | ≤ 5% | Legitimate messages flagged as scam |
| FNR | ≤ 10% | Scam messages missed |

### Secondary Metrics

| Metric | Description |
|--------|-------------|
| AUC-ROC | Area under ROC curve |
| AUC-PR | Area under precision-recall curve |
| MCC | Matthews correlation coefficient |
| Balanced Accuracy | Average of recall and specificity |
| Per-category F1 | F1 score per category |
| Calibration Error | Expected calibration error (ECE) |
| P50/P95/P99 Latency | Inference time percentiles |

### Per-Category Targets

| Category | Min Recall | Min Precision |
|----------|------------|---------------|
| UPI_FRAUD | 95% | 95% |
| BANKING_FRAUD | 95% | 95% |
| KYC_SCAM | 95% | 95% |
| AADHAAR_SCAM | 90% | 90% |
| PAN_SCAM | 90% | 90% |
| FAKE_CUSTOMER_CARE | 85% | 90% |
| COURIER_SCAM | 95% | 95% |
| ELECTRICITY_BILL_SCAM | 90% | 90% |
| QR_SCAM | 90% | 95% |
| LOTTERY_SCAM | 95% | 95% |
| INVESTMENT_SCAM | 90% | 90% |
| CRYPTO_SCAM | 85% | 90% |
| LOAN_SCAM | 90% | 90% |
| JOB_SCAM | 90% | 90% |
| ROMANCE_SCAM | 80% | 85% |
| GOVERNMENT_IMPERSONATION | 90% | 90% |
| DIGITAL_ARREST | 85% | 90% |
| INCOME_TAX_SCAM | 90% | 90% |
| TELECOM_SCAM | 90% | 90% |
| LEGITIMATE_BANKING | 95% | 95% |
| LEGITIMATE_UPI | 95% | 95% |
| LEGITIMATE_OTP | 90% | 85% |
| LEGITIMATE_COURIER | 95% | 90% |
| LEGITIMATE_GOVERNMENT | 90% | 85% |
| LEGITIMATE_OTHER | 90% | 90% |

## Evaluation Procedure

### Steps

1. **Load benchmark dataset** from `datasets/v2/benchmark/benchmark_v2.json`
2. **Run predictions** through model — each sample yields `{"prediction", "confidence", "category"}`
3. **Compute overall metrics** — accuracy, precision, recall, F1, FPR, FNR, AUC, MCC
4. **Compute per-category metrics** — breakdown by each of the 25 categories
5. **Calibration analysis** — reliability diagram, ECE
6. **Error analysis** — profile FPs and FNs, find failure patterns
7. **Regression check** — compare against previous best results
8. **Generate report** — HTML + JSON output

### Command

```bash
# Evaluate a single model
python benchmarks/v2/scripts/benchmark_runner.py \
    --dataset datasets/v2/benchmark/benchmark_v2.json \
    --models tfidf_lr tfidf_svm \
    --output benchmarks/v2/reports/

# Run full comparison
python benchmarks/v2/scripts/benchmark_runner.py \
    --dataset datasets/v2/benchmark/benchmark_v2.json \
    --all-models \
    --output benchmarks/v2/reports/
```

## Versioning

| Version | Date | Samples | Notes |
|---------|------|---------|-------|
| v2.0.0-alpha | 2026-Q3 | 100 | Initial seed |
| v2.0.0-beta | 2026-Q4 | 250 | Expanded with hard cases |
| v2.0.0-rc1 | 2027-Q1 | 400 | Near final |
| v2.0.0 | 2027-Q2 | 500+ | Production release |

## Quality Gates

Before marking any model as "production-ready":

- [ ] Overall accuracy ≥ 92%
- [ ] FPR ≤ 5%
- [ ] FNR ≤ 10%
- [ ] Per-category recall ≥ 80% (minimum for any category)
- [ ] Per-category precision ≥ 85% (minimum for any category)
- [ ] ECE (calibration error) ≤ 0.05
- [ ] P95 latency ≤ 50ms
- [ ] No regression on any category vs previous best