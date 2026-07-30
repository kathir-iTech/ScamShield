# Error Analysis: Gold Dataset

**Total errors:** 28 / 308 (9.1%)

## False Positives (Legitimate flagged as Scam)

**Count:** 3

| Text | Category | Confidence |
|------|----------|------------|
| Ecom Express: Delivery attempted but address not found. Update location: http:// | LEGITIMATE_COURIER | 0.636 |
| PhonePe: Your gold purchase of Rs 500 successful via Digital Gold. | LEGITIMATE_UPI | 0.534 |
| GPay: OTP 746281 for sending money to new contact. Do not share. | LEGITIMATE_OTP | 0.520 |

**FP by Category:**

- LEGITIMATE_COURIER: 1
- LEGITIMATE_OTP: 1
- LEGITIMATE_UPI: 1

## False Negatives (Scam flagged as Legitimate)

**Count:** 25

| Text | Category | Confidence |
|------|----------|------------|
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.128 |
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.128 |
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.128 |
| Amazon order dispatch aagirukku. Track pannugal. | LEGITIMATE_SHOPPING | 0.133 |
| Mee Amazon order dispatch ayindi. Track cheyandi. | LEGITIMATE_SHOPPING | 0.165 |
| Amazon order deliver aachu. Rating kudungal. | LEGITIMATE_SHOPPING | 0.205 |
| Amazon order deliver ayindi. Rating ivvandi. | LEGITIMATE_SHOPPING | 0.205 |
| Aaj dinner 8 baje. Restaurant book kar liya hai. | LEGITIMATE_PERSONAL | 0.214 |
| Aapka Flipkart order dispatch ho gaya hai. Track karo yahan. | LEGITIMATE_SHOPPING | 0.219 |
| Repu dinner 8 ki. Restaurant book chesanu. | LEGITIMATE_PERSONAL | 0.226 |
| Indru dinner 8 manikku. Restaurant book panniten. | LEGITIMATE_PERSONAL | 0.230 |
| GPay lo Rs 2,000 Rahul ki pampiyaru. Ref: 7890123456. | LEGITIMATE_UPI | 0.286 |
| Amazon ka order deliver ho gaya. Rating do please. | LEGITIMATE_SHOPPING | 0.291 |
| UPI se Rs 2,000 Rahul ko bheje gaye. Ref: 7890123456. | LEGITIMATE_UPI | 0.324 |
| GPay la Rs 2,000 Rahul ku anupirukkom. Ref: 7890123456. | LEGITIMATE_UPI | 0.329 |
| Canara Bank: Your cheque book ordered successfully. Delivery tracking: http://ca | BANKING_FRAUD | 0.331 |
| Airtel: Ungal recharge plan expire aaga irukku. Renew pannugal. | LEGITIMATE_TELECOM | 0.356 |
| Telegram: Login OTP 782345. Someone is trying to access your account from Hydera | OTP_SCAM | 0.359 |
| Airtel: Mee recharge plan expire avutundi. Renew chesukondi. | LEGITIMATE_TELECOM | 0.365 |
| Airtel: Aapka recharge plan expire hone wala hai. Renew karo app se. | LEGITIMATE_TELECOM | 0.404 |
| Your BHIM UPI account is credited with Rs 5,000. Thanks for using Digital India! | UPI_FRAUD | 0.412 |
| Amazon order return ayindi. Refund ki bank details update cheyandi. | FAKE_CUSTOMER_CARE | 0.429 |
| Axis Bank: Your account has been credited with Rs 75,000 from unknown source. Re | BANKING_FRAUD | 0.444 |
| LinkedIn: Your account will be restricted due to policy violation. Appeal at htt | FAKE_CUSTOMER_CARE | 0.483 |
| Aapka Amazon order return ho gaya hai. Refund ke liye bank details update karo. | FAKE_CUSTOMER_CARE | 0.495 |

**FN by Category:**

- LEGITIMATE_TELECOM: 6
- LEGITIMATE_SHOPPING: 6
- FAKE_CUSTOMER_CARE: 3
- LEGITIMATE_UPI: 3
- LEGITIMATE_PERSONAL: 3
- BANKING_FRAUD: 2
- UPI_FRAUD: 1
- OTP_SCAM: 1

## Weak Categories


### Legitimate Categories (F1_legit < 0.80)

- **LEGITIMATE_TELECOM**: F1_legit=0.7500, n=15

## Language-Specific Failures

- **en**: 248 samples, 8 errors (F1=0.9720)
- **hi-en**: 21 samples, 7 errors (F1=0.8000)
- **ta-en**: 20 samples, 6 errors (F1=0.8235)
- **te-en**: 19 samples, 7 errors (F1=0.7742)

## Recommendations

### Dataset Improvements

- **FP categories to augment:** Add more diverse samples for LEGITIMATE_COURIER (1), LEGITIMATE_OTP (1), LEGITIMATE_UPI (1)
- **FN categories to augment:** Add more scam variants for LEGITIMATE_TELECOM (6), LEGITIMATE_SHOPPING (6), FAKE_CUSTOMER_CARE (3), LEGITIMATE_UPI (3), LEGITIMATE_PERSONAL (3)
- **Weak legitimate categories**: Focus on LEGITIMATE_TELECOM
- **Non-English data**: Expand hi-en (7 errors in 21 samples), ta-en (6 errors in 20 samples), te-en (7 errors in 19 samples), 

### Model Improvements (if justified)

- **SVM + CalibratedClassifierCV**: Test if probability calibration improves AUC
