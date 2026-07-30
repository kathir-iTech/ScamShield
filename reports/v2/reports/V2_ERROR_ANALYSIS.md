# V2 Error Analysis

**Date:** 2026-07-30 14:49:11

## Summary

| Model | Correct | Incorrect | Accuracy | FP | FN | FPR | FNR |
| ----- | ------: | --------: | -------: | -: | -: | --: | --: |
| `embedding` | 107 | 5 | 0.9554 | 2 | 3 | 0.1111 | 0.0319 |
| `tfidf_lr` | 105 | 7 | 0.9375 | 4 | 3 | 0.2222 | 0.0319 |
| `tfidf_svm` | 107 | 5 | 0.9554 | 4 | 1 | 0.2222 | 0.0106 |

## Model: `embedding`

### False Positives (2 — Legit flagged as Scam)

**Categories affected:**
- LEGITIMATE_GOVERNMENT: 1
- LEGITIMATE_OTHER: 1

**Avg Confidence:** 0.9406

**Top FP Examples:**

| # | Category | Confidence | Text (truncated) |
| - | -------- | ---------: | ---------------- |
| 1 | LEGITIMATE_GOVERNMENT | 0.8812 | voter helpline: your voter id application e1234567 has been approved. card will be delivered shortly |
| 2 | LEGITIMATE_OTHER | 1.0000 | linkedin: john doe sent you a connection request. view profile: https://linkedin.com/in/johndoe |

### False Negatives (3 — Scam flagged as Safe)

**Categories affected:**
- TELECOM_SCAM: 2
- BANKING_FRAUD: 1

**Avg Confidence:** 0.1564

**Top FN Examples:**

| # | Category | Confidence | Text (truncated) |
| - | -------- | ---------: | ---------------- |
| 1 | TELECOM_SCAM | 0.1399 | netflix: your otp is 638192. share with our support agent for account recovery. do not ignore. |
| 2 | TELECOM_SCAM | 0.0046 | irctc: your booking otp is 719283. whatsapp this otp to 9876543210 for ticket confirmation. |
| 3 | BANKING_FRAUD | 0.3247 | hdfc bank: your account credited ₹1,00,000. verify otp 784321 to reverse if incorrect. |

## Model: `tfidf_lr`

### False Positives (4 — Legit flagged as Scam)

**Categories affected:**
- LEGITIMATE_GOVERNMENT: 2
- LEGITIMATE_OTHER: 2

**Avg Confidence:** 0.6165

**Top FP Examples:**

| # | Category | Confidence | Text (truncated) |
| - | -------- | ---------: | ---------------- |
| 1 | LEGITIMATE_GOVERNMENT | 0.6135 | uidai: your aadhaar update request ar1234567890 has been processed. check status at uidai.gov.in |
| 2 | LEGITIMATE_OTHER | 0.6031 | library reminder: the book 'wings of fire' is due for return by 25th march. late fee applies after t |
| 3 | LEGITIMATE_GOVERNMENT | 0.5542 | voter helpline: your voter id application e1234567 has been approved. card will be delivered shortly |
| 4 | LEGITIMATE_OTHER | 0.6951 | linkedin: john doe sent you a connection request. view profile: https://linkedin.com/in/johndoe |

### False Negatives (3 — Scam flagged as Safe)

**Categories affected:**
- TELECOM_SCAM: 2
- UPI_FRAUD: 1

**Avg Confidence:** 0.4639

**Top FN Examples:**

| # | Category | Confidence | Text (truncated) |
| - | -------- | ---------: | ---------------- |
| 1 | TELECOM_SCAM | 0.4822 | netflix: your otp is 638192. share with our support agent for account recovery. do not ignore. |
| 2 | TELECOM_SCAM | 0.4391 | irctc: your booking otp is 719283. whatsapp this otp to 9876543210 for ticket confirmation. |
| 3 | UPI_FRAUD | 0.4702 | ₹49,500 credited by mistake. return via upi: 9876543210@paytm. don't share with bank. |

## Model: `tfidf_svm`

### False Positives (4 — Legit flagged as Scam)

**Categories affected:**
- LEGITIMATE_GOVERNMENT: 2
- LEGITIMATE_OTHER: 2

**Avg Confidence:** 0.6040

**Top FP Examples:**

| # | Category | Confidence | Text (truncated) |
| - | -------- | ---------: | ---------------- |
| 1 | LEGITIMATE_GOVERNMENT | 0.6003 | uidai: your aadhaar update request ar1234567890 has been processed. check status at uidai.gov.in |
| 2 | LEGITIMATE_OTHER | 0.5785 | library reminder: the book 'wings of fire' is due for return by 25th march. late fee applies after t |
| 3 | LEGITIMATE_GOVERNMENT | 0.5504 | voter helpline: your voter id application e1234567 has been approved. card will be delivered shortly |
| 4 | LEGITIMATE_OTHER | 0.6868 | linkedin: john doe sent you a connection request. view profile: https://linkedin.com/in/johndoe |

### False Negatives (1 — Scam flagged as Safe)

**Categories affected:**
- UPI_FRAUD: 1

**Avg Confidence:** 0.4846

**Top FN Examples:**

| # | Category | Confidence | Text (truncated) |
| - | -------- | ---------: | ---------------- |
| 1 | UPI_FRAUD | 0.4846 | ₹49,500 credited by mistake. return via upi: 9876543210@paytm. don't share with bank. |

## Root Cause Analysis

### Which scam categories are most frequently missed?

| Category | FN Cross-Model Count | Likely Cause |
| -------- | -------------------: | ------------ |
| AADHAAR_SCAM | 0 | Well-classified |
| BANKING_FRAUD | 1 | Small sample size |
| COURIER_SCAM | 0 | Well-classified |
| CRYPTO_SCAM | 0 | Well-classified |
| DIGITAL_ARREST | 0 | Well-classified |
| ELECTRICITY_BILL_SCAM | 0 | Well-classified |
| FAKE_CUSTOMER_CARE | 0 | Well-classified |
| GOVERNMENT_IMPERSONATION | 0 | Well-classified |
| INCOME_TAX_SCAM | 0 | Well-classified |
| INVESTMENT_SCAM | 0 | Well-classified |
| JOB_SCAM | 0 | Well-classified |
| KYC_SCAM | 0 | Well-classified |
| LOAN_SCAM | 0 | Well-classified |
| LOTTERY_SCAM | 0 | Well-classified |
| PAN_SCAM | 0 | Well-classified |
| QR_SCAM | 0 | Well-classified |
| ROMANCE_SCAM | 0 | Well-classified |
| TELECOM_SCAM | 4 | High lexical overlap with legitimate messages |
| UPI_FRAUD | 2 | Small sample size |

### Which legitimate categories are most frequently misclassified?

| Category | FP Cross-Model Count | Likely Cause |
| -------- | -------------------: | ------------ |
| LEGITIMATE_BANKING | 0 | Well-classified |
| LEGITIMATE_COURIER | 0 | Well-classified |
| LEGITIMATE_GOVERNMENT | 5 | Contains financial/government keywords that overlap with scam vocabulary |
| LEGITIMATE_OTHER | 5 | Contains financial/other keywords that overlap with scam vocabulary |
| LEGITIMATE_OTP | 0 | Well-classified |
| LEGITIMATE_UPI | 0 | Well-classified |

### Categories needing more data

| Category | Samples | Issue |
| -------- | ------: | ----- |
| PAN_SCAM | 2 | Very low support — unreliable metrics |
| INCOME_TAX_SCAM | 4 | Very low support — unreliable metrics |
| DIGITAL_ARREST | 5 | Very low support — unreliable metrics |
| ROMANCE_SCAM | 7 | Very low support — unreliable metrics |
| LEGITIMATE_UPI | 7 | Very low support — unreliable metrics |
| LEGITIMATE_COURIER | 7 | Very low support — unreliable metrics |
| LEGITIMATE_OTP | 7 | Very low support — unreliable metrics |
| CRYPTO_SCAM | 7 | Very low support — unreliable metrics |
| LEGITIMATE_GOVERNMENT | 8 | Very low support — unreliable metrics |
| LEGITIMATE_BANKING | 9 | Very low support — unreliable metrics |
| QR_SCAM | 11 | Very low support — unreliable metrics |
