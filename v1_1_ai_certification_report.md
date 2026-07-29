# ScamShield v1.1 — Phase 12 AI Certification Report

**Date:** 2026-07-28  
**Certification Level:** Production-Readiness Audit  
**Status:** ❌ **NO-GO for Production** (Conditional GO for Beta/Research)

---

## 1. Executive Summary

ScamShield v1.0 was certified as **NO-GO for production** (conditional GO for beta/early access) due to three critical blockers:

1. **Romance scam 0% recall** — model trained on UCI SMS Spam (2005–2012 UK data), not Indian scam patterns
2. **Custom JWT vulnerabilities** — no-op `revoke_all_for_user()`, blacklist `clear()` at 100k entries
3. **`.env.production` committed to git**

After v1.0 refinements (FP reduction to 0 on 25-message legit benchmark, FN-009 fix, URL shortener substring bug fix, flip condition fix), we conducted the v1.1 AI Research & Detection Evolution Sprint. Full audit results below.

---

## 2. Phase 2: Data Quality Audit

| Metric | Value |
|--------|-------|
| Total rows | 5,715 |
| Scam / Safe | 888 (15.5%) / 4,827 (84.5%) |
| Duplicates | 414 (289 texts appear 2+ times) |
| Indian-context messages | ~370 (6.5%) |
| Non-ASCII texts | 553 (9.7%) |
| Mean / Median length | 80 / 63 chars |

**Category distribution of training data:**

| Category | Count | Scam |
|----------|-------|------|
| general | 4,827 | 0 |
| spam_generic | 747 | 747 |
| tanglish | 35 | 35 |
| upi_fraud | 15 | 15 |
| fake_kyc | 15 | 15 |
| govt_scheme | 14 | 14 |
| fake_job | 14 | 14 |
| bank_fraud | 14 | 14 |
| bill_scam | 12 | 12 |
| courier_scam | 12 | 12 |
| general_scam | 10 | 10 |

**Critical finding:** 747/888 scam messages (84%) are UK SMS spam from 2005–2012. Indian scam categories (UPI fraud, fake KYC, bank fraud, courier scam, etc.) have only **12–15 samples each** — far too few for reliable training.

---

## 3. Phase 3/4: Model Comparison

Benchmark: 162 samples (137 scam, 25 legitimate) from `evaluation/datasets/benchmark.json`

| Model | Accuracy | Precision | Recall | F1 | AUC |
|-------|----------|-----------|--------|-----|-----|
| **Current (disk)** | **82.10%** | 90.30% | 88.32% | 0.8930 | 0.7974 |
| **LogisticRegression (retrain)** | **88.27%** | 90.97% | 95.62% | **0.9324** | 0.9028 |
| SVM (linear) | 88.27% | 92.75% | 93.43% | 0.9309 | 0.9019 |
| SVM (rbf) | 84.57% | 95.16% | 86.13% | 0.9042 | **0.9194** |

**Best model:** LogisticRegression (F1=0.9324, AUC=0.9028) — marginally better than SVM linear.

**Category-level accuracy (best model):**

| Category | Total | Accuracy | TP | FP | FN |
|----------|-------|----------|----|----|-----|
| Bank KYC Scam | 16 | 100% | 16 | 0 | 0 |
| UPI Scam | 15 | 100% | 15 | 0 | 0 |
| Government Scheme Scam | 14 | 100% | 14 | 0 | 0 |
| Lottery Scam | 14 | 92.9% | 13 | 0 | 1 |
| Job Scam | 12 | 100% | 12 | 0 | 0 |
| Fake Customer Care | 10 | 80.0% | 8 | 0 | 2 |
| Loan Scam | 9 | 88.9% | 8 | 0 | 1 |
| QR Code Scam | 8 | 100% | 8 | 0 | 0 |
| Courier Scam | 7 | 100% | 7 | 0 | 0 |
| Phishing | 6 | 83.3% | 5 | 0 | 1 |
| Customs Scam | 5 | 100% | 5 | 0 | 0 |
| Electricity Bill Scam | 5 | 100% | 5 | 0 | 0 |
| Crypto Scam | 4 | 75.0% | 3 | 0 | 1 |
| Investment Scam | 8 | 100% | 8 | 0 | 0 |
| OTP Scam | 2 | 100% | 2 | 0 | 0 |
| **Legitimate** | **25** | **48.0%** | **0** | **13** | **0** |

**Key insight:** 100% recall on 12/18 scam categories. The two main problems:
- **52% false positive rate** on legitimate messages (13/25 flagged as scam)
- Lower recall on Fake Customer Care (80%), Phishing (83.3%), Crypto (75%)

---

## 4. Phase 5: Root Cause Analysis

### False Negatives (7 total)

| ID | Category | Confidence | Root Cause |
|----|----------|------------|------------|
| lottery-010 | Lottery Scam | 0.484 | Below threshold (0.5) |
| invest-005 | Crypto Scam | 0.326 | Low confidence: crypto/WhatsApp patterns not in training |
| otp-004 | Phishing | 0.492 | Below threshold |
| otp-008 | Phishing | 0.441 | Apple ID verify text — no training examples |
| support-005 | Fake Customer Care | 0.300 | IRCTC helpdesk pattern not in training |
| support-007 | Fake Customer Care | 0.452 | PhonePe support pattern not in training |
| loan-007 | Loan Scam | 0.477 | Below threshold |

### False Positives (13 total — ALL on Legitimate)

| ID | Text Pattern | Confidence | Trigger |
|----|-------------|------------|---------|
| legit-001 | OTP for SBI transaction | 0.640 | OTP + bank name + "share" |
| legit-002 | Aadhaar OTP valid for UIDAI | 0.589 | OTP + Aadhaar |
| legit-003 | HDFC Bank Rs 15000 credited | 0.557 | Money + bank name |
| legit-004 | Flipkart order shipped | 0.552 | URL + order context |
| legit-006 | Swiggy order confirmed | 0.618 | "Order" in commercial context |
| legit-008 | Mobile bill paid | 0.615 | Money + "paid" |
| legit-012 | Zomato delivered | 0.675 | "Delivered" + rating prompt |
| legit-013 | Password changed successfully | 0.558 | "Password changed" + "immediately" |
| legit-018 | BigBasket grocery delivery | 0.730 | "Delivery" + "order" |
| mixed-001 | Account credited Rs 1000 | 0.727 | Money + "account credited" |
| mixed-003 | Free consultation | 0.711 | "Free" + "reply" + callback |
| mixed-008 | Purchase survey 10% off | 0.534 | "Purchase" + "order" |
| mixed-009 | Pre-selected credit card | 0.704 | "Congratulations" + "credit card" + "limit" |

### Feature Analysis

**Top 10 scam-indicative features (coefficients):**
`http` (+6.56), `txt` (+5.23), `claim` (+4.29), `mobile` (+3.85), `free` (+3.76), `text` (+3.66), `stop` (+3.50), `reply` (+3.44), `won` (+3.13), `chat` (+2.91)

**Problem:** These are UK SMS spam features (2005 prize/lottery patterns). **No Indian-specific features** like `upi`, `kyc`, `aadhaar`, `pan`, `gpay`, `phonepe` appear in top 20.

---

## 5. Certification Decision

### ❌ NO-GO for Production

**Critical blockers:**

| # | Issue | Severity | Evidence |
|---|-------|----------|----------|
| 1 | **Training data is UK SMS spam, not Indian scams** | CRITICAL | 747/888 scam messages are UK SMS spam 2005–2012; Indian categories have 12–15 samples each; top features are UK prize/lottery patterns |
| 2 | **52% false positive rate on legitimate messages** | HIGH | 13/25 legit benchmark messages flagged as scam; real-world FP rate would be unacceptable |
| 3 | **Duplicate data inflates metrics** | MEDIUM | 414 duplicate rows (7.2% of dataset) cause train/test contamination |
| 4 | **No validation set, cross-validation only at 5-fold** | MEDIUM | No held-out validation for hyperparameter tuning |
| 5 | **Category column ignored during training** | MEDIUM | Cannot do per-category classification or routing |

**No romance scam recall** — remains 0% with current data.

### ✅ Conditional GO for Beta / Research

Continue as beta for research use with the following roadmap:

1. **Dataset Engineering (Phase 1):** Build 3000–5000 labelled Indian scam messages across 23+ categories (UPI fraud, Aadhaar KYC, courier scam, fake job, electricity bill, romance scam, etc.)
2. **Model retraining:** Replace UK-centric LogisticRegression with best-of-class (LR or SVM linear) on new dataset
3. **Rule engine refactoring:** Consolidate OTP detection from 7 locations, deduplicate FP/FN rules
4. **Auth replacement:** Replace custom JWT with `pyjwt` library, add proper revocation
5. **TypeScript strict mode:** Enable `strict: true` after fixing null/undefined errors
6. **Continuous evaluation:** Integrate `evaluation_runner.py` into CI pipeline

---

## 6. Actionable Recommendations

| Priority | Area | Recommendation |
|----------|------|----------------|
| **CRITICAL** | Dataset | Build 3000–5000 labelled Indian scam messages (UPI, Aadhaar, KYC, courier, fake job, electricity bill, romance, loan, investment, phishing, fake customer care) |
| **CRITICAL** | Dataset | Collect minimum 100 samples per category for reliable per-category metrics |
| **HIGH** | Dataset | Deduplicate training data before retraining |
| **HIGH** | Model | Replace current model with LogisticRegression or SVM linear — both achieve 88%+ accuracy on benchmark |
| **HIGH** | Evaluation | Merge all inline benchmark scripts into unified `benchmark.json` (>200 samples) |
| **MEDIUM** | FP Reduction | Add context-aware legit rules: OTP-without-solicitation, bank-credit-without-request, delivery-status messages |
| **MEDIUM** | Architecture | Fix auth layer (custom JWT → pyjwt) before production deployment |
| **MEDIUM** | Architecture | Remove dead code: unused components (5 frontend components), dead middleware (`RateLimitMiddleware`), bank list duplication (4+ files) |
| **LOW** | Engineering | Enable TypeScript `strict: true` |
| **LOW** | Engineering | Enable `sublinear_tf=True` in vectorizer for better frequency scaling |