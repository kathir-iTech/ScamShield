# Error Analysis: Gold Dataset

**Total errors:** 15 / 308 (4.9%)

## False Positives (Legitimate flagged as Scam)

**Count:** 2

| Text | Category | Confidence |
|------|----------|------------|
| Ecom Express: Delivery attempted but address not found. Update location: http:// | LEGITIMATE_COURIER | 0.631 |
| GPay: OTP 746281 for sending money to new contact. Do not share. | LEGITIMATE_OTP | 0.571 |

**FP by Category:**

- LEGITIMATE_COURIER: 1
- LEGITIMATE_OTP: 1

## False Negatives (Scam flagged as Legitimate)

**Count:** 13

| Text | Category | Confidence |
|------|----------|------------|
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.296 |
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.296 |
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.296 |
| Amazon order dispatch aagirukku. Track pannugal. | LEGITIMATE_SHOPPING | 0.346 |
| Amazon order deliver ayindi. Rating ivvandi. | LEGITIMATE_SHOPPING | 0.360 |
| Repu dinner 8 ki. Restaurant book chesanu. | LEGITIMATE_PERSONAL | 0.392 |
| Amazon order deliver aachu. Rating kudungal. | LEGITIMATE_SHOPPING | 0.397 |
| Your BHIM UPI account is credited with Rs 5,000. Thanks for using Digital India! | UPI_FRAUD | 0.429 |
| Telegram: Login OTP 782345. Someone is trying to access your account from Hydera | OTP_SCAM | 0.432 |
| Aaj dinner 8 baje. Restaurant book kar liya hai. | LEGITIMATE_PERSONAL | 0.435 |
| Canara Bank: Your cheque book ordered successfully. Delivery tracking: http://ca | BANKING_FRAUD | 0.441 |
| GPay lo Rs 2,000 Rahul ki pampiyaru. Ref: 7890123456. | LEGITIMATE_UPI | 0.444 |
| Indru dinner 8 manikku. Restaurant book panniten. | LEGITIMATE_PERSONAL | 0.499 |

**FN by Category:**

- LEGITIMATE_PERSONAL: 3
- LEGITIMATE_TELECOM: 3
- LEGITIMATE_SHOPPING: 3
- UPI_FRAUD: 1
- BANKING_FRAUD: 1
- OTP_SCAM: 1
- LEGITIMATE_UPI: 1

## Weak Categories


## Language-Specific Failures

- **en**: 248 samples, 5 errors (F1=0.9826)
- **hi-en**: 21 samples, 2 errors (F1=0.9500)
- **ta-en**: 20 samples, 4 errors (F1=0.8889)
- **te-en**: 19 samples, 4 errors (F1=0.8824)

## Recommendations

### Dataset Improvements

- **FP categories to augment:** Add more diverse samples for LEGITIMATE_COURIER (1), LEGITIMATE_OTP (1)
- **FN categories to augment:** Add more scam variants for LEGITIMATE_PERSONAL (3), LEGITIMATE_TELECOM (3), LEGITIMATE_SHOPPING (3), UPI_FRAUD (1), BANKING_FRAUD (1)
- **Non-English data**: Expand hi-en (2 errors in 21 samples), ta-en (4 errors in 20 samples), te-en (4 errors in 19 samples), 

### Model Improvements (if justified)

- **SVM + CalibratedClassifierCV**: Test if probability calibration improves AUC
