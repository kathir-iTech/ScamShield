# Validation Report — ScamShield v1.0.0

## Executive Summary

ScamShield v1.0.0 was evaluated on **511 diverse samples** across 20 categories. The system achieves **72.8% accuracy** and **83.1% F1 score**, with strong performance on high-signal scam categories (Lottery 96%, UPI 97%, Bank KYC 93%, OTP 90%) but elevated false positives on legitimate messages (38.3% accuracy).

## Dataset

| Attribute | Value |
|-----------|-------|
| Total Samples | 511 |
| Scam Samples | 430 |
| Legitimate Samples | 81 |
| Categories | 20 |
| Languages | English, Tamil, Tanglish |
| Difficulty | Easy 38.7%, Medium 43.2%, Hard 18.0% |
| Source Types | SMS, WhatsApp, Email, Telegram, Social |
| Notable Subsets | 16 image-based, 14 multi-message, 35 Tanglish, 22 Tamil |

## Overall Performance

| Metric | 162-Sample Baseline | 511-Sample Validation | Δ |
|--------|--------------------|----------------------|---|
| Accuracy | 83.3% | 72.8% | -10.5pp |
| Precision | 90.4% | 87.2% | -3.2pp |
| Recall | 89.8% | 79.3% | -10.5pp |
| F1 Score | 90.1% | 83.1% | -7.0pp |
| False Positive Rate | 52.0% | 61.7% | +9.7pp |
| False Negative Rate | 10.2% | 20.7% | +10.5pp |

The decline is expected — the 511-sample dataset includes harder samples (mixed-language, image-based, subtle scams) that stress-test beyond the original benchmark.

## Confusion Matrix

```
               Predicted
             Legit  Scam
Actual Legit   31    50
       Scam    89   341
```

- True Negatives: 31 | False Positives: 50
- False Negatives: 89 | True Positives: 341

## Per-Category Accuracy

| Category | Accuracy | Samples | Notes |
|----------|----------|---------|-------|
| UPI Scam | **97.2%** | 36 | Strong URL/UPI pattern detection |
| Lottery Scam | **96.0%** | 50 | Phone numbers + prize language well-detected |
| Bank KYC Scam | **92.7%** | 41 | Bank names + urgency patterns reliable |
| OTP Scam | **90.0%** | 10 | OTP keyword detection works well |
| Fake Customer Care | **88.2%** | 17 | Phone number patterns effective |
| Government Scheme | **85.0%** | 20 | Govt impersonation patterns solid |
| Mixed | **81.8%** | 11 | Multi-indicator samples handled |
| Phishing | **80.0%** | 65 | Broad coverage from ML + rules |
| Electricity Bill | **78.6%** | 14 | Disconnection threats detected |
| Subscription Scam | **77.3%** | 22 | Service impersonation patterns |
| Account Suspension | **76.5%** | 17 | Suspension language detected |
| Customs Scam | **75.0%** | 12 | Customs + payment patterns |
| QR Code Scam | **71.4%** | 14 | QR references + suspicious URLs |
| Courier Scam | **70.0%** | 20 | Delivery + payment patterns |
| Crypto Scam | **70.0%** | 10 | Crypto language partially detected |
| Job Scam | **66.7%** | 12 | Job + fee patterns detected |
| Loan Scam | **55.6%** | 18 | Loan offers sometimes missed |
| Investment Scam | **50.0%** | 28 | Subtle investment language missed |
| Legitimate | **38.3%** | 81 | High false positive rate |
| Fake Support | **38.5%** | 13 | Subtle support impersonation |
| Category Accuracy | **41.1%** | 511 | Correct category assignment |

## Error Analysis

### False Positives (50)
Legitimate messages flagged as scam. Common patterns:
- Transaction alerts with amounts ("Rs 5000 credited...") → flagged for currency amounts
- OTP messages with "OTP" keyword → flagged as scam despite legitimate context
- Service messages with urgency language ("password changed successfully", "account will be suspended if...")
- Delivery notification with tracking URLs → flagged for shortened URLs

### False Negatives (89)
Scam messages missed. Common patterns:
- Investment/crypto scams without URLs (just phone numbers)
- Loan scams with only a phone number, no URL
- Hard difficulty samples with subtle language
- Mixed-language (Tanglish) samples where scam indicators translated
- Image-based scam descriptions (text-only representation of scam images)

## Multi-Language Performance

| Language | Accuracy | Samples |
|----------|----------|---------|
| English | 74.5% | 454 |
| Tamil | 63.6% | 22 |
| Tanglish | 65.7% | 35 |

Non-English samples show reduced accuracy, suggesting the TF-IDF model's English-biased vocabulary and English-focused rule patterns are less effective on code-mixed and Tamil text.

## Key Findings

1. **Strong scam detection on high-signal categories** — UPI, Lottery, Bank KYC, OTP scams are reliably detected
2. **Legitimate false positive rate is the primary concern** — 61.7% FPR on legitimate messages reduces trustworthiness; 50 of 81 safe messages flagged
3. **Category accuracy (41.1%) needs improvement** — while the system detects scams, it often assigns wrong sub-categories
4. **Non-English performance degrades** — Tamil and Tanglish samples show 10-11pp lower accuracy
5. **Subtle scams (Investment, Fake Support) need better detection** — these categories lack strong URL/phone indicators
6. **Average inference (45.2ms) and P95 (65.8ms) are excellent** — pipeline is performant

## Recommendations

1. **Improve legitimate message handling** — add a "benign transaction" recognizer, lower sensitivity for amount-only messages
2. **Expand non-English rule patterns** — add Tamil and Tanglish rule variants
3. **Improve category classification** — add a secondary classifier for scam sub-type
4. **Add image scam detection** — build an image analysis pipeline beyond OCR text extraction
5. **Reduce false negatives on investment/crypto** — add domain-specific patterns for these categories
