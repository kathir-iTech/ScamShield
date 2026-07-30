# Error Analysis: Gold Dataset

**Total errors:** 43 / 308 (14.0%)

## False Positives (Legitimate flagged as Scam)

**Count:** 19

| Text | Category | Confidence |
|------|----------|------------|
| Please send me the photos from yesterday's party. Thanks! | LEGITIMATE_PERSONAL | 0.685 |
| Delhi University: Fee payment for semester 3 of Rs 25,000 is due by 15 Aug. Pay  | LEGITIMATE_COLLEGE | 0.677 |
| Airtel: Your data usage is 90% of 2GB/day limit. Top up at http://airtel.in | LEGITIMATE_TELECOM | 0.675 |
| VIT Vellore: Campus placement drive on 5 Aug. Register at http://vit-placement.i | LEGITIMATE_COLLEGE | 0.669 |
| Ecom Express: Delivery attempted but address not found. Update location: http:// | LEGITIMATE_COURIER | 0.659 |
| UPSC: Your civil services prelims result published. Check at http://upsc.gov.in | LEGITIMATE_COLLEGE | 0.655 |
| Can you pick up milk and bread on your way back home? | LEGITIMATE_PERSONAL | 0.639 |
| TRAI: Do not disturb registered. You will not receive promotional calls. | LEGITIMATE_TELECOM | 0.634 |
| Dinner tonight at 8? I'll book the restaurant. Let me know. | LEGITIMATE_PERSONAL | 0.615 |
| Hey mom, I reached the hostel safely. Will call you in the evening. | LEGITIMATE_PERSONAL | 0.572 |
| Your broadband bill of Rs 999 is due on 5 Aug. Auto-pay enabled. | LEGITIMATE_UTILITY | 0.564 |
| PhonePe: Your gold purchase of Rs 500 successful via Digital Gold. | LEGITIMATE_UPI | 0.563 |
| Your car service is due at 15,000 km. Book appointment at Maruti service center. | LEGITIMATE_PERSONAL | 0.561 |
| Happy birthday! Wishing you a wonderful year ahead. - Rahul | LEGITIMATE_PERSONAL | 0.548 |
| BSNL: Your FTTH plan auto-renewed for Rs 799. Next billing: 28 August. | LEGITIMATE_TELECOM | 0.538 |
| I'll be late today. Stuck in traffic near Silk Board. | LEGITIMATE_PERSONAL | 0.527 |
| GPay: Your weekly transaction summary: 12 payments totalling Rs 8,750. | LEGITIMATE_UPI | 0.519 |
| Axis Bank: Reward points earned this month: 2,450. Redeem via Axis Rewards porta | LEGITIMATE_BANKING | 0.506 |
| Flight AI 202 to Delhi is on time. Boarding at Gate 12 at 6:30 PM. | LEGITIMATE_PERSONAL | 0.502 |

**FP by Category:**

- LEGITIMATE_PERSONAL: 8
- LEGITIMATE_TELECOM: 3
- LEGITIMATE_COLLEGE: 3
- LEGITIMATE_UPI: 2
- LEGITIMATE_BANKING: 1
- LEGITIMATE_COURIER: 1
- LEGITIMATE_UTILITY: 1

## False Negatives (Scam flagged as Legitimate)

**Count:** 24

| Text | Category | Confidence |
|------|----------|------------|
| Mee Amazon order dispatch ayindi. Track cheyandi. | LEGITIMATE_SHOPPING | 0.135 |
| Amazon order dispatch aagirukku. Track pannugal. | LEGITIMATE_SHOPPING | 0.192 |
| Aapka Flipkart order dispatch ho gaya hai. Track karo yahan. | LEGITIMATE_SHOPPING | 0.217 |
| IRCTC: OTP 945612 for booking cancellation of PNR 4567890123. Not you? Contact s | OTP_SCAM | 0.300 |
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.313 |
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.313 |
| Mobile recharge Rs 599 successful. Plan valid 84 days. | LEGITIMATE_TELECOM | 0.313 |
| UPI se Rs 2,000 Rahul ko bheje gaye. Ref: 7890123456. | LEGITIMATE_UPI | 0.320 |
| GPay lo Rs 2,000 Rahul ki pampiyaru. Ref: 7890123456. | LEGITIMATE_UPI | 0.325 |
| Canara Bank: Your cheque book ordered successfully. Delivery tracking: http://ca | BANKING_FRAUD | 0.325 |
| Your BHIM UPI account is credited with Rs 5,000. Thanks for using Digital India! | UPI_FRAUD | 0.327 |
| Amazon order deliver aachu. Rating kudungal. | LEGITIMATE_SHOPPING | 0.327 |
| Amazon order deliver ayindi. Rating ivvandi. | LEGITIMATE_SHOPPING | 0.327 |
| Telegram: Login OTP 782345. Someone is trying to access your account from Hydera | OTP_SCAM | 0.328 |
| Axis Bank: Your account has been credited with Rs 75,000 from unknown source. Re | BANKING_FRAUD | 0.364 |
| Amazon ka order deliver ho gaya. Rating do please. | LEGITIMATE_SHOPPING | 0.367 |
| UPI transaction of Rs 7,450 to unknown beneficiary detected from your PhonePe. R | UPI_FRAUD | 0.394 |
| Your Google verification code is 482916. Do not share this code with anyone. If  | OTP_SCAM | 0.403 |
| SBI OTP 891234 for transfer of Rs 45,000 to account XX6789. If not authorised, c | OTP_SCAM | 0.430 |
| GPay la Rs 2,000 Rahul ku anupirukkom. Ref: 7890123456. | LEGITIMATE_UPI | 0.439 |
| GPay lo Rs 5,000 transaction jarigindi. Not you? Call now. | UPI_FRAUD | 0.440 |
| LinkedIn: Your account will be restricted due to policy violation. Appeal at htt | FAKE_CUSTOMER_CARE | 0.441 |
| Tez UPI collect request from merchant 'ShopEasy': Rs 12,500. Approve? Reply Y or | UPI_FRAUD | 0.488 |
| GPay transaction OTP: 623489. Amount: Rs 12,500 to Paytm merchant. Not you? Bloc | OTP_SCAM | 0.500 |

**FN by Category:**

- LEGITIMATE_SHOPPING: 6
- OTP_SCAM: 5
- UPI_FRAUD: 4
- LEGITIMATE_UPI: 3
- LEGITIMATE_TELECOM: 3
- BANKING_FRAUD: 2
- FAKE_CUSTOMER_CARE: 1

## Weak Categories

### Scam Categories (F1 < 0.80)

- **OTP_SCAM**: F1=0.5455, n=8

### Legitimate Categories (F1_legit < 0.80)

- **LEGITIMATE_TELECOM**: F1_legit=0.6667, n=15
- **LEGITIMATE_PERSONAL**: F1_legit=0.6923, n=20
- **LEGITIMATE_COLLEGE**: F1_legit=0.7692, n=8
- **LEGITIMATE_UPI**: F1_legit=0.7826, n=14

## Language-Specific Failures

- **en**: 248 samples, 30 errors (F1=0.8986)
- **hi-en**: 21 samples, 4 errors (F1=0.8947)
- **ta-en**: 20 samples, 4 errors (F1=0.8889)
- **te-en**: 19 samples, 5 errors (F1=0.8485)

## Recommendations

### Dataset Improvements

- **FP categories to augment:** Add more diverse samples for LEGITIMATE_PERSONAL (8), LEGITIMATE_TELECOM (3), LEGITIMATE_COLLEGE (3), LEGITIMATE_UPI (2), LEGITIMATE_BANKING (1)
- **FN categories to augment:** Add more scam variants for LEGITIMATE_SHOPPING (6), OTP_SCAM (5), UPI_FRAUD (4), LEGITIMATE_UPI (3), LEGITIMATE_TELECOM (3)
- **Weak scam categories**: Focus on OTP_SCAM
- **Weak legitimate categories**: Focus on LEGITIMATE_COLLEGE, LEGITIMATE_PERSONAL, LEGITIMATE_TELECOM, LEGITIMATE_UPI
- **Non-English data**: Expand hi-en (4 errors in 21 samples), ta-en (4 errors in 20 samples), te-en (5 errors in 19 samples), 

### Model Improvements (if justified)

- **SVM + CalibratedClassifierCV**: Test if probability calibration improves AUC
- **Model retrain** may be warranted if error rate exceeds 10% on growing gold dataset
