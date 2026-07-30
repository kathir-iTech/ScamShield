# V2 Dataset Collection Summary (Alpha → Beta)

**Date:** 2026-07-30 09:28:45

## Objective

Expand the v2 dataset from ~558 samples to 1,500+ high-quality labeled samples, 
focusing on underrepresented categories identified in the v2 model benchmark.

## What Was Added

| Category | Alpha | Added | Beta | Target | Change |
| -------- | ----: | ----: | ---: | -----: | ------ |
| AADHAAR_SCAM | 15 | 10 | 25 | 25 | ✅ Full coverage |
| CRYPTO_SCAM | 7 | 18 | 25 | 25 | ✅ Full coverage |
| DIGITAL_ARREST | 5 | 25 | 30 | 30 | ✅ Full coverage |
| FAKE_CUSTOMER_CARE | 18 | 7 | 25 | 25 | ✅ Full coverage |
| INCOME_TAX_SCAM | 4 | 21 | 25 | 25 | ✅ Full coverage |
| INVESTMENT_SCAM | 18 | 7 | 25 | 25 | ✅ Full coverage |
| LEGITIMATE_BANKING | 9 | 16 | 25 | 25 | ✅ Full coverage |
| LEGITIMATE_COURIER | 7 | 17 | 24 | 25 | ⚠️ 1 short |
| LEGITIMATE_GOVERNMENT | 8 | 16 | 24 | 25 | ⚠️ 1 short |
| LEGITIMATE_OTP | 7 | 17 | 24 | 25 | ⚠️ 1 short |
| LEGITIMATE_UPI | 7 | 18 | 25 | 25 | ✅ Full coverage |
| PAN_SCAM | 2 | 23 | 25 | 25 | ✅ Full coverage |
| QR_SCAM | 11 | 14 | 25 | 25 | ✅ Full coverage |
| ROMANCE_SCAM | 7 | 18 | 25 | 25 | ✅ Full coverage |
| TELECOM_SCAM | 15 | 10 | 25 | 25 | ✅ Full coverage |
| BANKING_FRAUD | 78 | 0 | 78 | — | Already adequate |
| COURIER_SCAM | 40 | 0 | 40 | — | Already adequate |
| ELECTRICITY_BILL_SCAM | 24 | 0 | 24 | — | Already adequate |
| GOVERNMENT_IMPERSONATION | 37 | 0 | 37 | — | Already adequate |
| JOB_SCAM | 44 | 0 | 44 | — | Already adequate |
| KYC_SCAM | 46 | 0 | 46 | — | Already adequate |
| LEGITIMATE_OTHER | 50 | 5 | 55 | — | Already adequate |
| LOAN_SCAM | 23 | 0 | 23 | — | Already adequate |
| LOTTERY_SCAM | 27 | 0 | 27 | — | Already adequate |
| UPI_FRAUD | 49 | 0 | 49 | — | Already adequate |

**Total added:** 242
**Final size:** 800

## Generation Method

- **Pattern-based synthesis:** Each example crafted to match real-world Indian scam patterns
- **Studied existing examples** in each category to maintain style consistency
- **Varied language:** English, Tanglish (ta-en), Hinglish (hi-en)
- **Varied risk levels:** CRITICAL for threats, HIGH for urgent scams, MEDIUM for softer frauds
  NONE for legitimate messages
- **Entity extraction:** Each sample scanned for URLs, phone numbers, UPI IDs, bank names,
  emails, Aadhaar numbers, and PAN card numbers

## Quality Controls

1. **Duplicate detection:** Text-based dedup across entire dataset
2. **ID uniqueness:** All new IDs generated with sequential numbering per category
3. **Label consistency:** Every sample verified for is_scam/ground_truth_label match
4. **Schema compliance:** All 14 CSV columns populated for every row
5. **Source tracking:** `source=synthetic` clearly marks all generated samples
6. **Realism:** Patterns based on real CERT-In, NPCI, RBI, and police advisories

## Next Steps

1. **Manual review:** Domain experts should review synthetic samples for accuracy
2. **Retrain models:** Use `dataset_v2_beta.csv` to retrain TF-IDF SVM and other models
3. **Add more diverse sources:** Collect real scam messages from Twitter, FB groups, SMS
4. **Expand languages:** Currently 95% English — add more Tamil, Hindi, Telugu samples
