import json
import time
import urllib.request
import urllib.error
from collections import defaultdict
from typing import Dict, List, Tuple

API_URL = "http://localhost:8000/analyze/text"

SAMPLES = [
    # ========== BANKING SCAM (16 samples) ==========
    {"text": "Your HDFC account has been blocked due to suspicious activity. Call 1800-XXX-XXXX immediately to reactivate.", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "SBI Alert: Your debit card has been deactivated. Update KYC at https://sbi-kyc-update.xyz or your account will be frozen.", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "ICICI Bank: Your account is temporarily suspended. Click here to restore access: http://bit.ly/icici-restore", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "Axis Bank Warning: Unauthorized login detected from New Delhi. Confirm your identity or your account will be blocked permanently.", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "Your Kotak Mahindra net banking has been locked. Call our helpdesk on 022-XXXX-XXXX to unlock within 24 hours.", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "PNB Alert: Rs 49,500 debited from your account. Not you? Call 1800-XXX-XXX immediately to reverse. OTP: 491823", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "Canara Bank: Your account KYC is expired. Update now or account will be suspended. https://canara-kyc.com/update", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "RBI Warning: Your bank account linked to illegal transactions. Call 011-XXXX-XXXX immediately to avoid legal action.", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "HDFC Bank: Your credit card application has been approved. Pay Rs 999 processing fee to receive your card.", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "YES BANK: Fraud detected on your account. Share your account details to secure your funds. Send details to fraud@yesbank-verify.com", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "State Bank of India: Your account will be deactivated. Click https://sbi-secure-login.xyz to verify your credentials now.", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "Bank of Baroda: Your savings account has been credited with INR 50,000. Pay Rs 2500 processing fee to claim this amount.", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "IDBI Bank: 2-factor authentication expired. Update immediately at https://idbi-update.tk or service will be disconnected.", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "Union Bank Alert: Your ATM card has been blocked. Call 1800-XXX-XXXX to reactivate. Do not ignore this message.", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "IndusInd Bank: New device login detected from Mumbai. If not you, secure your account now: http://bit.ly/indus-secure", "expected_category": "banking_scam", "expected_prediction": "scam"},
    {"text": "SEBI Alert: Your trading account has been used for unauthorized trades. Pay Rs 10,000 penalty to avoid suspension of demat account.", "expected_category": "banking_scam", "expected_prediction": "scam"},

    # ========== UPI SCAM (10 samples) ==========
    {"text": "Your UPI PIN has been reset. Click here to set new PIN: http://bit.ly/fake-upi", "expected_category": "upi_scam", "expected_prediction": "scam"},
    {"text": "GPay: Your UPI ID has been compromised. Verify immediately: https://gpay-verify.xyz", "expected_category": "upi_scam", "expected_prediction": "scam"},
    {"text": "PhonePe: Rs 12,500 sent to Ramesh Kumar. UPI ref UPIRef1234. Not you? Block here: http://bit.ly/phonepe-block", "expected_category": "upi_scam", "expected_prediction": "scam"},
    {"text": "Paytm UPI: Your account is limited. Complete KYC to restore unlimited payments. https://paytm-kyc.tk", "expected_category": "upi_scam", "expected_prediction": "scam"},
    {"text": "BHIM UPI: You received Rs 2,000. Claim by entering your UPI PIN at https://bhim-reward.com/claim", "expected_category": "upi_scam", "expected_prediction": "scam"},
    {"text": "Google Pay: Your UPI collect request of Rs 8,500 is pending. Approve now or your account will be debited automatically.", "expected_category": "upi_scam", "expected_prediction": "scam"},
    {"text": "Amazon Pay UPI: Congratulations! You won Rs 10,000 cashback. Claim at https://amazon-pay-reward.xyz", "expected_category": "upi_scam", "expected_prediction": "scam"},
    {"text": "UPI Alert: Your UPI linked mobile number is being changed. If not you, stop here: http://bit.ly/upi-stop", "expected_category": "upi_scam", "expected_prediction": "scam"},
    {"text": "Your UPI transaction of Rs 22,500 failed. Refund available. Click: https://refund-upi.com/process", "expected_category": "upi_scam", "expected_prediction": "scam"},
    {"text": "PhonePe: Your daily limit has been increased. Activate new limit by sharing OTP 728491 with our executive.", "expected_category": "upi_scam", "expected_prediction": "scam"},

    # ========== FAKE JOB SCAM (10 samples) ==========
    {"text": "Congratulations! You've been selected for Work From Home job. Earn Rs 50,000/month. Pay Rs 999 registration fee.", "expected_category": "fake_job", "expected_prediction": "scam"},
    {"text": "Urgent hiring for Amazon data entry. Salary Rs 35,000-60,000. No experience needed. Register: https://amazon-jobs.xyz", "expected_category": "fake_job", "expected_prediction": "scam"},
    {"text": "Flipkart is hiring part-time workers. Earn Rs 500-2000 per day. Join today: Pay Rs 499 for registration kit.", "expected_category": "fake_job", "expected_prediction": "scam"},
    {"text": "Google is offering Work From Home jobs. Type names and earn Rs 40,000/month. Processing fee Rs 1,500 required.", "expected_category": "fake_job", "expected_prediction": "scam"},
    {"text": "We liked your profile. Get international placement in Canada. Visa processing fee Rs 25,000. Limited seats!", "expected_category": "fake_job", "expected_prediction": "scam"},
    {"text": "YouTube video rating job. Earn Rs 200 per video. Weekly payout. Registration Rs 750. Contact now!", "expected_category": "fake_job", "expected_prediction": "scam"},
    {"text": "Microsoft home-based job. Data entry operator needed. Salary Rs 45,000/month. Security deposit Rs 2,000 refundable.", "expected_category": "fake_job", "expected_prediction": "scam"},
    {"text": "Swiggy delivery partner registration. Earn Rs 30,000 monthly. Complete your profile: registration fee Rs 499.", "expected_category": "fake_job", "expected_prediction": "scam"},
    {"text": "Railway recruitment 2026. 50,000 vacancies. Apply now with registration fee Rs 1,200. Guaranteed job placement.", "expected_category": "fake_job", "expected_prediction": "scam"},
    {"text": "Zomato customer support jobs from home. Salary Rs 25,000 plus incentives. Pay Rs 999 for training materials.", "expected_category": "fake_job", "expected_prediction": "scam"},

    # ========== FAKE COURIER SCAM (8 samples) ==========
    {"text": "Your FedEx package #FDX2891 is held at customs. Pay Rs 2500 clearance fee to release.", "expected_category": "fake_courier", "expected_prediction": "scam"},
    {"text": "DHL: Your international shipment is stuck at Mumbai customs. Pay Rs 3,200 for customs clearance. http://bit.ly/dhl-clear", "expected_category": "fake_courier", "expected_prediction": "scam"},
    {"text": "Blue Dart: Package delivery failed. Your parcel contains undeclared items. Pay Rs 5,000 penalty to avoid legal action.", "expected_category": "fake_courier", "expected_prediction": "scam"},
    {"text": "Amazon Logistics: Your order #AMZ99887 is held. Customs duties of Rs 1,800 pending. Pay at https://amazon-customs.xyz", "expected_category": "fake_courier", "expected_prediction": "scam"},
    {"text": "UPS: Your package from USA requires insurance clearance. Pay Rs 4,500 insurance fee for delivery.", "expected_category": "fake_courier", "expected_prediction": "scam"},
    {"text": "India Post: Your international parcel is detained. Customs clearance fee Rs 2,000 required. Contact immediately.", "expected_category": "fake_courier", "expected_prediction": "scam"},
    {"text": "FedEx Alert: Your shipment contains restricted items. Pay Rs 7,500 fine to avoid investigation by customs authorities.", "expected_category": "fake_courier", "expected_prediction": "scam"},
    {"text": "Your SpeedPost package requires additional postage of Rs 890. Pay online: https://indiapost-payment.com", "expected_category": "fake_courier", "expected_prediction": "scam"},

    # ========== OTP SCAM (10 samples) ==========
    {"text": "Your Aadhaar OTP is 284761. Do NOT share this OTP with anyone. KYC update required.", "expected_category": "otp_scam", "expected_prediction": "scam"},
    {"text": "SBI: Your OTP for transaction is 729384. Forward this OTP to 9222222222 for verification.", "expected_category": "otp_scam", "expected_prediction": "scam"},
    {"text": "Aadhaar OTP: 516273. Share this OTP with our executive to complete KYC or your Aadhaar will be deactivated.", "expected_category": "otp_scam", "expected_prediction": "scam"},
    {"text": "Your Google verification code is 382917. Do not share. But forward to your friend for referral bonus.", "expected_category": "otp_scam", "expected_prediction": "scam"},
    {"text": "OTP for PAN-Aadhaar linking is 462819. Send this OTP to 1800-XXX-XXXX immediately for link completion.", "expected_category": "otp_scam", "expected_prediction": "scam"},
    {"text": "IRCTC: Your booking OTP is 719283. WhatsApp this OTP to 9876543210 for ticket confirmation.", "expected_category": "otp_scam", "expected_prediction": "scam"},
    {"text": "Netflix: Your OTP is 638192. Share with our support agent for account recovery. Do not ignore.", "expected_category": "otp_scam", "expected_prediction": "scam"},
    {"text": "Facebook: Your login code is 482716. Forward this code to our verification bot on WhatsApp.", "expected_category": "otp_scam", "expected_prediction": "scam"},
    {"text": "Your one-time password for Paytm wallet is 927364. Never share with anyone except our customer support.", "expected_category": "otp_scam", "expected_prediction": "scam"},
    {"text": "Aadhaar OTP: 374829. Call us immediately with this OTP to update your mobile number in Aadhaar.", "expected_category": "otp_scam", "expected_prediction": "scam"},

    # ========== INVESTMENT SCAM (10 samples) ==========
    {"text": "Get 500% returns in 3 days! Bitcoin trading signal group. Limited seats. Join now!", "expected_category": "investment_scam", "expected_prediction": "scam"},
    {"text": "Stock market tips from experts. 100% guaranteed profit. Earn Rs 1 lakh in one week. Investment Rs 5,000 only.", "expected_category": "investment_scam", "expected_prediction": "scam"},
    {"text": "Cryptocurrency investment opportunity. Minimum investment Rs 10,000. Daily returns of 10% for lifetime.", "expected_category": "investment_scam", "expected_prediction": "scam"},
    {"text": "SEBI registered investment advisor. Get 10x returns in 30 days. Join our elite group. Fee Rs 15,000.", "expected_category": "investment_scam", "expected_prediction": "scam"},
    {"text": "Forex trading made easy. Earn $500 daily. Automated trading bot. One-time setup fee Rs 8,500.", "expected_category": "investment_scam", "expected_prediction": "scam"},
    {"text": "Mutual fund bonus scheme. Government approved. Invest Rs 25,000 get Rs 1,00,000 after 1 year. Limited period.", "expected_category": "investment_scam", "expected_prediction": "scam"},
    {"text": "NFT investment opportunity. Rare digital art collection. 1000x potential returns. Buy now at discounted price Rs 50,000.", "expected_category": "investment_scam", "expected_prediction": "scam"},
    {"text": "IPO guaranteed allotment. We have insider connections. Pay Rs 3,000 registration to get IPO shares at listing price.", "expected_category": "investment_scam", "expected_prediction": "scam"},
    {"text": "Ponzi scheme disguised as MLM. Actually just kidding but invest in our amazing gold trading plan. Minimum Rs 5,000.", "expected_category": "investment_scam", "expected_prediction": "scam"},
    {"text": "Real estate fractional ownership. Invest Rs 1,00,000 get 30% returns annually. Guaranteed buyback after 3 years.", "expected_category": "investment_scam", "expected_prediction": "scam"},

    # ========== ROMANCE SCAM (6 samples) ==========
    {"text": "Hi beautiful, I'm US Army captain in Syria. I need your help to transfer $2 million.", "expected_category": "romance_scam", "expected_prediction": "scam"},
    {"text": "I am a British oil engineer on offshore rig. I have fallen in love with you. Send me money for my visa to meet you.", "expected_category": "romance_scam", "expected_prediction": "scam"},
    {"text": "Hello dear. I am Maria from Russia. I want to marry you. Please send Rs 50,000 for my flight ticket to India.", "expected_category": "romance_scam", "expected_prediction": "scam"},
    {"text": "I am a UN doctor working in Congo. I received a gold shipment worth $5 million. Help me transfer it for 30% share.", "expected_category": "romance_scam", "expected_prediction": "scam"},
    {"text": "Sweetheart, I am a US soldier in Afghanistan. My leave has been denied. Pay $2,500 for my emergency leave approval.", "expected_category": "romance_scam", "expected_prediction": "scam"},
    {"text": "I am a wealthy widow from UK. I need a trustworthy person to inherit my $10 million fortune. Share your bank details.", "expected_category": "romance_scam", "expected_prediction": "scam"},

    # ========== GOVERNMENT SCAM (10 samples) ==========
    {"text": "Your PAN card has been used in illegal transactions. Call Income Tax Dept immediately or face arrest.", "expected_category": "government_scam", "expected_prediction": "scam"},
    {"text": "Income Tax Department: Tax evasion case registered against you. Pay Rs 50,000 penalty immediately to avoid arrest warrant.", "expected_category": "government_scam", "expected_prediction": "scam"},
    {"text": "Your Aadhaar card will be deactivated. Update your Aadhaar now at https://uidai-update.xyz or face legal consequences.", "expected_category": "government_scam", "expected_prediction": "scam"},
    {"text": "Electricity board: Your connection will be disconnected for non-payment. Pay Rs 4,200 immediately via this link: https://bill-pay.tk", "expected_category": "government_scam", "expected_prediction": "scam"},
    {"text": "PM Kisan Yojana: You are eligible for Rs 6,000 installment. Click to claim: https://pmkisan-gov.xyz/claim", "expected_category": "government_scam", "expected_prediction": "scam"},
    {"text": "Water department: Your water connection will be cut. Pay outstanding bill of Rs 3,800 at https://water-bill-pay.com", "expected_category": "government_scam", "expected_prediction": "scam"},
    {"text": "Central Government: Rs 1,50,000 subsidy approved for your bank account. Pay Rs 2,500 processing fee to release funds.", "expected_category": "government_scam", "expected_prediction": "scam"},
    {"text": "GST department: Your GST return has discrepancies. Pay Rs 15,000 penalty or your business registration will be cancelled.", "expected_category": "government_scam", "expected_prediction": "scam"},
    {"text": "NREGA: You have pending wages of Rs 12,000. Update your bank details at https://nrega-wages.xyz to receive payment.", "expected_category": "government_scam", "expected_prediction": "scam"},
    {"text": "Ayushman Bharat: Your health insurance is expiring. Renew now with Rs 1,200 premium or lose coverage permanently.", "expected_category": "government_scam", "expected_prediction": "scam"},

    # ========== LEGITIMATE SMS (20 samples) ==========
    {"text": "Your Flipkart order #OD12345678 has been shipped. Track here: https://flipkart.com/track", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Your monthly Netflix subscription of Rs 199 will be charged on 15th. Manage your account settings.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Your Amazon order #AMZ876543 is out for delivery. Expected by 8 PM. Track at https://amazon.in/track", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "ICICI Bank: Your credit card bill of Rs 12,500 is due on 05-Apr-2026. Auto-debit will be processed.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Swiggy: Your order from Dominos is being prepared. Estimated delivery by 7:30 PM. Track live on the app.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Zomato: Table for 2 at Pizza Express confirmed for 28 Mar 8 PM. Order #ZB89765.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "HDFC Bank: Rs 5,000 credited to your account from NEFT. Ref: NEFT123456789.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Your Uber ride is arriving. Driver: Rajesh, Car: MH12AB1234 White Swift. ETA 3 mins.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Airtel: Your monthly plan of Rs 499 will expire on 31 Mar. Recharge now to continue uninterrupted service.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "IRCTC: Your train ticket for 12951 Mumbai-Delhi on 15 Apr is confirmed. PNR: 4123567890.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Google: Your account verification code is 839201. This code expires in 10 minutes.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "LinkedIn: John Doe sent you a connection request. View profile: https://linkedin.com/in/johndoe", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "WhatsApp: Your verification code is 482-931. Do not share this code with anyone.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Paytm: Rs 250 received from Ravi Kumar. UPI Ref: 987654321098. Wallet balance: Rs 1,250.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Your appointment with Dr Sharma at Apollo Hospital is confirmed for 10:30 AM on 20 Mar.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "SBI: Your FD of Rs 2,00,000 has matured. Maturity amount Rs 2,45,678 credited to savings account.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Myntra: 50% off on your favorite brands! Use code MYNTRA50. Shop now: https://myntra.com/sale", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Vistara: Check-in for flight UK915 DEL-BOM on 22 Mar is now open. Web check-in: https://vistara.com/webcheckin", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "PhonePe: Rs 1,200 bill paid for electricity. Receipt: PP-RCPT-928374. Auto-pay scheduled for next month.", "expected_category": "legitimate", "expected_prediction": "safe"},
    {"text": "Zerodha: Your trade of 100 shares of TCS at Rs 3,450 executed successfully. Ledger updated.", "expected_category": "legitimate", "expected_prediction": "safe"},

    # ========== LOTTERY / PRIZE SCAM (8 samples) ==========
    {"text": "Congratulations! You won Rs 25,00,000 in KBC Lottery. Claim your prize by paying Rs 5,000 processing fee.", "expected_category": "lottery_scam", "expected_prediction": "scam"},
    {"text": "You won an iPhone 16 Pro! Claim your prize at https://apple-lucky-winner.xyz. Pay Rs 999 for shipping.", "expected_category": "lottery_scam", "expected_prediction": "scam"},
    {"text": "Google Lucky Draw: You won Rs 15,00,000. Contact Mr Sharma at 9876543210 with registration fee Rs 8,000.", "expected_category": "lottery_scam", "expected_prediction": "scam"},
    {"text": "Amazon Great Indian Sale winner! You won Rs 5,00,000 shopping voucher. Tax processing fee Rs 3,500 required.", "expected_category": "lottery_scam", "expected_prediction": "scam"},
    {"text": "Reliance Jio: You won free recharge for lifetime. Pay Rs 499 registration fee to activate the offer.", "expected_category": "lottery_scam", "expected_prediction": "scam"},
    {"text": "Air India: You won 2 free international tickets worth Rs 2,00,000. Processing fee Rs 4,900. Limited period offer.", "expected_category": "lottery_scam", "expected_prediction": "scam"},
    {"text": "Tata Motors customer reward: You won a brand new Nexon! Contact us with registration fee of Rs 12,000.", "expected_category": "lottery_scam", "expected_prediction": "scam"},
    {"text": "Parker Pen lucky draw: You won Rs 50,00,000. Deposit Rs 10,000 as processing fee to release your winnings.", "expected_category": "lottery_scam", "expected_prediction": "scam"},

    # ========== TECH SUPPORT SCAM (5 samples) ==========
    {"text": "Windows Alert: Your computer has been infected with 5 viruses! Call Microsoft Certified Technician immediately: 1800-XXX-XXXX.", "expected_category": "tech_support_scam", "expected_prediction": "scam"},
    {"text": "Your Netflix account has been suspended due to billing issues. Update payment: https://netflix-billing-update.xyz", "expected_category": "tech_support_scam", "expected_prediction": "scam"},
    {"text": "Facebook: Your account was reported for violation. Verify now at https://facebook-verification.tk or be permanently banned.", "expected_category": "tech_support_scam", "expected_prediction": "scam"},
    {"text": "Your Amazon Prime membership will expire today. Renew at discounted rate Rs 999. Click: https://amazon-prime-renew.xyz", "expected_category": "tech_support_scam", "expected_prediction": "scam"},
    {"text": "Google: Your business listing has been suspended. Re-verify at https://google-business-verify.com to restore visibility.", "expected_category": "tech_support_scam", "expected_prediction": "scam"},

    # ========== LOAN SCAM (5 samples) ==========
    {"text": "Instant personal loan up to Rs 25 lakhs. No paperwork. 0% interest for 6 months. Processing fee Rs 2,500.", "expected_category": "loan_scam", "expected_prediction": "scam"},
    {"text": "Bajaj Finserv: Your pre-approved loan of Rs 5,00,000 is ready. Pay Rs 3,000 documentation fee to disburse.", "expected_category": "loan_scam", "expected_prediction": "scam"},
    {"text": "Home loan at 2% interest rate! Government subsidy available. Register with Rs 5,000 processing fee. Limited offer.", "expected_category": "loan_scam", "expected_prediction": "scam"},
    {"text": "Student loan for abroad studies. 100% approval. No collateral. Pay Rs 2,000 application fee to proceed.", "expected_category": "loan_scam", "expected_prediction": "scam"},
    {"text": "Business loan Rs 50 lakhs in 24 hours. CIBIL not required. Processing fee 1% of loan amount. Contact now.", "expected_category": "loan_scam", "expected_prediction": "scam"},

    # ========== PHISHING / ACCOUNT SCAM (6 samples) ==========
    {"text": "Your email account password will expire today. Keep same password: https://email-verify-now.xyz", "expected_category": "phishing_scam", "expected_prediction": "scam"},
    {"text": "Instagram: Your account has been hacked. Recover now: https://instagram-recovery.xyz/login", "expected_category": "phishing_scam", "expected_prediction": "scam"},
    {"text": "LinkedIn: Someone tried to access your account from Russia. Secure here: http://bit.ly/linkedin-secure", "expected_category": "phishing_scam", "expected_prediction": "scam"},
    {"text": "Twitter: Your account has been restricted. Appeal at https://twitter-appeal.tk to restore your account.", "expected_category": "phishing_scam", "expected_prediction": "scam"},
    {"text": "Microsoft: Unusual sign-in detected. Verify your identity at https://microsoft-account-verify.com", "expected_category": "phishing_scam", "expected_prediction": "scam"},
    {"text": "Your Apple ID has been locked for security reasons. Unlock here: https://apple-id-unlock.xyz", "expected_category": "phishing_scam", "expected_prediction": "scam"},
]


def call_api(text: str) -> dict:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps({"text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"error": str(e)}


def evaluate():
    results = []
    errors = []
    category_results = defaultdict(list)

    print(f"{'='*100}")
    print(f"  SCAMSHIELD BENCHMARK EVALUATION REPORT")
    print(f"  API Endpoint: {API_URL}")
    print(f"  Total Samples: {len(SAMPLES)}")
    print(f"  Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}\n")

    for i, sample in enumerate(SAMPLES, 1):
        text = sample["text"]
        expected_cat = sample["expected_category"]
        expected_pred = sample["expected_prediction"]

        response = call_api(text)

        if "error" in response:
            errors.append((i, text, response["error"]))
            print(f"  [{i:03d}] ERROR: {response['error']}")
            continue

        result = {
            "index": i,
            "text_preview": text[:80] + ("..." if len(text) > 80 else ""),
            "text": text,
            "expected_category": expected_cat,
            "expected_prediction": expected_pred,
            "prediction": response.get("prediction", "unknown"),
            "confidence": response.get("confidence", 0),
            "scam_category": response.get("scam_category", ""),
            "risk_level": response.get("risk_level", ""),
            "assessment_score": response.get("assessment_score", 0),
            "assessment_band": response.get("assessment_band", ""),
            "rule_score": response.get("rule_score", 0),
            "rule_label": response.get("rule_label", ""),
        }
        results.append(result)
        category_results[expected_cat].append(result)

        correct = "CORRECT" if result["prediction"] == result["expected_prediction"] else "MISCLASSIFIED"
        marker = "+" if correct == "CORRECT" else "!"
        print(f"  [{i:03d}] {marker} pred={result['prediction']:<5} conf={result['confidence']:.3f} "
              f"cat={result['scam_category']:<20} risk={result['risk_level']:<6} "
              f"score={result['assessment_score']:<4} band={result['assessment_band']:<8} "
              f"expected={expected_pred:<5} [{correct}]")
        print(f"         Text: {result['text_preview']}")

    print(f"\n{'='*100}")
    print(f"  SUMMARY STATISTICS")
    print(f"{'='*100}")
    total = len(results)
    correct_total = sum(1 for r in results if r["prediction"] == r["expected_prediction"])
    misclassified = [r for r in results if r["prediction"] != r["expected_prediction"]]
    total_errors = len(errors)

    print(f"  Total Samples Tested:     {total}")
    print(f"  Correct Predictions:      {correct_total}")
    print(f"  Misclassified:            {len(misclassified)}")
    print(f"  API Errors:               {total_errors}")
    print(f"  Overall Accuracy:         {correct_total/total*100:.2f}%" if total > 0 else "  N/A")
    print(f"  Error Rate:               {(total-correct_total)/total*100:.2f}%" if total > 0 else "  N/A")

    print(f"\n{'='*100}")
    print(f"  PER-CATEGORY BREAKDOWN")
    print(f"{'='*100}")
    print(f"  {'Category':<25} {'Total':>6} {'Correct':>8} {'Accuracy':>9} {'FP':>5} {'FN':>5}")
    print(f"  {'-'*25} {'-'*6} {'-'*8} {'-'*9} {'-'*5} {'-'*5}")

    grand_tp = grand_fp = grand_fn = grand_tn = 0
    category_metrics = {}

    for cat in sorted(category_results.keys()):
        cat_res = category_results[cat]
        total_cat = len(cat_res)
        if cat == "legitimate":
            tp = sum(1 for r in cat_res if r["prediction"] == "safe")
            fp = sum(1 for r in cat_res if r["prediction"] == "scam")
            fn = 0
            tn = 0
        else:
            tp = sum(1 for r in cat_res if r["prediction"] == "scam")
            fp = 0
            fn = sum(1 for r in cat_res if r["prediction"] == "safe")
            tn = 0

        correct_cat = sum(1 for r in cat_res if r["prediction"] == r["expected_prediction"])
        accuracy_cat = correct_cat / total_cat * 100 if total_cat > 0 else 0

        category_metrics[cat] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "total": total_cat, "correct": correct_cat}

        if cat == "legitimate":
            grand_tn += tp
            grand_fp += fp
        else:
            grand_tp += tp
            grand_fn += fn

        print(f"  {cat:<25} {total_cat:>6} {correct_cat:>8} {accuracy_cat:>8.1f}% {'N/A':>5} {'N/A':>5}")

    print(f"{'='*100}")

    total_scam = sum(v["total"] for k, v in category_metrics.items() if k != "legitimate")
    total_legit = category_metrics.get("legitimate", {}).get("total", 0)
    print(f"\n  Scam samples: {total_scam}, Legitimate samples: {total_legit}")

    print(f"\n{'='*100}")
    print(f"  CONFUSION MATRIX")
    print(f"{'='*100}")
    print(f"  {'':<20} {'Predicted Scam':>16} {'Predicted Safe':>16}")
    print(f"  {'-'*20} {'-'*16} {'-'*16}")
    print(f"  {'Actual Scam':<20} {grand_tp:>16} {grand_fn:>16}")
    print(f"  {'Actual Safe':<20} {grand_fp:>16} {grand_tn:>16}")

    precision = grand_tp / (grand_tp + grand_fp) if (grand_tp + grand_fp) > 0 else 0
    recall = grand_tp / (grand_tp + grand_fn) if (grand_tp + grand_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    specificity = grand_tn / (grand_tn + grand_fp) if (grand_tn + grand_fp) > 0 else 0
    fpr = grand_fp / (grand_fp + grand_tn) if (grand_fp + grand_tn) > 0 else 0
    fnr = grand_fn / (grand_fn + grand_tp) if (grand_fn + grand_tp) > 0 else 0

    print(f"\n{'='*100}")
    print(f"  OVERALL METRICS")
    print(f"{'='*100}")
    print(f"  Precision:           {precision:.4f}  ({precision*100:.2f}%)")
    print(f"  Recall (Sensitivity):{recall:.4f}  ({recall*100:.2f}%)")
    print(f"  F1 Score:            {f1:.4f}  ({f1*100:.2f}%)")
    print(f"  Specificity:         {specificity:.4f}  ({specificity*100:.2f}%)")
    print(f"  False Positive Rate:  {fpr:.4f}  ({fpr*100:.2f}%)")
    print(f"  False Negative Rate:  {fnr:.4f}  ({fnr*100:.2f}%)")

    print(f"\n{'='*100}")
    print(f"  PER-CATEGORY PRECISION, RECALL, F1")
    print(f"{'='*100}")
    print(f"  {'Category':<25} {'Precision':>10} {'Recall':>10} {'F1 Score':>10} {'Support':>8}")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")

    for cat in sorted(category_metrics.keys()):
        m = category_metrics[cat]
        if cat == "legitimate":
            p = m["tp"] / (m["tp"] + m["fp"]) if (m["tp"] + m["fp"]) > 0 else 0
            r = m["tp"] / (m["tp"] + m["fn"]) if (m["tp"] + m["fn"]) > 0 else 0  # fn always 0 for legit
            f = 2 * p * r / (p + r) if (p + r) > 0 else 0
            print(f"  {'safe (' + cat + ')':<25} {p:>10.4f} {r:>10.4f} {f:>10.4f} {m['total']:>8}")
        else:
            p = m["tp"] / (m["tp"] + m["fp"]) if (m["tp"] + m["fp"]) > 0 else 1.0  # fp always 0 here
            r = m["tp"] / (m["tp"] + m["fn"]) if (m["tp"] + m["fn"]) > 0 else 0
            f = 2 * p * r / (p + r) if (p + r) > 0 else 0
            print(f"  {'scam (' + cat + ')':<25} {p:>10.4f} {r:>10.4f} {f:>10.4f} {m['total']:>8}")

    print(f"\n{'='*100}")
    print(f"  MISCLASSIFICATION ANALYSIS")
    print(f"{'='*100}")
    if misclassified:
        for i, r in enumerate(misclassified, 1):
            print(f"\n  --- Misclassification #{i} ---")
            print(f"  Input Text:     {r['text']}")
            print(f"  Expected:       prediction={r['expected_prediction']}, category={r['expected_category']}")
            print(f"  Predicted:      prediction={r['prediction']}, category={r['scam_category']}")
            print(f"  Confidence:     {r['confidence']:.4f}")
            print(f"  Risk Level:     {r['risk_level']}")
            print(f"  Assessment:     score={r['assessment_score']}, band={r['assessment_band']}")
            print(f"  Rule Score:     {r['rule_score']} ({r['rule_label']})")

            text_lower = r['text'].lower()
            reasons = []

            if r["expected_prediction"] == "scam" and r["prediction"] == "safe":
                reasons.append("FALSE NEGATIVE: Scam text classified as safe.")
                has_urgency = any(w in text_lower for w in ["urgent", "immediately", "now", "hurry", "limited"])
                has_money = any(w in text_lower for w in ["rs", "inr", "pay", "fee", "money", "transfer"])
                has_link = "http" in text_lower
                has_suspicious_keywords = any(w in text_lower for w in ["kyc", "otp", "bank", "account", "aadhaar", "pan", "upi"])

                if not has_urgency:
                    reasons.append("  - Missing urgency keywords (urgent, immediately, now)")
                else:
                    reasons.append("  - Urgency detected but insufficient scoring")
                if not has_money:
                    reasons.append("  - Missing monetary demand keywords")
                else:
                    reasons.append("  - Money mention detected but overall score below thresholds")
                if has_link:
                    legit_domains = ["flipkart.com", "amazon.in", "amazon.com", "paytm.com", "phonepe.com", "google.com", "facebook.com", "netflix.com", "linkedin.com", "whatsapp.com"]
                    is_legit_domain = any(d in text_lower for d in legit_domains)
                    if is_legit_domain:
                        reasons.append("  - URL uses a known legitimate domain, reducing suspicion")
                    else:
                        reasons.append("  - URL present but not flagged with enough weight")
                if not has_suspicious_keywords:
                    reasons.append("  - Missing scam-specific keywords that trigger rules")
                reasons.append("  - Rule engine combined score likely fell below the scam threshold (35/70)")

            elif r["expected_prediction"] == "safe" and r["prediction"] == "scam":
                reasons.append("FALSE POSITIVE: Legitimate text classified as scam.")
                if "otp" in text_lower or "verification code" in text_lower or "one time password" in text_lower:
                    reasons.append("  - OTP keyword triggered OTP rule even though message has no sharing request")
                if "http" in text_lower:
                    reasons.append("  - URL in message triggered suspicious link rule")
                if "bank" in text_lower or any(b in text_lower for b in ["sbi", "hdfc", "icici", "axis"]):
                    reasons.append("  - Bank name mentioned triggered service keywords rule")
                if "pay" in text_lower or "rs" in text_lower:
                    reasons.append("  - Money/payment mention triggered urgent money rule")
                reasons.append("  - Combined rule score exceeded the safe threshold")
            else:
                reasons.append("Unexpected misclassification pattern.")

            reasons.append("  - SUGGESTED FIX: Adjust rule weights or add context-aware detection")

            for reason in reasons:
                print(f"  {reason}")
    else:
        print("  No misclassifications found!")

    if errors:
        print(f"\n  --- API Errors ({len(errors)}) ---")
        for idx, text, err in errors:
            print(f"  [{idx}] {text[:60]}... -> {err}")

    print(f"\n{'='*100}")
    print(f"  END OF EVALUATION REPORT")
    print(f"{'='*100}")


if __name__ == "__main__":
    evaluate()
