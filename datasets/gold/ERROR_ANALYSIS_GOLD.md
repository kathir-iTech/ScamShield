# Error Analysis: Gold Dataset

**Total errors:** 21 / 308 (6.8%)

## False Positives (Legitimate flagged as Scam)

**Count:** 3

| Text | Category | Confidence |
|------|----------|------------|
| Ecom Express: Delivery attempted but address not found. Update location: http:// | LEGITIMATE_COURIER | 0.638 |
| GPay: OTP 746281 for sending money to new contact. Do not share. | LEGITIMATE_OTP | 0.585 |
| Happy birthday! Wishing you a wonderful year ahead. - Rahul | LEGITIMATE_PERSONAL | 0.500 |

**FP by Category:**

- LEGITIMATE_COURIER: 1
- LEGITIMATE_OTP: 1
- LEGITIMATE_PERSONAL: 1

## False Negatives (Scam flagged as Legitimate)

**Count:** 18

| Text | Category | Confidence |
|------|----------|------------|
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.139 |
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.139 |
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.139 |
| Repu dinner 8 ki. Restaurant book chesanu. | LEGITIMATE_PERSONAL | 0.212 |
| Indru dinner 8 manikku. Restaurant book panniten. | LEGITIMATE_PERSONAL | 0.228 |
| Aaj dinner 8 baje. Restaurant book kar liya hai. | LEGITIMATE_PERSONAL | 0.237 |
| Amazon order dispatch aagirukku. Track pannugal. | LEGITIMATE_SHOPPING | 0.262 |
| Amazon order deliver ayindi. Rating ivvandi. | LEGITIMATE_SHOPPING | 0.271 |
| Amazon order deliver aachu. Rating kudungal. | LEGITIMATE_SHOPPING | 0.299 |
| Amazon ka order deliver ho gaya. Rating do please. | LEGITIMATE_SHOPPING | 0.325 |
| Telegram: Login OTP 782345. Someone is trying to access your account from Hydera | OTP_SCAM | 0.346 |
| Canara Bank: Your cheque book ordered successfully. Delivery tracking: http://ca | BANKING_FRAUD | 0.357 |
| Mee Amazon order dispatch ayindi. Track cheyandi. | LEGITIMATE_SHOPPING | 0.395 |
| Your BHIM UPI account is credited with Rs 5,000. Thanks for using Digital India! | UPI_FRAUD | 0.400 |
| Aapka Flipkart order dispatch ho gaya hai. Track karo yahan. | LEGITIMATE_SHOPPING | 0.415 |
| Axis Bank: Your account has been credited with Rs 75,000 from unknown source. Re | BANKING_FRAUD | 0.455 |
| NCB Delhi: A parcel with 3kg MDMA is booked in your name. You are under narcotic | DIGITAL_ARREST | 0.479 |
| GPay lo Rs 2,000 Rahul ki pampiyaru. Ref: 7890123456. | LEGITIMATE_UPI | 0.482 |

**FN by Category:**

- LEGITIMATE_SHOPPING: 6
- LEGITIMATE_PERSONAL: 3
- LEGITIMATE_TELECOM: 3
- BANKING_FRAUD: 2
- UPI_FRAUD: 1
- OTP_SCAM: 1
- DIGITAL_ARREST: 1
- LEGITIMATE_UPI: 1

## Weak Categories


## Language-Specific Failures

- **en**: 248 samples, 8 errors (F1=0.9720)
- **hi-en**: 21 samples, 4 errors (F1=0.8947)
- **ta-en**: 20 samples, 4 errors (F1=0.8889)
- **te-en**: 19 samples, 5 errors (F1=0.8485)

## Recommendations

### Dataset Improvements

- **FP categories to augment:** Add more diverse samples for LEGITIMATE_COURIER (1), LEGITIMATE_OTP (1), LEGITIMATE_PERSONAL (1)
- **FN categories to augment:** Add more scam variants for LEGITIMATE_SHOPPING (6), LEGITIMATE_PERSONAL (3), LEGITIMATE_TELECOM (3), BANKING_FRAUD (2), UPI_FRAUD (1)
- **Non-English data**: Expand hi-en (4 errors in 21 samples), ta-en (4 errors in 20 samples), te-en (5 errors in 19 samples), 

### Model Improvements (if justified)

- **SVM + CalibratedClassifierCV**: Test if probability calibration improves AUC
