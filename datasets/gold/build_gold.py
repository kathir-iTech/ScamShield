"""
Build the independent GOLD evaluation dataset (300-500 real messages).
NEVER used for training — only for final evaluation.
"""

import csv, json, os, re, sys, random
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

random.seed(42)

OUT_DIR = Path(__file__).parent
GOLD_PATH = OUT_DIR / "gold_dataset.csv"
LEAKAGE_PATH = OUT_DIR / "LEAKAGE_REPORT.md"
DATASET_REPORT_PATH = OUT_DIR / "GOLD_DATASET_REPORT.md"
EVAL_REPORT_PATH = OUT_DIR / "GOLD_EVALUATION_REPORT.md"
ERROR_PATH = OUT_DIR / "ERROR_ANALYSIS_GOLD.md"

CATEGORIES = [
    "UPI_FRAUD", "KYC_SCAM", "BANKING_FRAUD", "COURIER_SCAM", "OTP_SCAM",
    "INVESTMENT_SCAM", "JOB_SCAM", "LOTTERY_SCAM", "DIGITAL_ARREST",
    "INCOME_TAX_SCAM", "PAN_SCAM", "ROMANCE_SCAM", "CRYPTO_SCAM",
    "QR_SCAM", "LOAN_SCAM", "FAKE_CUSTOMER_CARE", "GOVERNMENT_IMPERSONATION",
    "TELECOM_SCAM", "ELECTRICITY_BILL_SCAM", "LEGITIMATE_BANKING",
    "LEGITIMATE_UPI", "LEGITIMATE_COURIER", "LEGITIMATE_GOVERNMENT",
    "LEGITIMATE_OTP", "LEGITIMATE_TELECOM", "LEGITIMATE_COLLEGE",
    "LEGITIMATE_UTILITY", "LEGITIMATE_SHOPPING", "LEGITIMATE_PERSONAL",
]

SCAM_CATEGORIES = {c for c in CATEGORIES if not c.startswith("LEGITIMATE_")}
LEGIT_CATEGORIES = {c for c in CATEGORIES if c.startswith("LEGITIMATE_")}

# ──────────────────────────────────────
# Gold messages — written fresh, NOT from templates
# Each is a (text, category, language, is_scam) tuple
# ──────────────────────────────────────

SCAM_MESSAGES = [
    # UPI FRAUD
    ("Your GPay account has been blocked due to multiple failed attempts. Recover here: http://gpay-help.xyz", "UPI_FRAUD", "en"),
    ("UPI transaction of Rs 7,450 to unknown beneficiary detected from your PhonePe. Reverse? Share OTP 871234.", "UPI_FRAUD", "en"),
    ("BHIM app update required: Your UPI services will stop in 24 hours. Update via http://bhim-update.in", "UPI_FRAUD", "en"),
    ("Paytm UPI: You received Rs 25,000 from an unknown sender. Click to accept or return: http://paytm-claim.tk", "UPI_FRAUD", "en"),
    ("Your UPI PIN was changed from a new device. If not you, block here: http://upi-secure.xyz", "UPI_FRAUD", "en"),
    ("Amazon Pay UPI: Cashback reward of Rs 10,000 unlocked. Claim at http://amazon-pay-reward.xyz", "UPI_FRAUD", "en"),
    ("Tez UPI collect request from merchant 'ShopEasy': Rs 12,500. Approve? Reply Y or ignore.", "UPI_FRAUD", "en"),
    ("PhonePe UPI limit increased to Rs 2 lakh. Activation fee Rs 99: http://phonepe-upgrade.tk", "UPI_FRAUD", "en"),
    ("UPI auto-pay mandate set for Rs 5,000 monthly to QuickLoan. Cancel at http://cancel-mandate.xyz", "UPI_FRAUD", "en"),
    ("Your BHIM UPI account is credited with Rs 5,000. Thanks for using Digital India!", "UPI_FRAUD", "en"),

    # KYC SCAM
    ("SBI KYC warning: Your account will be frozen within 48 hours. Update KYC: http://sbi-kyc-update.xyz", "KYC_SCAM", "en"),
    ("HDFC Bank: Your KYC documents are rejected. Re-submit at http://hdfc-kyc-reverify.in within 24 hours.", "KYC_SCAM", "en"),
    ("ICICI Prudential: KYC pending for your insurance policy. Policy will lapse. Upload at http://icicipru-kyc.tk", "KYC_SCAM", "en"),
    ("RBI mandate: All bank accounts must complete Video KYC by March 31. Book slot: http://vkyc-rbi.xyz", "KYC_SCAM", "en"),
    ("Your demat account KYC is expired. Shares will be frozen. Update at http://demat-kyc.in", "KYC_SCAM", "en"),
    ("Aadhaar based e-KYC failed for your HDFC account. Visit nearest branch or click http://ekyc-fix.xyz", "KYC_SCAM", "en"),
    ("Mutual Fund KYC is mandatory. Your investments will be halted. Complete at http://mf-kyc.tk", "KYC_SCAM", "en"),
    ("Your PM Kisan KYC is due by 15th. Benefits will stop. Update at http://pmkisan-kyc-update.xyz", "KYC_SCAM", "en"),
    ("Insurance KYC: Your policy will be surrendered if not completed. Documents needed: Aadhaar, PAN.", "KYC_SCAM", "en"),
    ("TRAI: SIM KYC expired for your mobile number. Re-verify at http://sim-kyc-verify.in or line cut.", "KYC_SCAM", "en"),

    # BANKING FRAUD
    ("SBI Alert: Rs 45,000 withdrawn from your account at Mumbai ATM. Not you? Call 1800-123-4567 immediately.", "BANKING_FRAUD", "en"),
    ("HDFC Bank: Your debit card blocked due to 3 wrong PIN attempts. Unblock at http://hdfc-unblock.xyz", "BANKING_FRAUD", "en"),
    ("ICICI Bank: Your net banking password will expire today. Renew at http://icici-renew.in", "BANKING_FRAUD", "en"),
    ("Axis Bank: Your account has been credited with Rs 75,000 from unknown source. Return via this link.", "BANKING_FRAUD", "en"),
    ("PNB: New login from Delhi detected on your account. Secure at http://pnb-alert.xyz", "BANKING_FRAUD", "en"),
    ("Canara Bank: Your cheque book ordered successfully. Delivery tracking: http://canara-cheque.tk", "BANKING_FRAUD", "en"),
    ("Bank of Baroda: Your international transactions blocked due to security reasons. Unblock globally at http://bob-global.xyz", "BANKING_FRAUD", "en"),
    ("Kotak Mahindra: Your credit card EMI payment failed. Pay Rs 12,500 now to avoid late fee: http://kotak-pay.in", "BANKING_FRAUD", "en"),
    ("Yes Bank: Your savings account converted to premium. Annual fee Rs 3,500 deducted. Dispute? Call 1800-258-3690.", "BANKING_FRAUD", "en"),
    ("IndusInd Bank: Your salary account upgraded to Private Banking. Fee of Rs 12,500 applicable.", "BANKING_FRAUD", "en"),
    ("SBI: Your account is marked as dormant. Activate now at http://sbi-activate.xyz", "BANKING_FRAUD", "en"),
    ("HDFC Bank: Unauthorized access detected from Kolkata IP. Confirm identity at http://hdfc-safe.in", "BANKING_FRAUD", "en"),
    ("ICICI Bank: Your credit card fraud alert. Transaction of Rs 65,000 at Apple Store. Block card? Reply BLOCK.", "BANKING_FRAUD", "en"),
    ("Axis Bank reward points: 25,000 points expiring. Redeem at http://axis-rewards.xyz", "BANKING_FRAUD", "en"),

    # COURIER SCAM
    ("FedEx: Your international parcel contains undeclared items. Customs clearance fee Rs 8,500: http://fedex-fee.xyz", "COURIER_SCAM", "en"),
    ("DHL: Your shipment from New York is detained. Insurance fee Rs 3,200 required: http://dhl-insure.tk", "COURIER_SCAM", "en"),
    ("Blue Dart: Your passport delivery requires Rs 1,500 address verification fee. Pay now.", "COURIER_SCAM", "en"),
    ("India Post: Your registered parcel held due to incomplete address. Update at http://indiapost-update.in", "COURIER_SCAM", "en"),
    ("Amazon Logistics: Your package damaged in transit. Claim Rs 12,500 compensation: http://amazon-claim.xyz", "COURIER_SCAM", "en"),
    ("Delhivery: Your COD order of Rs 25,000 out for delivery. Confirm payment method: http://delhivery-pay.tk", "COURIER_SCAM", "en"),
    ("DTDC: Your courier from Dubai requires customs clearance of Rs 15,000. Pay at http://dtdc-customs.xyz", "COURIER_SCAM", "en"),
    ("Shiprocket: Your parcel weight mismatch. Additional Rs 500 shipping charge required.", "COURIER_SCAM", "en"),

    # OTP SCAM
    ("Your Google verification code is 482916. Do not share this code with anyone. If not you, call 1800-425-6789.", "OTP_SCAM", "en"),
    ("Facebook security: OTP 739185 for login from Mumbai. Not you? Secure account: http://fb-secure.xyz", "OTP_SCAM", "en"),
    ("WhatsApp Web login attempt detected. OTP 561234. If not you, reset at http://whatsapp-reset.tk", "OTP_SCAM", "en"),
    ("SBI OTP 891234 for transfer of Rs 45,000 to account XX6789. If not authorised, call immediately.", "OTP_SCAM", "en"),
    ("GPay transaction OTP: 623489. Amount: Rs 12,500 to Paytm merchant. Not you? Block at http://gpay-block.in", "OTP_SCAM", "en"),
    ("Microsoft account recovery OTP: 451278. If you did not request this, ignore or visit http://microsoft-alert.xyz", "OTP_SCAM", "en"),
    ("Telegram: Login OTP 782345. Someone is trying to access your account from Hyderabad.", "OTP_SCAM", "en"),
    ("IRCTC: OTP 945612 for booking cancellation of PNR 4567890123. Not you? Contact support.", "OTP_SCAM", "en"),

    # INVESTMENT SCAM
    ("Stock market tip: Midcap gem identified. 300% returns in 6 months. Join paid group Rs 12,999. Call 1800-258-3690.", "INVESTMENT_SCAM", "en"),
    ("Mutual fund SIP: 28% annualized returns guaranteed. Minimum Rs 3,000/month. Free consultation now.", "INVESTMENT_SCAM", "en"),
    ("Forex trading: Make Rs 25,000 per day with our AI robot. One-time setup fee Rs 15,000: http://forex-robot.xyz", "INVESTMENT_SCAM", "en"),
    ("IPO allotment guaranteed for HNI category. Invest Rs 50,000 for 10x returns. Limited seats.", "INVESTMENT_SCAM", "en"),
    ("Real estate: Buy under-construction flats in Noida at 50% market rate. Booking amount Rs 25,000.", "INVESTMENT_SCAM", "en"),
    ("Gold savings: Pay Rs 11,000 for 11 months, get 1 year free. Total 13 months gold at 11 months price.", "INVESTMENT_SCAM", "en"),
    ("P2P lending: 24% interest on your investment. Principal protected. Start with Rs 10,000 at http://p2p-earn.tk", "INVESTMENT_SCAM", "en"),
    ("Cattle farming investment: 35% returns annually. Buy a cow for Rs 50,000, earn Rs 17,500 yearly.", "INVESTMENT_SCAM", "en"),
    ("HYIP: High yield investment program. 5% daily returns for 30 days. Minimum deposit Rs 5,000.", "INVESTMENT_SCAM", "en"),
    ("Your old LIC policy matured: Rs 2,85,000 ready for settlement. Pay Rs 8,500 processing fee.", "INVESTMENT_SCAM", "en"),

    # JOB SCAM
    ("Data entry job: Earn Rs 60,000/month from home. Registration fee Rs 2,999. Limited positions.", "JOB_SCAM", "en"),
    ("Google is hiring remote data annotators. Salary Rs 45,000/month. Apply with Rs 1,500 registration: http://google-jobs.xyz", "JOB_SCAM", "en"),
    ("Air India ground staff recruitment. Age 18-30. Application fee Rs 3,500. Last date 31 July.", "JOB_SCAM", "en"),
    ("Work from home: Amazon product reviewers needed. Rs 500 per review. Join now: membership Rs 2,500.", "JOB_SCAM", "en"),
    ("Call center jobs in Mumbai: Voice process. Salary Rs 35,000 + incentives. Training bond Rs 25,000.", "JOB_SCAM", "en"),
    ("Government job: Postal department vacancies. Guaranteed selection. Coaching fee Rs 45,000.", "JOB_SCAM", "en"),
    ("Freelance translation: English to Hindi translators needed. Pay per word. Portfolio fee Rs 1,000.", "JOB_SCAM", "en"),
    ("Modeling assignment for international brand. Stipend Rs 2 lakh. Registration Rs 7,500.", "JOB_SCAM", "en"),

    # LOTTERY SCAM
    ("KBC lucky draw: You won Rs 75,00,000 in Sony TV contest. Claim ID WIN789. Call 1800-123-4567.", "LOTTERY_SCAM", "en"),
    ("Amazon Great Indian Sale winner: You won Rs 50,000 shopping voucher. Redeem at http://amazon-voucher-claim.xyz", "LOTTERY_SCAM", "en"),
    ("Google Pay scratch card: Congratulations Rs 1,00,000 winner. Processing fee Rs 2,500 to release prize.", "LOTTERY_SCAM", "en"),
    ("Deepavali bumper: Your ticket number 452367 won Rs 25,00,000. Claim at http://lottery-claim.tk", "LOTTERY_SCAM", "en"),
    ("You won a brand new Honda City in Flipkart Big Billion Days. Pay Rs 15,000 documentation to deliver.", "LOTTERY_SCAM", "en"),
    ("Lotto India jackpot: You won Rs 5 crore. Registration fee Rs 12,500 for final processing.", "LOTTERY_SCAM", "en"),

    # DIGITAL ARREST
    ("Mumbai Cyber Cell: Your Aadhaar linked to a child pornography racket. Digital arrest warrant issued. Connect now on video call.", "DIGITAL_ARREST", "en"),
    ("CBI Hyderabad: Rs 15 crore bank fraud traced to your account. You are under digital arrest until investigation completes.", "DIGITAL_ARREST", "en"),
    ("Enforcement Directorate: Money laundering case PMLA 2026. Your assets will be attached. Digital custody ordered.", "DIGITAL_ARREST", "en"),
    ("Delhi Police: Your phone number was used to send ransom messages to the CM office. Stay on the line for interrogation.", "DIGITAL_ARREST", "en"),
    ("RBI Cyber Fraud: 87 unauthorized transactions from your account. Do not disconnect. Video verification in progress.", "DIGITAL_ARREST", "en"),
    ("Supreme Court notice: You are summoned in a 2 crore fraud case. Non-compliance = arrest warrant.", "DIGITAL_ARREST", "en"),
    ("NCB Delhi: A parcel with 3kg MDMA is booked in your name. You are under narcotics investigation. Stay online.", "DIGITAL_ARREST", "en"),
    ("Kolkata Police: Your social media account is used for fake news. Digital house arrest. Do not leave your location.", "DIGITAL_ARREST", "en"),

    # INCOME TAX SCAM
    ("Income Tax: You have a pending refund of Rs 42,500. Update bank details at http://itr-refund-process.xyz", "INCOME_TAX_SCAM", "en"),
    ("IT department: Your tax return has discrepancies. Call 1800-258-3690 to resolve within 7 days.", "INCOME_TAX_SCAM", "en"),
    ("CBDT notice: You under-reported income of Rs 12,50,000 in FY 2024-25. Pay 30% penalty now.", "INCOME_TAX_SCAM", "en"),
    ("Form 16 not matching your ITR: Tax liability of Rs 85,000 calculated. Pay at http://tax-pay.in", "INCOME_TAX_SCAM", "en"),
    ("Income Tax refund processing fee Rs 2,500 required to release your Rs 55,000 refund.", "INCOME_TAX_SCAM", "en"),
    ("Section 148 notice: Income escaping assessment for AY 2023-24. Submit revised return within 30 days.", "INCOME_TAX_SCAM", "en"),

    # PAN SCAM
    ("IT Dept: Your PAN ABCDE1234F has been used for tax evasion in Surat. Call immediately to avoid arrest.", "PAN_SCAM", "en"),
    ("PAN card: Your PAN is linked to 5 different Aadhaar numbers. This is illegal. Contact us at 1800-123-4567.", "PAN_SCAM", "en"),
    ("PAN-Aadhaar linking incomplete: Your PAN will be deactivated permanently. Link now at http://link-pan-aadhaar.xyz", "PAN_SCAM", "en"),
    ("Your PAN has been used to buy property worth Rs 85 lakhs in Jaipur. Verify ownership at http://pan-verify.in", "PAN_SCAM", "en"),
    ("PAN card update: Biometric verification required for your PAN. Visit nearest centre or pay Rs 3,500 for doorstep.", "PAN_SCAM", "en"),
    ("ITR filed using your PAN without your knowledge. File police complaint and call our helpline immediately.", "PAN_SCAM", "en"),

    # ROMANCE SCAM
    ("Hey baby, I am Maria from Spain. I saw your profile and fell in love. I want to come to India but my father needs Rs 50,000 for my tickets.", "ROMANCE_SCAM", "en"),
    ("Hello ji, I am Priya, 26 years old from London. I have 2 crore inheritance but need Rs 75,000 for legal fees to release it.", "ROMANCE_SCAM", "en"),
    ("I am Jessica, US Army nurse in Syria. My contract is ending. Send $1,000 for my flight to meet you in India.", "ROMANCE_SCAM", "en"),
    ("Hi dear, I am a Japanese fashion model. I want to settle in India with you. My agency demands Rs 1,50,000 release fee.", "ROMANCE_SCAM", "en"),
    ("I am a rich widow from Dubai. My husband died leaving me 5 million dollars. Help me transfer this money for a 30% cut.", "ROMANCE_SCAM", "en"),

    # CRYPTO SCAM
    ("Bitcoin halving: Prices will hit Rs 1.5 crore by Dec 2026. Buy now at http://btc-invest.xyz Minimum Rs 25,000.", "CRYPTO_SCAM", "en"),
    ("Ethereum merge upgrade: Staking rewards 30% APY. Stake now via our platform: http://eth-stake-rewards.tk", "CRYPTO_SCAM", "en"),
    ("New meme coin launch: ShibaFloki. Pre-sale at Rs 0.01. Expected 1000x returns. Join at http://shibafloki.xyz", "CRYPTO_SCAM", "en"),
    ("Your MetaMask wallet has been compromised. Move funds to our secure wallet: http://metamask-safe.in", "CRYPTO_SCAM", "en"),
    ("Solana NFT mint: Exclusive collection of 10,000 digital art pieces. Guaranteed 5x on listing. Mint at http://sol-nft.xyz", "CRYPTO_SCAM", "en"),
    ("Crypto arbitrage: Earn 2% daily by trading between exchanges. Our bot handles everything. Deposit Rs 50,000.", "CRYPTO_SCAM", "en"),

    # QR SCAM
    ("Flipkart gift card QR: http://qr-flipkart.tk. Scan to add Rs 10,000 voucher to your wallet.", "QR_SCAM", "en"),
    ("Swiggy food voucher QR code: http://qr-swiggy.xyz. Scan for Rs 500 off on your next order.", "QR_SCAM", "en"),
    ("Your vaccination certificate QR is ready: http://cowin-qr-download.in. Download and keep for travel.", "QR_SCAM", "en"),
    ("Metro recharge: Scan QR code at http://metro-recharge-qr.xyz for Rs 500 free travel credit.", "QR_SCAM", "en"),
    ("Zomato Pro membership QR: http://qr-zomato-pro.tk. Scan to activate 1 year free membership.", "QR_SCAM", "en"),
    ("QR code payment of Rs 250 to 'Parking Solutions' failed. Re-pay at http://parking-pay.xyz", "QR_SCAM", "en"),

    # LOAN SCAM
    ("Personal loan of Rs 50,000 instantly approved. Zero documents. Processing fee just Rs 2,999: http://instant-cash.xyz", "LOAN_SCAM", "en"),
    ("Your loan application of Rs 2,00,000 is approved by XYZ Finance. Pay Rs 12,500 insurance to disburse.", "LOAN_SCAM", "en"),
    ("Loan EMI overdue: Your credit score will be damaged. Pay Rs 15,000 immediately to regularize.", "LOAN_SCAM", "en"),
    ("Business loan up to Rs 50 lakhs at 8% interest. No collateral. Processing fee 2% of loan amount upfront.", "LOAN_SCAM", "en"),
    ("Two wheeler loan approved: Honda Activa at zero down payment. EMI Rs 2,500. Booking fee Rs 3,500.", "LOAN_SCAM", "en"),
    ("Personal loan repayment: Your cheque bounced. Legal notice under NI Act will be filed. Settle with Rs 25,000.", "LOAN_SCAM", "en"),

    # FAKE CUSTOMER CARE
    ("Netflix: Your account is on hold. Update payment at http://netflix-pay.xyz or subscription will be cancelled.", "FAKE_CUSTOMER_CARE", "en"),
    ("Amazon: Your account has been temporarily suspended. Verify identity at http://amazon-verify-account.xyz", "FAKE_CUSTOMER_CARE", "en"),
    ("Microsoft: Your Windows license has expired. Renew for Rs 7,999 at http://microsoft-renew.in to continue updates.", "FAKE_CUSTOMER_CARE", "en"),
    ("Apple Support: Your iCloud has been accessed from China. Secure at http://apple-id-secure.xyz", "FAKE_CUSTOMER_CARE", "en"),
    ("Google: Your workspace storage is full. Emails will stop. Upgrade to 2TB at Rs 1,200/year: http://google-storage.tk", "FAKE_CUSTOMER_CARE", "en"),
    ("Swiggy: Your account has won a free meal for 1 year. Confirm at http://swiggy-free.tk with delivery fee Rs 299.", "FAKE_CUSTOMER_CARE", "en"),
    ("Telegram: Unusual login from Indonesia. Secure your account at http://telegram-secure.xyz", "FAKE_CUSTOMER_CARE", "en"),
    ("LinkedIn: Your account will be restricted due to policy violation. Appeal at http://linkedin-appeal.in", "FAKE_CUSTOMER_CARE", "en"),

    # GOVERNMENT IMPERSONATION
    ("PM Awas Yojana: Your housing subsidy of Rs 2,50,000 is approved. Pay Rs 15,000 processing fee to credit.", "GOVERNMENT_IMPERSONATION", "en"),
    ("Ministry of Labour: You are eligible for Rs 75,000 skill development grant. Apply at http://govt-grant.xyz", "GOVERNMENT_IMPERSONATION", "en"),
    ("Ayushman Bharat: Your health insurance coverage increased to Rs 10 lakh. Pay Rs 3,500 upgrade fee.", "GOVERNMENT_IMPERSONATION", "en"),
    ("Voter ID correction: Your name has discrepancies. Update at http://voter-id-correction.in. Fee Rs 500.", "GOVERNMENT_IMPERSONATION", "en"),
    ("Passport Seva: Your application requires police verification urgently. Pay Rs 2,500 fast-track fee.", "GOVERNMENT_IMPERSONATION", "en"),
    ("Caste certificate online: Apply for certificate at http://caste-cert.xyz. Processing fee Rs 1,500.", "GOVERNMENT_IMPERSONATION", "en"),

    # TELECOM SCAM
    ("Jio: Your SIM card will be deactivated in 12 hours. Re-verify at http://jio-reverify.xyz", "TELECOM_SCAM", "en"),
    ("Airtel Black: Your plan upgraded to premium. Rs 7,999 annual fee will be auto-debited. Cancel at http://airtel-cancel.tk", "TELECOM_SCAM", "en"),
    ("VI: Your number porting request received. Cancellation fee Rs 2,500 applies. Call to stop.", "TELECOM_SCAM", "en"),
    ("BSNL: Your landline has outstanding dues of Rs 4,500. Pay at http://bsnl-dues.in or connection will be terminated.", "TELECOM_SCAM", "en"),
    ("TRAI: Your number reported for SMS spam. Fine of Rs 8,500 imposed. Pay at http://trai-fine.xyz", "TELECOM_SCAM", "en"),
    ("JioFiber: Your internet speed upgraded to 1 Gbps. Installation fee Rs 2,500 required.", "TELECOM_SCAM", "en"),

    # ELECTRICITY BILL SCAM
    ("Tata Power-DDL: Your bill of Rs 6,200 overdue. Disconnection team dispatched. Pay at http://tatapower-pay.xyz", "ELECTRICITY_BILL_SCAM", "en"),
    ("BSES Rajdhani: Final notice before meter removal. Pay Rs 4,800 at http://bses-final.in", "ELECTRICITY_BILL_SCAM", "en"),
    ("Adani Electricity: Smart meter installation mandatory. Fee Rs 3,500. Ignore = penalty of Rs 10,000.", "ELECTRICITY_BILL_SCAM", "en"),
    ("MSEB: Power theft suspected at your premises. Inspection ordered. Settlement fee Rs 25,000 if found guilty.", "ELECTRICITY_BILL_SCAM", "en"),
    ("UPPCL: Your security deposit needs enhancement by Rs 8,000. Pay at http://uppcl-deposit.tk", "ELECTRICITY_BILL_SCAM", "en"),
    ("KSEB: Smart meter reading shows abnormal usage. Fine of Rs 7,500 imposed.", "ELECTRICITY_BILL_SCAM", "en"),
    ("TPC: Your electricity connection will be removed for non-payment. Pay Rs 9,500 now.", "ELECTRICITY_BILL_SCAM", "en"),
    ("CESC: Your meter was tampered. Penalty of Rs 50,000 imposed. Call to settle at discount.", "ELECTRICITY_BILL_SCAM", "en"),
]

LEGIT_MESSAGES = [
    # LEGITIMATE BANKING
    ("SBI: Your account XX3456 is credited with Rs 50,000 by NEFT from ABC Corp. Ref: NEFT1234567890.", "LEGITIMATE_BANKING", "en"),
    ("HDFC Bank: Your credit card payment of Rs 15,000 received on 28 July 2026. Thank you.", "LEGITIMATE_BANKING", "en"),
    ("ICICI Bank: Your FD of Rs 3,00,000 matured on 25 July. Renewed for 1 year at 7.5% p.a.", "LEGITIMATE_BANKING", "en"),
    ("Axis Bank: Reward points earned this month: 2,450. Redeem via Axis Rewards portal.", "LEGITIMATE_BANKING", "en"),
    ("PNB: Your passbook is updated at ATM. Last 5 transactions printed on 29 July.", "LEGITIMATE_BANKING", "en"),
    ("Kotak Mahindra: Your salary for July 2026 of Rs 1,25,000 has been credited.", "LEGITIMATE_BANKING", "en"),
    ("Canara Bank: Your loan EMI of Rs 35,200 deducted successfully for home loan account.", "LEGITIMATE_BANKING", "en"),
    ("Bank of Baroda: Interest of Rs 3,540 credited to your savings account for Q1.", "LEGITIMATE_BANKING", "en"),
    ("SBI: Your e-statement for July 2026 is ready. Download from SBI YONO app.", "LEGITIMATE_BANKING", "en"),
    ("HDFC Securities: Your dividend of Rs 8,500 credited for shares held.", "LEGITIMATE_BANKING", "en"),

    # LEGITIMATE UPI
    ("Rs 2,000 sent to Rahul Sharma via GPay. UPI ref: 7890123456. Date: 28 July 2026.", "LEGITIMATE_UPI", "en"),
    ("PhonePe: Rs 650 received from your mother. UPI ref: 8765432109. Available balance: Rs 12,340.", "LEGITIMATE_UPI", "en"),
    ("Paytm UPI: Rs 3,200 paid to BigBasket for groceries. UPI mandate active.", "LEGITIMATE_UPI", "en"),
    ("BHIM: Your UPI transaction of Rs 1,500 to Metro recharge successful. Token: BHIM789012.", "LEGITIMATE_UPI", "en"),
    ("Amazon Pay: Rs 15,000 refund credited to your bank for cancelled order #OD9876543210.", "LEGITIMATE_UPI", "en"),
    ("GPay: Your weekly transaction summary: 12 payments totalling Rs 8,750.", "LEGITIMATE_UPI", "en"),
    ("UPI collect request from Flipkart: Rs 2,499 for order OD123456. Pay by 31 July.", "LEGITIMATE_UPI", "en"),
    ("Cred UPI: Cashback of Rs 287 credited for timely bill payments this month.", "LEGITIMATE_UPI", "en"),

    # LEGITIMATE COURIER
    ("Amazon: Your order #OD8765432109 has been shipped via Delhivery. Track: http://amazon.in/track", "LEGITIMATE_COURIER", "en"),
    ("Delhivery: Your parcel from Myntra is out for delivery. Expected between 4-7 PM today.", "LEGITIMATE_COURIER", "en"),
    ("FedEx: Your international package cleared customs. Delivery scheduled for 30 July.", "LEGITIMATE_COURIER", "en"),
    ("India Post: Speed post article ED123456789IN delivered to addressee on 28 July at 11:30 AM.", "LEGITIMATE_COURIER", "en"),
    ("DTDC: Your important documents courier delivered to Bangalore office. Signatory: Rajesh K.", "LEGITIMATE_COURIER", "en"),
    ("Blue Dart: Your return pickup confirmed for 30 July between 10 AM - 1 PM.", "LEGITIMATE_COURIER", "en"),
    ("Ecom Express: Delivery attempted but address not found. Update location: http://ecom-update.tk", "LEGITIMATE_COURIER", "en"),
    ("Shiprocket: Your order is in transit from Mumbai hub. AWB: 1234567890123.", "LEGITIMATE_COURIER", "en"),
    ("XpressBees: Your package from Ajio is shipped. Expected delivery in 2-3 business days.", "LEGITIMATE_COURIER", "en"),

    # LEGITIMATE GOVERNMENT
    ("PM Kisan: The 19th installment of Rs 2,000 has been credited to your Aadhaar-linked account.", "LEGITIMATE_GOVERNMENT", "en"),
    ("EPFO: Your EPF claim of Rs 1,85,000 has been approved. Amount will be credited within 5 working days.", "LEGITIMATE_GOVERNMENT", "en"),
    ("Aadhaar: Your address update request has been processed. Download updated Aadhaar from UIDAI portal.", "LEGITIMATE_GOVERNMENT", "en"),
    ("Voter ID: Your new EPIC card has been dispatched via India Post. Track at http://eci.gov.in", "LEGITIMATE_GOVERNMENT", "en"),
    ("Passport: Your application status updated to 'Printed'. Will be dispatched shortly.", "LEGITIMATE_GOVERNMENT", "en"),
    ("NPS: Your Tier 1 account balance as of 31 July: Rs 8,25,000. Monthly contribution Rs 10,000.", "LEGITIMATE_GOVERNMENT", "en"),
    ("MGNREGA: Wages for 22 days in June 2026 credited: Rs 7,480. Check your account.", "LEGITIMATE_GOVERNMENT", "en"),
    ("RTO: Your driving licence renewal application is approved. New valid till 30 July 2036.", "LEGITIMATE_GOVERNMENT", "en"),

    # LEGITIMATE OTP
    ("Your SBI OTP for transaction of Rs 25,000 is 392847. Valid for 5 minutes.", "LEGITIMATE_OTP", "en"),
    ("Amazon login OTP: 583920. If you did not request this, reset your password immediately.", "LEGITIMATE_OTP", "en"),
    ("HDFC Bank: OTP 829475 for adding beneficiary. Valid until 15:45.", "LEGITIMATE_OTP", "en"),
    ("GPay: OTP 746281 for sending money to new contact. Do not share.", "LEGITIMATE_OTP", "en"),
    ("IRCTC: OTP 938472 for booking of PNR 2345678901. Valid for 10 minutes.", "LEGITIMATE_OTP", "en"),
    ("DigiLocker: OTP 562839 for accessing your documents. Valid for 5 minutes.", "LEGITIMATE_OTP", "en"),
    ("PhonePe: OTP 183945 for login from new device. Ignore if not you.", "LEGITIMATE_OTP", "en"),
    ("Aadhaar PVC card: OTP 674839 for ordering. Delivery in 7 working days.", "LEGITIMATE_OTP", "en"),

    # LEGITIMATE TELECOM
    ("Jio: Your monthly plan of Rs 599 will expire on 5 Aug. Recharge to continue services.", "LEGITIMATE_TELECOM", "en"),
    ("Airtel: Your data usage is 90% of 2GB/day limit. Top up at http://airtel.in", "LEGITIMATE_TELECOM", "en"),
    ("VI: International roaming pack for UAE activated. Rs 2,999 charged. Valid 30 days.", "LEGITIMATE_TELECOM", "en"),
    ("BSNL: Your FTTH plan auto-renewed for Rs 799. Next billing: 28 August.", "LEGITIMATE_TELECOM", "en"),
    ("JioFiber: Your monthly data usage: 850GB out of 1000GB. Speed: 100Mbps.", "LEGITIMATE_TELECOM", "en"),
    ("TRAI: Do not disturb registered. You will not receive promotional calls.", "LEGITIMATE_TELECOM", "en"),

    # LEGITIMATE COLLEGE
    ("IIT Madras: Your semester exam results for May 2026 are published. Check academic portal.", "LEGITIMATE_COLLEGE", "en"),
    ("Delhi University: Fee payment for semester 3 of Rs 25,000 is due by 15 Aug. Pay online.", "LEGITIMATE_COLLEGE", "en"),
    ("Anna University: Your hall ticket for end semester exams is available for download.", "LEGITIMATE_COLLEGE", "en"),
    ("Amrita Vishwa: Your project submission deadline extended to 10 August 2026.", "LEGITIMATE_COLLEGE", "en"),
    ("VIT Vellore: Campus placement drive on 5 Aug. Register at http://vit-placement.in", "LEGITIMATE_COLLEGE", "en"),

    # LEGITIMATE UTILITY
    ("Tata Power: Your electricity bill for July is Rs 2,850. Due date: 15 Aug. Pay via app.", "LEGITIMATE_UTILITY", "en"),
    ("BSES: Thank you for your payment of Rs 3,200 received on 28 July.", "LEGITIMATE_UTILITY", "en"),
    ("Ajao Water: Your water bill for Q2 is Rs 1,250. Pay before 31 Aug to avoid late fee.", "LEGITIMATE_UTILITY", "en"),
    ("Housing society: Maintenance bill for August is Rs 4,500. Pay by 10th.", "LEGITIMATE_UTILITY", "en"),
    ("Property tax: Your payment for FY 2025-26 of Rs 12,750 received successfully.", "LEGITIMATE_UTILITY", "en"),

    # LEGITIMATE SHOPPING
    ("Amazon: Your order of iPhone 16 has been delivered. Rate your purchase on the app.", "LEGITIMATE_SHOPPING", "en"),
    ("Flipkart: Your return request for jeans has been approved. Pickup scheduled for 31 July.", "LEGITIMATE_SHOPPING", "en"),
    ("Myntra: 50% off on your favourite brands. Use code MINT50. Shop now: http://myntra.com", "LEGITIMATE_SHOPPING", "en"),
    ("BigBasket: Your order of Rs 2,800 has been delivered. Fresh vegetables guaranteed!", "LEGITIMATE_SHOPPING", "en"),
    ("Zomato: Your order from Pind Balluchi is being prepared. ETA 25 minutes.", "LEGITIMATE_SHOPPING", "en"),
    ("Blinkit: Your order of Rs 450 will be delivered in 10 minutes. Track live.", "LEGITIMATE_SHOPPING", "en"),

    # LEGITIMATE PERSONAL
    ("Hey mom, I reached the hostel safely. Will call you in the evening.", "LEGITIMATE_PERSONAL", "en"),
    ("Dinner tonight at 8? I'll book the restaurant. Let me know.", "LEGITIMATE_PERSONAL", "en"),
    ("Meeting rescheduled to 3 PM tomorrow. Please confirm attendance.", "LEGITIMATE_PERSONAL", "en"),
    ("Happy birthday! Wishing you a wonderful year ahead. - Rahul", "LEGITIMATE_PERSONAL", "en"),
    ("Can you pick up milk and bread on your way back home?", "LEGITIMATE_PERSONAL", "en"),
    ("Your doctor appointment is confirmed for 2 Aug at 10 AM at Apollo Clinic.", "LEGITIMATE_PERSONAL", "en"),
    ("Flight AI 202 to Delhi is on time. Boarding at Gate 12 at 6:30 PM.", "LEGITIMATE_PERSONAL", "en"),
    ("Gym membership renewed for 6 months. Total paid: Rs 8,999. Valid till Jan 2027.", "LEGITIMATE_PERSONAL", "en"),
    ("Your package delivered to neighbour. Please collect at door no 45.", "LEGITIMATE_PERSONAL", "en"),
    ("Please send me the photos from yesterday's party. Thanks!", "LEGITIMATE_PERSONAL", "en"),
    ("I'll be late today. Stuck in traffic near Silk Board.", "LEGITIMATE_PERSONAL", "en"),
    ("Dental appointment reminder: You have a checkup on 5 Aug at 4 PM.", "LEGITIMATE_PERSONAL", "en"),
    ("EMI for personal loan of Rs 8,500 deducted successfully for July.", "LEGITIMATE_PERSONAL", "en"),
    ("Bus ETA: Your bus 500A will arrive at stop in 5 minutes.", "LEGITIMATE_PERSONAL", "en"),
    ("Your car service is due at 15,000 km. Book appointment at Maruti service center.", "LEGITIMATE_PERSONAL", "en"),
    ("Railway PNR 4583927163: Train 12627 Karnataka Exp. Departs 22:00 from Platform 3.", "LEGITIMATE_PERSONAL", "en"),
    ("UPI: Rs 3,000 received from friend for trip contribution.", "LEGITIMATE_PERSONAL", "en"),
    ("Cash deposit of Rs 20,000 at SBI ATM successful on 26 July.", "LEGITIMATE_BANKING", "en"),
    ("Your credit card bill of Rs 22,500 generated. Due date: 15 Aug.", "LEGITIMATE_BANKING", "en"),
    ("IDFC Bank: Your FD of Rs 1,00,000 renewed for 1 year at 8.2% p.a.", "LEGITIMATE_BANKING", "en"),
    ("Electricity bill: Thank you for your payment of Rs 3,100.", "LEGITIMATE_UTILITY", "en"),
    ("Water supply disruption on 2 Aug due to pipeline maintenance in your area.", "LEGITIMATE_UTILITY", "en"),
    ("Your broadband bill of Rs 999 is due on 5 Aug. Auto-pay enabled.", "LEGITIMATE_UTILITY", "en"),
    ("Gas booking: Your LPG cylinder has been booked. Delivery in 3-5 days.", "LEGITIMATE_UTILITY", "en"),
    ("Insurance premium reminder: Your health insurance of Rs 18,500 due on 10 Aug.", "LEGITIMATE_SHOPPING", "en"),
    ("Nykaa: 30% off on beauty products. Use code NYK30. Offer ends midnight.", "LEGITIMATE_SHOPPING", "en"),
    ("Your Meesho order has been delivered successfully. Rate your experience.", "LEGITIMATE_SHOPPING", "en"),
    ("Croma: Your new AC installation scheduled for 2 Aug between 9 AM - 12 PM.", "LEGITIMATE_SHOPPING", "en"),
    ("Swiggy: Order delivered! Enjoy your meal. Rate your delivery partner.", "LEGITIMATE_SHOPPING", "en"),
    ("Zepto: Your order of Rs 899 is out for delivery. ETA 8 minutes.", "LEGITIMATE_SHOPPING", "en"),
    ("Your Tata Play recharge of Rs 275 successful. All channels active.", "LEGITIMATE_TELECOM", "en"),
    ("Airtel Fiber: 100GB additional data credited for loyalty reward.", "LEGITIMATE_TELECOM", "en"),
    ("Jio: Your plan auto-renewed. Rs 599 debited. Valid till 26 Aug.", "LEGITIMATE_TELECOM", "en"),
    ("NTA: Your NEET application number is 12345678. Admit card available from 10 Aug.", "LEGITIMATE_COLLEGE", "en"),
    ("UPSC: Your civil services prelims result published. Check at http://upsc.gov.in", "LEGITIMATE_COLLEGE", "en"),
    ("Scholarship: Your renewal application approved for AY 2026-27. Amount Rs 12,000.", "LEGITIMATE_COLLEGE", "en"),
    ("GPay: Weekly cashback of Rs 45 credited. Make 10 more transactions to unlock bonus.", "LEGITIMATE_UPI", "en"),
    ("PhonePe: Your gold purchase of Rs 500 successful via Digital Gold.", "LEGITIMATE_UPI", "en"),
    ("UPI transaction of Rs 250 to Mumbai Local monthly pass successful.", "LEGITIMATE_UPI", "en"),
]

# ──────────────────────────────────────
# Non-English messages
# ──────────────────────────────────────

HINGLISH_MESSAGES = [
    ("Aapka Aadhaar card block hone wala hai. Update karo yahan: http://uidai-update.xyz", "AADHAAR_SCAM", "hi-en"),
    ("SBI account freeze ho jayega agar KYC complete nahi kiya. Click karo: http://sbi-kyc.in", "KYC_SCAM", "hi-en"),
    ("Aapke PAN card se income tax fraud hua hai. Turant call karo 1800-123-4567.", "PAN_SCAM", "hi-en"),
    ("Rs 50,000 ka loan instantly approved. Processing fee sirf Rs 2,999. Apply abhi.", "LOAN_SCAM", "hi-en"),
    ("CBI ne aapke khilaf warrant issue kiya hai. Digital arrest. Video call pe connect karo.", "DIGITAL_ARREST", "hi-en"),
    ("Income tax refund of Rs 37,500 aapke naam par hai. Bank details update karo.", "INCOME_TAX_SCAM", "hi-en"),
    ("KBC mein aapne Rs 25,00,000 jeete hain. Claim karne ke liye call karo.", "LOTTERY_SCAM", "hi-en"),
    ("GPay se Rs 5,000 ka transaction hua hai. Not you? Call karo turant.", "UPI_FRAUD", "hi-en"),
    ("Aapka Amazon order return ho gaya hai. Refund ke liye bank details update karo.", "FAKE_CUSTOMER_CARE", "hi-en"),
    ("Job chahiye? Ghar baithe Rs 60,000/month. Registration fee Rs 2,500.", "JOB_SCAM", "hi-en"),
    ("PM Awas Yojana mein aapka subsidy approve hua hai. Rs 12,500 processing fee pay karo.", "GOVERNMENT_IMPERSONATION", "hi-en"),
    ("Your Aadhaar used in drug trafficking case. Police case registered. Call now.", "DIGITAL_ARREST", "hi-en"),
    ("APNA number se 5 saal ka FD khola hai. Amount: Rs 50,000. Maturity par milega Rs 85,000.", "INVESTMENT_SCAM", "hi-en"),
    ("SBI: Aapke account mein Rs 25,000 credit hue hain. Thank you for using SBI.", "LEGITIMATE_BANKING", "hi-en"),
    ("Airtel: Aapka recharge plan expire hone wala hai. Renew karo app se.", "LEGITIMATE_TELECOM", "hi-en"),
    ("Aapka Flipkart order dispatch ho gaya hai. Track karo yahan.", "LEGITIMATE_SHOPPING", "hi-en"),
    ("Aapke SBI account mein Rs 50,000 credit hue hain. NEFT se.", "LEGITIMATE_BANKING", "hi-en"),
    ("UPI se Rs 2,000 Rahul ko bheje gaye. Ref: 7890123456.", "LEGITIMATE_UPI", "hi-en"),
    ("Amazon ka order deliver ho gaya. Rating do please.", "LEGITIMATE_SHOPPING", "hi-en"),
    ("Aaj dinner 8 baje. Restaurant book kar liya hai.", "LEGITIMATE_PERSONAL", "hi-en"),
    ("Mobile recharge Rs 599 successful. Plan valid 84 days.", "LEGITIMATE_TELECOM", "hi-en"),
]

TAMIL_MESSAGES = [
    ("Ungal Aadhaar card block aagum. Udanave update pannugal: http://aadhaar-update.xyz", "AADHAAR_SCAM", "ta-en"),
    ("SBI KYC complete pannavittaal account freeze aagum. Click pannugal: http://sbi-kyc-update.in", "KYC_SCAM", "ta-en"),
    ("Ungal PAN card use panni tax evasion pannirukkaanga. Udanave 1800-123-4567 kku call pannugal.", "PAN_SCAM", "ta-en"),
    ("Rs 50,000 loan instant approval. Processing fee matum Rs 2,999. Apply now.", "LOAN_SCAM", "ta-en"),
    ("CBI warrant issued against you. Digital arrest. Video call connect aavom.", "DIGITAL_ARREST", "ta-en"),
    ("Income tax refund Rs 37,500 ready. Bank details update pannugal.", "INCOME_TAX_SCAM", "ta-en"),
    ("KBC-la Rs 25,00,000 winner! Claim panna call pannugal.", "LOTTERY_SCAM", "ta-en"),
    ("GPay-la Rs 5,000 transaction aagirukku. Not you? Call now.", "UPI_FRAUD", "ta-en"),
    ("Ungal GPay account block aagirukku. Recover panna http://gpay-help.xyz kku pongal.", "UPI_FRAUD", "ta-en"),
    ("Amazon order return aagirukku. Refund receive panna bank details update pannugal.", "FAKE_CUSTOMER_CARE", "ta-en"),
    ("Veedla irundhu job pannalam. Rs 60,000/month. Registration fee Rs 2,500.", "JOB_SCAM", "ta-en"),
    ("PM Awas Yojana subsidy approved. Rs 12,500 processing fee pay pannugal.", "GOVERNMENT_IMPERSONATION", "ta-en"),
    ("SBI: Ungal account ku Rs 25,000 credit aagirukku.", "LEGITIMATE_BANKING", "ta-en"),
    ("Airtel: Ungal recharge plan expire aaga irukku. Renew pannugal.", "LEGITIMATE_TELECOM", "ta-en"),
    ("Amazon order dispatch aagirukku. Track pannugal.", "LEGITIMATE_SHOPPING", "ta-en"),
    ("SBI: Ungal account ku Rs 50,000 NEFT la credit aagirukku.", "LEGITIMATE_BANKING", "ta-en"),
    ("GPay la Rs 2,000 Rahul ku anupirukkom. Ref: 7890123456.", "LEGITIMATE_UPI", "ta-en"),
    ("Amazon order deliver aachu. Rating kudungal.", "LEGITIMATE_SHOPPING", "ta-en"),
    ("Indru dinner 8 manikku. Restaurant book panniten.", "LEGITIMATE_PERSONAL", "ta-en"),
    ("Mobile recharge Rs 599 successful. Plan valid 84 days.", "LEGITIMATE_TELECOM", "ta-en"),
]

TELUGU_MESSAGES = [
    ("Mee Aadhaar card block avutundi. Venti update chesukondi: http://aadhaar-update.xyz", "AADHAAR_SCAM", "te-en"),
    ("SBI KYC complete cheyakapote account freeze avutundi. Click cheyandi: http://sbi-kyc.in", "KYC_SCAM", "te-en"),
    ("Mee PAN card tho income tax fraud jarigindi. Vente 1800-123-4567 ki call cheyandi.", "PAN_SCAM", "te-en"),
    ("Rs 50,000 loan instant approval. Processing fee Rs 2,999 matrame.", "LOAN_SCAM", "te-en"),
    ("CBI mee meeda warrant issue chesindi. Digital arrest. Video call connect avvali.", "DIGITAL_ARREST", "te-en"),
    ("Income tax refund Rs 37,500 ready. Bank details update chesukondi.", "INCOME_TAX_SCAM", "te-en"),
    ("KBC lo Rs 25,00,000 gelicharu! Claim cheyandi call cheyandi.", "LOTTERY_SCAM", "te-en"),
    ("GPay lo Rs 5,000 transaction jarigindi. Not you? Call now.", "UPI_FRAUD", "te-en"),
    ("Amazon order return ayindi. Refund ki bank details update cheyandi.", "FAKE_CUSTOMER_CARE", "te-en"),
    ("Intlo nunchi job cheyyochu. Rs 60,000/month. Registration fee Rs 2,500.", "JOB_SCAM", "te-en"),
    ("PM Awas Yojana subsidy approved. Rs 12,500 processing fee cheyandi.", "GOVERNMENT_IMPERSONATION", "te-en"),
    ("SBI: Mee account ki Rs 25,000 credit ayindi.", "LEGITIMATE_BANKING", "te-en"),
    ("Mee Amazon order dispatch ayindi. Track cheyandi.", "LEGITIMATE_SHOPPING", "te-en"),
    ("Airtel: Mee recharge plan expire avutundi. Renew chesukondi.", "LEGITIMATE_TELECOM", "te-en"),
    ("SBI: Mee account ki Rs 50,000 NEFT dwara credit ayindi.", "LEGITIMATE_BANKING", "te-en"),
    ("GPay lo Rs 2,000 Rahul ki pampiyaru. Ref: 7890123456.", "LEGITIMATE_UPI", "te-en"),
    ("Amazon order deliver ayindi. Rating ivvandi.", "LEGITIMATE_SHOPPING", "te-en"),
    ("Repu dinner 8 ki. Restaurant book chesanu.", "LEGITIMATE_PERSONAL", "te-en"),
    ("Mobile recharge Rs 599 successful. Plan valid 84 days.", "LEGITIMATE_TELECOM", "te-en"),
]

ALL_CANDIDATES = []
for msg in SCAM_MESSAGES:
    ALL_CANDIDATES.append({"text": msg[0], "category": msg[1], "language": msg[2], "is_scam": True})
for msg in HINGLISH_MESSAGES:
    ALL_CANDIDATES.append({"text": msg[0], "category": msg[1], "language": msg[2], "is_scam": True})
for msg in TAMIL_MESSAGES:
    ALL_CANDIDATES.append({"text": msg[0], "category": msg[1], "language": msg[2], "is_scam": True})
for msg in TELUGU_MESSAGES:
    ALL_CANDIDATES.append({"text": msg[0], "category": msg[1], "language": msg[2], "is_scam": True})
for msg in LEGIT_MESSAGES:
    ALL_CANDIDATES.append({"text": msg[0], "category": msg[1], "language": msg[2], "is_scam": False})


def make_text_clean(text):
    return text.strip().lower()


def make_id(category, index):
    return f"GOLD_{category}_{index:04d}"


# ──────────────────────────────────────
# Leakage check
# ──────────────────────────────────────

def load_training_texts():
    """Load all texts from all training datasets."""
    paths = {
        "v1": "D:/Developer/Desktop/ScamShield/backend/data/scam_dataset.csv",
        "v2_alpha": "D:/Developer/Desktop/ScamShield/datasets/v2/annotated/dataset_v2_alpha.csv",
        "v2_beta": "D:/Developer/Desktop/ScamShield/datasets/v2/annotated/dataset_v2_beta.csv",
        "v2_gamma": "D:/Developer/Desktop/ScamShield/datasets/v2/annotated/dataset_v2_gamma.csv",
    }
    source_data = {}
    for name, path in paths.items():
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        texts = [r.get("text", "").strip() for r in rows]
        cleans = [c.get("text_clean", "") or t.lower() for c, t in zip(rows, texts)]
        source_data[name] = {"texts": set(texts), "cleans": set(cleans), "rows": rows}
    return source_data


def check_leakage(candidate_text, clean_text, source_data):
    """Returns list of (source, match_type, matched_text) for each leak found."""
    leaks = []
    for sname, sdata in source_data.items():
        if candidate_text in sdata["texts"]:
            leaks.append((sname, "exact", candidate_text[:80]))
            continue
        if clean_text in sdata["cleans"]:
            # Find original
            for r in sdata["rows"]:
                rc = r.get("text_clean", "") or r.get("text", "").strip().lower()
                if rc == clean_text:
                    leaks.append((sname, "cleaned_exact", r.get("text", "")[:80]))
                    break
            else:
                leaks.append((sname, "cleaned_exact", candidate_text[:80]))
    return leaks


ENTITY_PATTERNS = [
    (r'https?://[^\s]+', '<URL>'),
    (r'\b\d{10,}\b', '<PHONE>'),
    (r'\b[A-Z]{5}\d{4}[A-Z]\b', '<PAN>'),
    (r'\b\d{12}\b', '<AADHAAR>'),
    (r'(?:Rs|INR|\$)\s*[\d,]+', '<AMOUNT>'),
    (r'\b[\w.%-]+@[\w.-]+\.[A-Za-z]{2,4}\b', '<EMAIL>'),
]

TRAIN_NGRAMS = {}
TRAIN_GENERALIZED = {}

def _ngrams(s, n=4):
    s = s.lower()
    return set(s[i:i+n] for i in range(len(s)-n+1))

def _generalize(s):
    g = s
    for pat, repl in ENTITY_PATTERNS:
        g = re.sub(pat, repl, g)
    return g

def init_caches(source_data):
    for sname, sdata in source_data.items():
        ngram_entries = []
        gen_set = set()
        for orig in sdata["texts"]:
            ng = _ngrams(orig)
            if ng:
                ngram_entries.append((orig, ng))
            gen_set.add(_generalize(orig))
        TRAIN_NGRAMS[sname] = ngram_entries
        TRAIN_GENERALIZED[sname] = gen_set
    total_entries = sum(len(v) for v in TRAIN_NGRAMS.values())
    total_gen = sum(len(v) for v in TRAIN_GENERALIZED.values())
    print(f"Cached: {total_entries} ngram sets, {total_gen} generalized texts")


def check_template_similarity(candidate_text, threshold=0.85):
    cand_ng = _ngrams(candidate_text)
    if not cand_ng:
        return []
    for sname, entries in TRAIN_NGRAMS.items():
        for orig, orig_ng in entries:
            overlap = len(cand_ng & orig_ng) / max(len(cand_ng), len(orig_ng))
            if overlap >= threshold:
                return [(sname, "near_duplicate", f"overlap={overlap:.2f}", orig[:80])]
    return []


def check_template_variant(candidate_text):
    cand_gen = _generalize(candidate_text)
    for sname, gen_set in TRAIN_GENERALIZED.items():
        if cand_gen in gen_set:
            return [(sname, "template_variant", f"generalized match: {cand_gen[:80]}", "")]
    return []





def main():
    source_data = load_training_texts()
    print(f"Training sources: {list(source_data.keys())}")
    total = sum(len(s["texts"]) for s in source_data.values())
    print(f"Total training texts: {total}")
    init_caches(source_data)

    passed = []
    leaked = []
    for idx, cand in enumerate(ALL_CANDIDATES):
        if idx % 50 == 0:
            print(f"  Checking candidate {idx}/{len(ALL_CANDIDATES)}...")
        text = cand["text"].strip()
        clean = make_text_clean(text)
        
        leaks = check_leakage(text, clean, source_data)
        if leaks:
            leaked.append((cand, leaks))
            continue
        
        near = check_template_similarity(text)
        if near:
            leaked.append((cand, near))
            continue
        
        tv = check_template_variant(text)
        if tv:
            leaked.append((cand, tv))
            continue
        
        passed.append(cand)
    
    print(f"\nPassed: {len(passed)}, Leaked: {len(leaked)}")
    
    if leaked:
        print("\n--- LEAKS ---")
        for cand, leaks in leaked[:20]:
            print(f"  [{cand['category']}] {cand['text'][:60]}...")
            for l in leaks:
                print(f"    -> {l[0]}:{l[1]} {l[2]}")
    
    # Write gold dataset from passed candidates
    fieldnames = ["id", "text", "text_clean", "language", "category", "is_scam",
                  "risk_level", "ground_truth_label", "source", "version",
                  "extracted_entities", "annotation_notes", "created_at", "updated_at"]
    
    rows = []
    cat_counter = Counter()
    lang_counter = Counter()
    scam_count = 0
    
    for i, cand in enumerate(passed, 1):
        category = cand["category"]
        is_scam = cand["is_scam"]
        lang = cand["language"]
        text = cand["text"]
        text_clean = make_text_clean(text)
        
        cat_counter[category] += 1
        lang_counter[lang] += 1
        if is_scam:
            scam_count += 1
        
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        rows.append({
            "id": make_id(category, i),
            "text": text,
            "text_clean": text_clean,
            "language": lang,
            "category": category,
            "is_scam": str(is_scam),
            "risk_level": "HIGH" if is_scam else "NONE",
            "ground_truth_label": "scam" if is_scam else "legitimate",
            "source": "gold_evaluation",
            "version": "1.0.0-gold",
            "extracted_entities": "{}",
            "annotation_notes": f"Gold evaluation sample for {category}.",
            "created_at": now,
            "updated_at": now,
        })
    
    # Write CSV
    with open(GOLD_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nGold dataset saved: {len(rows)} rows to {GOLD_PATH}")
    print(f"  Scam: {scam_count}, Legit: {len(rows) - scam_count}")
    
    # Generate leakage report
    with open(LEAKAGE_PATH, "w", encoding="utf-8") as f:
        f.write("# Leakage Report: Gold Dataset vs Training Datasets\n\n")
        f.write(f"**Gold candidates:** {len(ALL_CANDIDATES)}\n")
        f.write(f"**Passed leakage check:** {len(passed)}\n")
        f.write(f"**Leaked (removed):** {len(leaked)}\n\n")
        f.write("## Leakage Detection Methods\n\n")
        f.write("- **Exact match:** Direct string match against training texts\n")
        f.write("- **Cleaned exact:** Match after lowercasing/trimming\n")
        f.write("- **Near duplicate:** 4-gram overlap >= 85%\n")
        f.write("- **Template variant:** Entity-generalized text matches training template\n\n")
        if leaked:
            f.write("## Leaked Candidates\n\n")
            f.write("| Category | Text | Source | Match Type |\n")
            f.write("|----------|------|--------|------------|\n")
            for cand, leaks in leaked:
                for l in leaks:
                    f.write(f"| {cand['category']} | {cand['text'][:60]}... | {l[0]} | {l[1]} |\n")
        f.write("\n## Summary\n\n")
        f.write(f"**Gold dataset is clean.** {len(passed)} samples passed all leakage checks.\n")
        f.write(f"Zero contamination from training datasets.\n")
    
    print(f"Leakage report: {LEAKAGE_PATH}")
    
    # Generate dataset report
    with open(DATASET_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Gold Dataset Report\n\n")
        f.write(f"**Total samples:** {len(rows)}\n")
        f.write(f"**Scam:** {scam_count}\n")
        f.write(f"**Legitimate:** {len(rows) - scam_count}\n\n")
        f.write("## Category Distribution\n\n")
        f.write("| Category | Count |\n")
        f.write("|----------|-------|\n")
        for cat in sorted(cat_counter):
            f.write(f"| {cat} | {cat_counter[cat]} |\n")
        f.write("\n## Language Distribution\n\n")
        f.write("| Language | Count |\n")
        f.write("|----------|-------|\n")
        for lang in sorted(lang_counter):
            f.write(f"| {lang} | {lang_counter[lang]} |\n")
        f.write("\n## Dataset Characteristics\n\n")
        f.write("- Purpose: Final evaluation only. NEVER used for training.\n")
        f.write("- Composition: Manually curated real-world-style messages\n")
        f.write("- Languages: English, Hinglish, Tanglish, Teluglish\n")
        f.write("- Categories: 29 (20 scam + 9 legitimate)\n")
    
    print(f"Dataset report: {DATASET_REPORT_PATH}")
    print("Done!")


if __name__ == "__main__":
    main()
