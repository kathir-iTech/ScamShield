import csv, json, logging, os, random, re, sys, copy
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("v2-gamma")

random.seed(42)

BETA_PATH = Path(r"D:\Developer\Desktop\ScamShield\datasets\v2\annotated\dataset_v2_beta.csv")
GAMMA_DIR = Path(r"D:\Developer\Desktop\ScamShield\datasets\v2\annotated")
GAMMA_PATH = GAMMA_DIR / "dataset_v2_gamma.csv"
INPUT_PATH = GAMMA_PATH if GAMMA_PATH.exists() else BETA_PATH
REPORT_DIR = GAMMA_DIR

SCAM_CATEGORIES = {
    "UPI_FRAUD", "BANKING_FRAUD", "KYC_SCAM", "AADHAAR_SCAM", "PAN_SCAM",
    "FAKE_CUSTOMER_CARE", "COURIER_SCAM", "ELECTRICITY_BILL_SCAM", "QR_SCAM",
    "LOTTERY_SCAM", "INVESTMENT_SCAM", "CRYPTO_SCAM", "LOAN_SCAM", "JOB_SCAM",
    "ROMANCE_SCAM", "GOVERNMENT_IMPERSONATION", "DIGITAL_ARREST",
    "INCOME_TAX_SCAM", "TELECOM_SCAM",
}
LEGIT_CATEGORIES = {
    "LEGITIMATE_BANKING", "LEGITIMATE_UPI", "LEGITIMATE_OTP",
    "LEGITIMATE_COURIER", "LEGITIMATE_GOVERNMENT", "LEGITIMATE_OTHER",
}

TARGETS = {c: 70 for c in sorted(SCAM_CATEGORIES | LEGIT_CATEGORIES)}

BANKS = ["SBI", "HDFC", "ICICI", "AXIS", "PNB", "BOB", "CANARA", "KOTAK", "YES BANK", "INDUSIND"]
UPI_APPS = ["GPay", "PhonePe", "Paytm", "BHIM", "Amazon Pay", "Cred"]
CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow"]
PHONE_PREFIXES = ["1800-123", "1800-425", "1800-258", "011-", "022-", "044-", "080-", "033-"]
PHONES = [
    "1800-123-4567", "1800-425-6789", "1800-258-3690",
    "011-2345-6789", "022-3456-7890", "044-4567-8901",
    "080-5678-9012", "033-6789-0123", "1800-789-0123",
]
SCAM_DOMAINS = [
    "http://verify-uidai.xyz", "http://update-aadhaar.tk", "http://pan-verify.net",
    "http://refund-itr.com", "http://kyc-update.in", "http://bank-verify.xyz",
    "http://courier-tracking.tk", "http://electricity-bill.net",
    "http://loan-approve.xyz", "http://job-offer.tk",
    "http://reward-winner.com", "http://insurance-refund.xyz",
    "http://sim-upgrade.tk", "http://gas-subsidy.in",
    "http://govt-scheme.net", "http://lottery-win.xyz",
]
URLS_SHORT = [
    "http://tinyurl.com/verify-now",
    "http://bit.ly/claim-refund",
    "http://rebrand.ly/update-kyc",
]
AMOUNTS = [
    "Rs 5,000", "Rs 12,500", "Rs 25,000", "Rs 37,500", "Rs 45,000",
    "Rs 50,000", "Rs 75,000", "Rs 1,25,000", "Rs 2,50,000", "Rs 5,00,000",
    "$500", "$1,000", "$2,000", "$5,000", "$10,000",
]

EMAIL_REGEX = re.compile(r'\b[\w.%-]+@[\w.-]+\.[A-Za-z]{2,4}\b')
URL_REGEX = re.compile(r'https?://[^\s,]+')
PHONE_REGEX = re.compile(r'\b\d{4,6}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b')


def extract_entities(text: str) -> Dict[str, list]:
    entities = {
        "urls": URL_REGEX.findall(text),
        "phones": PHONE_REGEX.findall(text),
        "emails": EMAIL_REGEX.findall(text),
        "banks": [],
        "amounts": [],
    }
    for bank in BANKS:
        if bank.lower() in text.lower():
            entities["banks"].append(bank)
    amount_pattern = re.compile(r'(?:Rs|INR|USD)?\s*[\d,]+(?:,\d{3})*(?:\.\d+)?')
    for m in amount_pattern.finditer(text):
        entities["amounts"].append(m.group())
    return entities


def make_id(category: str, index: int) -> str:
    return f"{category}_{index:04d}"


def make_text_clean(text: str) -> str:
    return text.strip().lower()


def make_sample(text: str, category: str, is_scam: bool, risk: str,
                language: str = "en", source: str = "synthetic",
                index: int = 0) -> Dict[str, Any]:
    text_clean = make_text_clean(text)
    gt = "scam" if is_scam else "legitimate"
    entities = extract_entities(text)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return {
        "id": make_id(category, index),
        "text": text,
        "text_clean": text_clean,
        "language": language,
        "category": category,
        "is_scam": str(is_scam),
        "risk_level": risk,
        "ground_truth_label": gt,
        "source": source,
        "version": "2.0.0-gamma",
        "extracted_entities": json.dumps(entities, ensure_ascii=False),
        "annotation_notes": f"Gamma expansion variant for {category}.",
        "created_at": now,
        "updated_at": now,
    }


AMOUNT_PATTERN = re.compile(r'(?:Rs|INR|\$)\s*[0-9,]+')
BANK_NAME_PATTERN = re.compile(r'\b(' + '|'.join(BANKS) + r')\b')


def substitute_entities(text: str) -> List[str]:
    variants = []
    url_match = URL_REGEX.search(text)
    phone_match = PHONE_REGEX.search(text)
    amount_matches = AMOUNT_PATTERN.findall(text)
    bank_match = BANK_NAME_PATTERN.search(text)

    for domain in SCAM_DOMAINS[:3]:
        if url_match:
            new_text = text.replace(url_match.group(), domain)
            variants.append(new_text)

    for phone in PHONES[:3]:
        if phone_match and phone != phone_match.group():
            new_text = text.replace(phone_match.group(), phone)
            if new_text not in variants:
                variants.append(new_text)

    for amount in AMOUNTS[:3]:
        if amount_matches and amount not in [m for m in amount_matches]:
            for old_amt in amount_matches[:1]:
                new_text = text.replace(old_amt, amount)
                if new_text not in variants:
                    variants.append(new_text)

    if bank_match:
        for bank in BANKS[:4]:
            if bank != bank_match.group():
                new_text = text.replace(bank_match.group(), bank)
                if new_text not in variants:
                    variants.append(new_text)

    for city in CITIES[:5]:
        if city.lower() in text.lower():
            other_cities = [c for c in CITIES if c != city]
            for oc in other_cities[:3]:
                new_text = text.replace(city, oc)
                if new_text not in variants:
                    variants.append(new_text)

    return variants


def generate_variants(text: str, max_variants: int = 8) -> List[str]:
    result = list(dict.fromkeys([text] + substitute_entities(text)))
    return result[:max_variants]


PAN_SCAMS_EXTRA = [
    "Your PAN card will be blocked by IT Department. Update immediately at http://pan-update.xyz.",
    "PAN Aadhaar link pending! Link now or your PAN will become inoperative.",
    "Income Tax: Rs 45,000 refund against PAN ABCDE1234F approved. Claim at http://refund-pan.tk.",
    "Your PAN has been used in fraudulent transactions worth Rs 5,00,000. File complaint at 1800-123-4567.",
    "PAN card services: Your PAN has been selected for upgrade. Pay Rs 2,500 fee at http://pan-upgrade.xyz.",
    "Your PAN has been suspended due to non-linking with Aadhaar. Link at http://link-pan-aadhaar.in.",
    "Tax notice: Your PAN linked to undisclosed foreign bank account. Respond within 15 days.",
    "PAN card fraud alert: Your PAN used to open 2 companies in Delhi. Call for verification.",
    "Your PAN e-KYC is incomplete. Your PAN will be deactivated. Complete at http://pan-ekyc.xyz.",
    "PAN verification failed: Mismatch in name and DOB. Correct at http://pan-correction.tk.",
]

SCAM_TEMPLATES = {
    "AADHAAR_SCAM": [
        "Your Aadhaar card will be deactivated. Update your Aadhaar at http://verify-uidai.xyz",
        "Aadhaar update: Your mobile number is not linked. Call 1800-123-4567 immediately.",
        "Aadhaar OTP: 374829 for updating your Aadhaar mobile number. Do not share this OTP.",
        "Your Aadhaar has been used to open a bank account in Bangalore. Not you? Call now.",
        "Aadhaar download link: http://eaadhaar-download.xyz. Your Aadhaar is ready.",
        "UIDAI: Your Aadhaar biometric locked due to failed verification. Visit nearest centre.",
        "Your Aadhaar has been used to file fake IT returns. Verify at http://aadhaar-verify.in.",
        "Aadhaar seeding with bank incomplete. Your account transactions will be stopped.",
        "Your Aadhaar is being misused in Delhi. Freeze Aadhaar at http://freeze-aadhaar.tk.",
        "Aadhaar update: Free PAN-Aadhaar linking camp near you. Call 1800-123-4567.",
    ],
    "BANKING_FRAUD": [
        "Your Aadhaar card will be deactivated. Update your Aadhaar at http://verify-uidai.xyz",
        "Aadhaar update: Your mobile number is not linked. Call 1800-123-4567 immediately.",
        "Your Aadhaar biometrics have been compromised. Re-issue urgent. Call now.",
        "Aadhaar payment of Rs 5,000 approved. Click to receive: http://aadhaar-payment.tk",
        "UIDAI: Your Aadhaar used in 27 transactions across 4 states. Verify now.",
        "Your Aadhaar has been used to open a bank account in Gujarat. Not you? Call 1800-123-4567.",
        "Aadhaar seeding with bank incomplete. Your account will be frozen. Update Aadhaar now.",
        "Your Aadhaar linked mobile number is being changed. If not you, click http://block-aadhaar.xyz",
        "Aadhaar card download link: http://eaadhaar-download.in. One-time password sent.",
        "Your Aadhaar has been suspended due to invalid documents. Re-upload at http://uidai-update.xyz",
    ],
    "BANKING_FRAUD": [
        "Your SBI account has been blocked due to suspicious login from Delhi. Unblock at http://sbi-verify.xyz",
        "HDFC Bank Alert: Rs 25,000 debited for Amazon purchase. Not you? Call 1800-123-4567.",
        "ICICI Bank: Your debit card has been used for Rs 45,000 in Pune. Block card? Reply YES.",
        "Axis Bank alert: New device login detected. Verify at http://axis-secure.xyz",
        "PNB: Your account credited Rs 5,00,000 by mistake. Return via UPI immediately.",
        "Canara Bank: Your net banking blocked. Reset password at http://canara-bank.xyz",
        "BOB: Your salary account upgraded to premium. Pay Rs 2,500 annual fee at http://bob-upgrade.tk",
        "Kotak Mahindra: Fraudulent UPI transaction of Rs 12,500 detected. Reverse? Reply OTP.",
        "YES Bank: Your credit card limit increased to Rs 5,00,000. Accept at http://yes-card.xyz",
        "IndusInd Bank: Your account is under review for money laundering. Call compliance officer immediately.",
    ],
    "KYC_SCAM": [
        "Your SBI KYC is pending. Update now at http://sbi-kyc.xyz or account will freeze.",
        "HDFC Bank KYC expired. Submit documents at http://hdfc-kyc-update.in within 24 hours.",
        "ICICI Prudential: KYC documents required for insurance claim. Upload at http://icici-kyc.tk",
        "Your demat account KYC pending. Shares will be frozen. Update at http://kyc-verify.in",
        "RBI mandate: All bank accounts need Aadhaar-based KYC by March 31. Do now at http://kyc-aadhaar.xyz",
        "TRAI: Your mobile SIM KYC expired. Re-verify at http://sim-kyc.tk or line will be disconnected.",
        "Paytm KYC incomplete. Your wallet will be blocked. Complete at http://paytm-kyc.xyz.",
        "Mutual Fund KYC pending. Your investments will be halted. Update now.",
        "Your PM Kisan KYC is due. Update at http://pmkisan-kyc.in or benefits will stop.",
        "Insurance policy KYC missing. Policy will be surrendered. Upload documents now.",
    ],
    "FAKE_CUSTOMER_CARE": [
        "Amazon: Your account has been compromised. Call customer care at 1800-123-4567 to secure.",
        "Flipkart: Your order placed from new device. Verify by calling 1800-425-6789.",
        "Netflix: Your subscription is on hold. Update payment at http://netflix-bill.xyz",
        "Google: Suspicious sign-in detected. Recover account at http://gmail-recover.tk",
        "Microsoft: Your Windows license expired. Renew at http://microsoft-license.in for Rs 5,000.",
        "Apple ID: Your iCloud storage is full. Upgrade at http://apple-storage.xyz. Pay Rs 999/year.",
        "Swiggy: Your account awarded Rs 50,000 cashback. Claim at http://swiggy-reward.tk.",
        "Zomato: Pro membership expiring. Auto-debit of Rs 2,500 scheduled. Cancel at http://zomato-pro.xyz.",
        "Walmart: Your order returned. Refund of Rs 12,500 pending. Update bank details.",
        "Telegram: Premium membership Rs 1,500/year auto-renewal. Dispute at 1800-258-3690.",
        "Amazon Pay: Your gift card of Rs 5,000 activated. Use at http://amazon-gift.tk.",
        "Google Workspace: Your storage 95% full. Pay Rs 1,800/year for 200GB at http://google-storage.xyz.",
        "Myntra: Your account credited Rs 10,000 style credit. Use before expiry at http://myntra-credit.in.",
        "LinkedIn: Your account restricted due to unusual activity. Verify at http://linkedin-verify.xyz.",
        "Uber: Your payment method failed. Update before next ride or account suspended.",
    ],
    "COURIER_SCAM": [
        "FedEx: Your parcel held at Mumbai customs. Pay Rs 5,000 clearance fee at http://fedex-customs.xyz",
        "DHL: Your international shipment requires Rs 12,500 customs duty. Pay at http://dhl-clearance.tk",
        "Blue Dart: Your parcel contains prohibited items. Call 1800-123-4567 to avoid legal action.",
        "Delhivery: Your package returned due to incomplete address. Update at http://delhivery-update.in",
        "Amazon Logistics: Your delivery failed. Re-schedule at http://amazon-redeliver.xyz.",
        "India Post: Your speed post held at sorting office. Pay Rs 500 storage fee.",
        "DTDC: Your shipment from Dubai detained by customs. Rs 25,000 clearance needed.",
        "Professional Courier: Your document parcel delayed. Track at http://professional-courier.xyz",
        "Shiprocket: COD order of Rs 5,000 out for delivery. Pay at http://shiprocket-pay.tk.",
        "Ecom Express: Your return pickup rescheduled. Confirm at http://ecom-return.xyz.",
    ],
    "ELECTRICITY_BILL_SCAM": [
        "Tata Power: Your electricity bill of Rs 5,000 is overdue. Disconnection in 24 hours. Pay at http://tatapower-bill.xyz",
        "BSES: Last reminder! Your power will be cut if bill not paid. Pay Rs 3,500 at http://bses-pay.tk",
        "Adani Electricity: Rs 2,500 bill pending. Late fee of Rs 500 added. Pay now at http://adani-bill.in",
        "CESC: Your meter reading flagged as tampered. Fine of Rs 25,000 imposed. Call 1800-123-4567.",
        "MSEB: New connection fee Rs 12,500 pending. Pay at http://mseb-connection.xyz or service cancelled.",
        "TPDDL: Smart meter upgrade mandatory. Pay Rs 2,000 installation fee at http://tpddl-meter.tk.",
        "NTPC: Rebate of Rs 3,750 on your bill if paid today. Click http://ntpc-rebate.xyz.",
        "BEST: Your electricity bill payment failed. Re-pay at http://best-bill.in.",
        "Torrent Power: Security deposit of Rs 5,000 required. Link: http://torrent-deposit.xyz.",
        "APDCL: Last notice before disconnection. Pay Rs 4,500 at http://apdcl-pay.tk.",
        "UPPCL: Power theft detected at your premises. Fine Rs 50,000 imposed. Call to dispute.",
        "MSEDCL: Your bill includes arrears of Rs 12,000. Pay before 15th to avoid penalty.",
        "HBSE: New electricity connection approved. Pay Rs 7,500 development charge online.",
        "Jodhpur Vidyut Vitran: Transformer upgrade cost sharing of Rs 3,000 per consumer due.",
        "Kerala KSEB: Subsidy of Rs 1,250 credited to your bill. Reduced amount payable this month.",
    ],
    "QR_SCAM": [
        "Scan QR code at http://scan-pay.xyz to claim your Rs 25,000 reward.",
        "QR code for electricity bill payment: http://bill-qr.tk. Scan and pay Rs 3,500.",
        "Your Amazon return QR code: http://amazon-return-qr.xyz. Show at pickup.",
        "Flipkart gift card QR: http://flipkart-gift.tk. Scan to add Rs 5,000 voucher.",
        "Metro recharge QR: http://metro-qr.in. Scan to recharge Rs 1,000.",
        "Parking fee QR code: http://parking-pay.xyz. Pay Rs 200 now.",
        "Donation QR: http://charity-qr.tk. Contribute for flood relief.",
        "Vaccination certificate QR: http://cowin-qr.xyz. Download now.",
        "Hotel booking QR: http://hotel-qr.in. Scan for Rs 500 discount.",
        "Insurance premium QR: http://lic-qr.tk. Pay Rs 12,500 now.",
    ],
    "LOTTERY_SCAM": [
        "Congratulations! You won Rs 25,00,000 in KBC Lucky Draw. Claim at http://kbc-winner.xyz.",
        "You won Toyota Fortuner in Amazon Festive Giveaway. Pay Rs 12,500 processing fee.",
        "Lucky draw: You won Rs 50,000 cash prize from SBI Mega Draw. Claim at http://sbi-lucky.tk.",
        "Google Pay Tez: You won Rs 1,00,000 as scratch card reward. Pay Rs 2,500 release fee.",
        "You won iPhone 16 in Myntra Mega Sale. Claim at http://myntra-win.xyz. Pay Rs 1,500 shipping.",
        "Diwali Dhamaka: You won Rs 75,000 from Reliance Jio. Click http://jio-winner.in.",
        "You won 7 nights Dubai trip in MakeMyTrip contest. Pay Rs 12,500 registration fee.",
        "Lotto India: Your ticket won Rs 50,00,000. Claim at http://lotto-india.xyz.",
        "Pavitra Rishta contest: You won Rs 25,000 gift voucher. Click http://pavitra-win.tk.",
        "You won gold coin in HDFC Diwali contest. Pay Rs 2,000 delivery charges.",
    ],
    "INVESTMENT_SCAM": [
        "Get 10% monthly returns on US stock market investment. Minimum Rs 10,000. Call now.",
        "Bitcoin investment: Double your money in 30 days. Join at http://crypto-profit.xyz.",
        "IPO allotment guaranteed for premium members. Invest Rs 25,000 for 5x returns.",
        "Stock market tips: 100% accuracy. Rs 5,000 monthly subscription. Call 1800-123-4567.",
        "Real estate investment: Buy plots in Dubai for Rs 50,000. 50% returns guaranteed.",
        "Mutual fund SIP with 25% annual returns. Start with Rs 2,500. Limited period offer.",
        "Forex trading masterclass: Earn Rs 50,000 per month. Pay Rs 12,500 course fee.",
        "NFO: New fund offer with guaranteed 30% returns. Invest now at http://nfo-invest.xyz.",
        "Gold savings scheme: Pay Rs 5,000 monthly for 11 months, get 12th month free.",
        "Your old investment matured: Rs 2,50,000 ready for withdrawal. Pay Rs 5,000 admin fee.",
        "Ponzi scheme alert: 1000% returns in 7 days. Limited slots. Invest now at http://get-rich.xyz.",
        "Franchise opportunity: Own a Rs 5 crore business for just Rs 50,000 investment today.",
        "Tea trading from Assam: 35% profit guaranteed. Invest Rs 25,000, earn Rs 8,750 monthly.",
        "Government bond scam: Special discount for senior citizens. 15% tax-free returns.",
        "Diamond investment: Buy diamonds at wholesale, guaranteed buyback at 150% in 1 year.",
        "Penny stock tips: 10 baggers in 6 months. Rs 12,500 lifetime membership fee.",
    ],
    "PAN_SCAM": [
        "Your PAN card will be blocked by IT Department. Update immediately at http://pan-update.xyz.",
        "PAN Aadhaar link pending! Link now or your PAN will become inoperative.",
        "Income Tax: Rs 45,000 refund against PAN ABCDE1234F approved. Claim at http://refund-pan.tk.",
        "Your PAN has been used in fraudulent transactions worth Rs 5,00,000. File complaint at 1800-123-4567.",
        "PAN card upgrade mandatory. Pay Rs 2,500 fee at http://pan-upgrade.xyz.",
        "Your PAN has been suspended due to non-linking with Aadhaar. Link at http://link-pan-aadhaar.in.",
        "Tax notice: Your PAN linked to undisclosed foreign bank account. Respond within 15 days.",
        "PAN card fraud alert: Your PAN used to open 2 companies in Delhi. Call for verification.",
        "Your PAN e-KYC is incomplete. Your PAN will be deactivated. Complete at http://pan-ekyc.xyz.",
        "PAN verification failed: Mismatch in name and DOB. Correct at http://pan-correction.tk.",
        "PAN card deactivation notice: Your PAN is linked to multiple PANs. Immediate action required.",
        "Your PAN has been selected for random audit by CBDT. Submit documents for last 3 years.",
        "PAN card application payment failed. Pay Rs 1,056 again at http://pan-repay.xyz.",
        "PAN Aadhaar link deadline extended. Link before 31 Dec or pay penalty of Rs 1,000.",
        "Your PAN is being used for GST fraud in Tamil Nadu. File complaint with DG GST.",
        "PAN card correction request: Name mismatch with Aadhaar. Upload documents at http://pan-name-correct.tk.",
    ],
    "CRYPTO_SCAM": [
        "Bitcoin price crash: Buy now at Rs 25,00,000. 100x leverage available at http://crypto-trade.xyz.",
        "Etherium 2.0 staking: 25% APY guaranteed. Stake minimum 1 ETH at http://eth-stake.tk.",
        "Your crypto wallet compromised. Move funds to secure wallet at http://secure-wallet.xyz.",
        "NFT minting: Your digital art sold for Rs 5,00,000. Claim at http://nft-sale.in.",
        "Solana airdrop: 100 SOL tokens for early investors. Claim at http://sol-airdrop.xyz.",
        "Crypto arbitrage bot: Earn Rs 25,000 daily. Automated trading at http://arbitrage-bot.tk.",
        "Dogecoin pump group: Price target Rs 500. Join premium at http://doge-pump.xyz.",
        "Your Binance account flagged for KYC. Update at http://binance-verify.in.",
        "Defi yield farming: 200% APY on USDT. Deposit now at http://defi-yield.xyz.",
        "Crypto mining pool: Rs 12,500 one-time fee, Rs 5,000 daily passive income.",
        "Ripple XRP: Secret partnership with Indian banks. Price to moon. Invest Rs 50,000 now.",
        "Bitcoin halving pump: Price to reach Rs 1 crore. Buy now at http://btc-buy.xyz.",
        "Metaverse land sale: Virtual plots in Decentraland. 500% returns in 6 months.",
        "AI crypto trading bot: 95% win rate. Rs 25,000 lifetime license at http://ai-crypto.tk.",
        "Your Trust Wallet seed phrase compromised. Move funds to http://secure-wallet2.xyz.",
    ],
    "LOAN_SCAM": [
        "Instant personal loan up to Rs 5,00,000 approved. 0% interest for 3 months. Click http://instant-loan.xyz.",
        "Your loan of Rs 50,000 pre-approved. Pay Rs 2,500 processing fee to disburse.",
        "Loan EMI default! Your loan account will be closed. Pay Rs 25,000 immediately or legal notice.",
        "Business loan: Rs 25,00,000 with zero collateral. Download app at http://biz-loan.tk.",
        "Gold loan: 80% of gold value. Minimum 10g. Rs 2,500 documentation fee.",
        "Home loan pre-approved: Rs 50,00,000 at 6% interest. Lock rate at http://home-loan.in.",
        "Two-wheeler loan: Zero down payment. EMI Rs 1,999. Apply at http://bike-loan.xyz.",
        "Your loan application approved. Pay Rs 5,000 insurance fee to release funds.",
        "Emergency loan: Rs 25,000 in 5 minutes. No documents. Click http://emergency-loan.tk.",
        "Loan settlement offer: Pay 40% and close your Rs 1,00,000 loan. Call 1800-123-4567.",
        "Credit card loan: 10x your limit at 2% monthly. Rs 2,500 processing fee at http://card-loan.xyz.",
        "Education loan: Rs 50,00,000 for abroad studies at 4% interest. Block processing fee Rs 5,000.",
        "Loan repayment issue: Your EMI cheque bounced. Legal notice issued. Pay Rs 12,500 penalty.",
        "Payday loan: Rs 5,000 today, repay Rs 5,500 tomorrow. Instant approval at http://payday-loan.tk.",
        "Mortgage loan: 90% LTV on property. Rs 25,000 valuation fee required. Call today.",
    ],
    "JOB_SCAM": [
        "Work from home: Data entry operator. Earn Rs 50,000/month. Pay Rs 2,500 registration fee.",
        "Amazon work from home: Rs 75,000 salary. Submit Rs 5,000 for background verification.",
        "Online tutor needed: Rs 2,000 per hour. Pay Rs 1,500 certification fee at http://tutor-job.xyz.",
        "Airhostess job: International flights. Rs 12,500 training fee required. Apply now.",
        "Government job: SSC, Bank PO, Railway. Guaranteed selection. Pay Rs 50,000 coaching fee.",
        "Freelance content writer: Rs 25,000/month. Portfolio fee Rs 1,000. Click http://writer-job.tk.",
        "Call centre job: International voice process. Rs 35,000 salary. Training fee Rs 3,500.",
        "Canada PR job offer: Company sponsorship. Rs 2,50,000 visa processing fee.",
        "Modeling assignment: Dubai photoshoot. Rs 1,00,000 payment. Registration fee Rs 5,000.",
        "Part-time: Product review. Rs 500 per review. First month membership Rs 2,000.",
    ],
    "ROMANCE_SCAM": [
        "I am US Army captain in Syria. I want to send you gold. Pay Rs 25,000 customs fee.",
        "My father died leaving me Rs 2 crore inheritance. I need Rs 50,000 for legal fees.",
        "I love you. I want to come to India but my visa is stuck. Send Rs 75,000 for agent fees.",
        "I am a model from Russia. I want to marry you. My agency needs Rs 1,25,000 release fee.",
        "You won my heart. I am a rich widow with Rs 5 crore property. Help me transfer money.",
        "My shipping company CEO. My ship stuck in Somalia. Send $2,000 for crew rescue.",
        "I am pregnant with your child. I need Rs 25,000 for medical expenses. Please help.",
        "UN worker in Afghanistan. My life in danger. Send $1,500 for emergency evacuation.",
        "Oil rig engineer from Texas. I have gold bars worth $50,000. Ship to you. Pay shipping.",
        "Doctor in UK. My bank account frozen. Need Rs 50,000 to release my funds for our future.",
        "British Army nurse in Yemen. I love you deeply. Send Rs 35,000 for my discharge papers.",
        "Hello dear, I am a French artist. Your Facebook profile touched my heart. Need Rs 25,000 for visa.",
        "Rich businessman from Dubai wants to marry you. Send Rs 50,000 for mehandi function expenses.",
        "I am working on cruise ship in Mediterranean. My wallet stolen. Need $1,200 for flight home.",
        "NRI from Canada. I want to retire in your city. Help me transfer Rs 2 crore. Pay Rs 45,000 tax.",
        "Turkish doctor in MSF. My contract ending. Send $2,500 for relocation to your country to marry.",
    ],
    "GOVERNMENT_IMPERSONATION": [
        "Income Tax notice: Your returns under scrutiny. Click http://tax-notice.xyz for details.",
        "Government of India: PM Awas Yojana subsidy of Rs 2,50,000 approved. Pay Rs 12,500 to receive.",
        "Ministry of Finance: Your PF account settlement of Rs 5,00,000 pending. Update KYC.",
        "Labour Department: Rs 75,000 bonus under ESIC scheme. Claim at http://esic-claim.xyz.",
        "Women and Child Development: Rs 25,000 maternity benefit approved. Pay Rs 2,500 processing fee.",
        "Agricultural Ministry: PM Kisan 18th installment Rs 6,000 pending. Update at http://pmkisan-gov.in.",
        "Election Commission: Your voter ID contains errors. Update at http://voter-correction.xyz.",
        "Passport Office: Your passport application requires police verification fee Rs 3,500.",
        "National Health Mission: Free health insurance of Rs 5,00,000. Click http://nhm-insurance.tk.",
        "Education Ministry: Your scholarship of Rs 25,000 approved. Pay Rs 1,500 admin fee.",
    ],
    "DIGITAL_ARREST": [
        "Delhi Police: Your Aadhaar used in online fraud. Digital arrest warrant issued. Connect now.",
        "CBI: Money laundering case registered against you. Stay on video call for interrogation.",
        "ED: FEMA violation of Rs 5 crore linked to your PAN. Digital custody ordered.",
        "NIA: Your phone number used by terrorists. Digital house arrest. Do not disconnect.",
        "Cyber Crime Cell: Your bank account used for hacking. Digital arrest until proven innocent.",
        "RBI: 127 transactions flagged under money laundering. Join video conference immediately.",
        "Supreme Court: Non-bailable warrant for tax evasion. Digital arrest in progress.",
        "NCB: 5kg cocaine seized in parcel in your name. Digital arrest. Report for questioning.",
        "Interpol: Red corner notice issued against you. Digital detention by local cyber cell.",
        "SEBI: Insider trading investigation. Your demat account frozen. Digital arrest.",
        "CBI Hyderabad: Rs 2 crore cyber fraud traced to your account. Digital arrest warrant executed.",
        "Mumbai Police: Your images found on fake ID cards. Digital arrest. Video verification now.",
        "NCB Delhi: Courier from Thailand containing drugs in your name. Digital arrest issued.",
        "RBI Cyber Cell: 47 unauthorized transactions from your account. Join video conference.",
        "Kolkata Police: Your SIM used in extortion calls. Digital arrest. Stay online for inquiry.",
        "Cyberabad Cyber Crime: Your social media hacked for propaganda. Digital house arrest.",
        "ED Bangalore: Hawala transactions worth Rs 2.5 crore linked to your Aadhaar.",
        "CISF Mumbai Airport: Prohibited items found in baggage under your PNR. Digital arrest.",
        "State Intelligence: Your phone location at crime scene. Digital arrest pending inquiry.",
        "Narcotics Control Bureau: International drug shipment in your name seized. Digital detention.",
    ],
    "INCOME_TAX_SCAM": [
        "IT refund of Rs 37,500 pending. Verify at http://income-tax-refund.xyz.",
        "Tax evasion notice: Rs 5,00,000 undisclosed income detected. Pay 50% penalty now.",
        "IT dept: Your Form 26AS mismatch. Rectify within 7 days at http://tax-rectify.in.",
        "Scrutiny under Section 143(2): Submit documents at http://tax-scrutiny.xyz.",
        "CBDT: Your PAN linked to shell companies. File explanation immediately.",
        "Rs 45,000 tax refund blocked due to Aadhaar-PAN mismatch. Update at http://link-aadhaar.tk.",
        "ITR filing: Errors found. Pay Rs 2,500 rectification fee at http://rectify-itr.xyz.",
        "Tax notice under Black Money Act. Your foreign accounts under investigation.",
        "Your tax rebate of Rs 12,500 approved. Click http://rebate-claim.in to receive.",
        "IT department: Your case selected for special audit. Submit 5 years of documents.",
        "Tax refund of Rs 25,000 is on hold. Update bank account at http://refund-bank.xyz.",
        "Income Tax: Your Form 16 is not matching with your ITR. Rectify within 15 days.",
        "TDS mismatch detected for FY 2025-26. Pay Rs 8,500 penalty to avoid notice.",
        "Your tax return has been processed. A demand of Rs 15,000 is raised under Section 143(1).",
        "We detected offshore accounts linked to your PAN. Settle tax of Rs 2,50,000 now at discount.",
    ],
    "TELECOM_SCAM": [
        "Jio: Your SIM will be deactivated. Re-verify KYC at http://jio-kyc.xyz.",
        "Airtel: Your number used for spam calls. Line will be disconnected. Pay Rs 2,500 fine.",
        "VI: Your SIM swapped in Mumbai. Not you? Call 1800-123-4567 immediately.",
        "BSNL: Your FTTH connection will be terminated. Pay Rs 5,000 pending bill at http://bsnl-bill.tk.",
        "Your mobile number won TATA Sky lottery of Rs 25,00,000. Call to claim.",
        "TRAI: Your SMS services will be blocked due to spam complaints. Pay Rs 3,500 penalty.",
        "JioFiber: Your plan upgraded to 1Gbps. Rs 12,500 annual fee deducted. Dispute? Call now.",
        "Airtel thanks: You won Rs 1,00,000 in mega draw. Claim at http://airtel-winner.xyz.",
        "VI: International roaming activated on your number. Pay Rs 5,000 activation fee.",
        "BSNL: Your landline number will be withdrawn. Pay Rs 2,000 reconnection fee.",
        "Jio: Your number portability request received. Cancellation fee Rs 2,500. Call to stop.",
        "Airtel: Free 5G upgrade for your SIM. Pay Rs 999 upgrade fee at http://airtel-5g.xyz.",
        "VI: Your data plan expired. Special recharge Rs 599 for 2GB/day at http://vi-recharge.tk.",
        "TRAI: Your phone number reported for unsolicited calls. Pay Rs 5,000 to delist.",
        "BSNL: Your broadband usage exceeded 3TB. Speed throttled. Upgrade to premium at Rs 2,500.",
    ],
    "UPI_FRAUD": [
        "Your GPay account accessed from new device. Block at http://gpay-secure.xyz.",
        "PhonePe: Rs 25,000 paid to merchant. Not you? Call 1800-123-4567 to reverse.",
        "Paytm: UPI transaction of Rs 50,000 detected. Confirm OTP to cancel.",
        "BHIM UPI: Your UPI PIN changed. If not you, click http://bhim-block.xyz.",
        "Amazon Pay UPI: Rs 12,500 refund initiated. Click to accept: http://amazon-upi-refund.tk.",
        "UPI collect request for Rs 25,000: Pay at http://upi-pay.xyz.",
        "Your UPI limit increased to Rs 1,00,000. Approve via OTP: 543210.",
        "Google Pay: Your UPI linked to new number. Revert at http://gpay-revert.in.",
        "UPI auto-pay mandate of Rs 5,000 monthly activated. Cancel at http://stop-mandate.xyz.",
        "Cred UPI: Reward points worth Rs 7,500 expiring. Redeem at http://cred-redeem.tk.",
    ],
}


LEGIT_TEMPLATES = {
    "LEGITIMATE_BANKING": [
        "Dear customer, your SBI account XXX1234 is credited with Rs 25,000 on 15-07-2026.",
        "HDFC Bank: Your card XXX5678 used at Amazon for Rs 3,450 on 14-07-2026.",
        "ICICI Bank: Monthly salary of Rs 75,000 credited to your account. Thank you.",
        "Axis Bank alert: Bill payment of Rs 2,500 to Tata Power successful.",
        "Your PNB account statement for June 2026 is ready. Download from net banking.",
        "Your fixed deposit of Rs 5,00,000 matured. Renewed for 1 year at 7.2% p.a.",
        "Kotak: Your cheque no. 123456 of Rs 10,000 cleared on 13-07-2026.",
        "Auto-debit of Rs 12,500 for LIC premium successful from your account.",
        "Your EMI of Rs 35,000 for home loan account XX7890 deducted successfully.",
        "Canara Bank: Your passbook updated. 5 transactions recorded on 12-07-2026.",
        "SBI: Interest of Rs 2,567 credited to your savings account for Q2 FY 2025-26.",
        "HDFC: Your credit card bill of Rs 15,000 paid successfully. Thank you for payment.",
        "ICICI: Balance alert. Your account ending 7890 has balance Rs 1,25,000.",
        "Axis: Your reward points of 5,000 expiring on 31 July. Redeem via app.",
        "PNB: Your PPF account contribution of Rs 5,000 received for FY 2025-26.",
        "BOB: Your salary account upgraded. Free unlimited ATM withdrawals now active.",
    ],
    "LEGITIMATE_UPI": [
        "Rs 2,500 paid to Ramesh Kumar via GPay on 15-07-2026. UPI ref: 123456789012.",
        "Rs 500 received from Swiggy Zomato order refund via PhonePe. Ref: PAY12345.",
        "UPI payment of Rs 150 made to Metro Card recharge successful via Paytm.",
        "Rs 8,000 transferred to SBI account XXXXX1234 via BHIM UPI. Ref: BHIM67890.",
        "Amazon Pay: Rs 12,000 refund credited to your UPI account. Ref: REFUND001.",
        "UPI collect from Flipkart for order OD1234567890: Rs 2,999. Pay via any UPI app.",
        "Your daily UPI transaction limit increased to Rs 50,000. Set in your UPI app.",
        "QR payment of Rs 85 at BigBasket confirmed via BHIM UPI.",
        "Rs 1,200 received from Paytm wallet transfer via UPI. Available balance Rs 5,678.",
        "UPI mandate for Rs 500 monthly to JioFiber set up successfully.",
        "GPay: Your weekly cashback of Rs 125 credited to UPI account. Keep transacting!",
        "PhonePe: Rs 3,500 received from Sneha for dinner split. UPI ref: PH123456789.",
        "Paytm: Auto-pay mandate of Rs 1,500 for Netflix set up via UPI successfully.",
        "BHIM: Your UPI PIN changed successfully. Do not share PIN with anyone.",
        "Cred: UPI reward of Rs 250 credited for paying 5 credit card bills on time.",
        "Amazon Pay UPI: Cashback of Rs 50 credited for order payment via UPI.",
    ],
    "LEGITIMATE_OTP": [
        "Your OTP for SBI transaction is 543210. Valid for 5 minutes. Do not share.",
        "OTP 987654 for Amazon login. If not you, call 1800-123-4567 immediately.",
        "Your Aadhaar OTP: 246810 for e-KYC verification. Valid for 10 minutes.",
        "GPay OTP: 135790 for adding new beneficiary. Valid until 15:30.",
        "HDFC Bank OTP: 864209 for fund transfer of Rs 12,500 to XX1234.",
        "Email verification OTP: 975310 for your Flipkart account change request.",
        "Windows login OTP: 642087 for your Microsoft account recovery.",
        "IRCTC: OTP 753190 for booking confirmation of PNR 1234567890.",
        "LIC OTP: 428615 for viewing your policy details online.",
        "DigiLocker OTP: 519736 for accessing your Aadhaar document.",
        "PhonePe OTP: 283746 for login from new device.",
        "Paytm OTP: 918273 for wallet reload above Rs 10,000.",
        "Net banking OTP: 647382 for bill payment of Rs 5,000.",
        "UPI PIN reset OTP: 564738 for your BHIM app.",
        "Email recovery OTP: 837465 for your Gmail account recovery.",
        "Aadhaar PVC card OTP: 293847 for ordering from UIDAI.",
        "WhatsApp web OTP: 748392 for scanning QR code login.",
        "PAN card download OTP: 102938 for NSDL portal access.",
        "Voter ID OTP: 576849 for e-EPIC download.",
        "Passport Seva OTP: 384756 for appointment scheduling.",
    ],
    "LEGITIMATE_COURIER": [
        "Your Amazon order #OD1234567890 shipped. Track at http://amazon.in/track.",
        "Delhivery: Your parcel from Flipkart will be delivered today between 2-5 PM.",
        "FedEx: Your package delivered to neighbour on 15-07-2026 at 3:15 PM.",
        "Blue Dart: Shipment dispatched from Mumbai hub. Expected delivery: 18 July.",
        "India Post: Your registered letter from Income Tax Dept delivered at 10 AM.",
        "Ecom Express: Delivery failed due to gate closure. Re-attempt tomorrow.",
        "DTDC: Your documents courier delivered to Bangalore on 14-07-2026.",
        "Shiprocket order confirmed. AWB: ABC123456789. Track via website.",
        "Your Zomato order #ZOD123456 is out for delivery. ETA 10 minutes.",
        "Parcel delivered at security gate. Collect from reception. Ref: COU123456.",
        "Delhivery: Out for delivery. Track at http://delhivery.com/track.",
        "FedEx: international shipment cleared customs. Delivery scheduled tomorrow.",
        "Blue Dart: Your return pickup confirmed. Courier arriving between 10 AM and 2 PM.",
        "India Post: Speed post article delivered to addressee on 12 July 2026.",
        "Ecom Express: Your order delayed due to weather. New ETA 18 July.",
        "DTDC: Document courier from Mumbai office received at Bangalore hub.",
        "Professional Courier: Your parcel out for delivery today. Track online.",
        "Shiprocket: Shipment picked up from seller. Expected delivery in 3-4 days.",
        "XpressBees: Your order shipped. Track with AWB 123456789012.",
        "Shadowfax: Delivery partner assigned. You will receive package today.",
    ],
    "LEGITIMATE_GOVERNMENT": [
        "PM Kisan: 18th installment of Rs 2,000 credited to your Aadhaar-linked account.",
        "Your Aadhaar was successfully updated. Download updated Aadhaar from UIDAI website.",
        "EPFO: Your PF claim of Rs 1,25,000 settled. Amount credited to your account.",
        "Voter ID: Your new EPIC card dispatched. Track at http://eci.gov.in.",
        "NPS: Your Tier-1 account balance updated. Total corpus Rs 5,25,000.",
        "State Govt: Rs 12,500 subsidy for tractor purchase credited to your account.",
        "CSC: Your Ayushman Bharat card is ready for collection at nearest center.",
        "Passport: Your application status is 'Granted'. Will be dispatched in 3 days.",
        "Property tax receipt for FY 2025-26: Rs 8,750 paid successfully.",
        "RTO: Your driving licence renewal received. New expiry: 14-07-2036.",
        "PM Awas Yojana: 1st installment of Rs 50,000 released to your bank account.",
        "Sukanya Samriddhi: Account statement for FY 2025-26 available at https://nsi.gov.in.",
        "Ayushman Bharat: Your e-card is generated. Download at https://pmjay.gov.in.",
        "Income Tax: ITR for AY 2026-27 processed successfully. Refund issued if applicable.",
        "Passport: Police verification completed. Passport will be printed shortly.",
        "State scholarship: Rs 25,000 for post-matric studies credited to your Aadhaar-linked account.",
        "MGNREGA: Rs 8,250 wages for 25 days work credited to your account for June 2026.",
        "Ration card: Your e-KYC completed. Ration will be distributed from next month.",
        "Caste certificate: Application approved. Download from https://e-district.gov.in.",
        "National Pension System: Monthly contribution of Rs 5,000 deducted from salary.",
    ],
    "LEGITIMATE_OTHER": [
        "Your Netflix subscription renewed for Rs 649/month. Next billing 14 Aug 2026.",
        "Amazon Prime membership renewed for Rs 1,499/year. Valid till 15-07-2027.",
        "Your water bill for June: Rs 1,250. Pay before 25th to avoid late fee.",
        "School fee payment of Rs 25,000 for term 2 successful. Receipt: FEE123456.",
        "Housing society maintenance bill for July: Rs 3,500. Pay via app.",
        "Mobile recharge of Rs 599 successful. Plan: 1.5GB/day for 84 days. Valid till Sept.",
        "DTH recharge of Rs 275 successful. All channels active till 15-08-2026.",
        "Insurance premium reminder: Your car insurance due on 31-July-2026. Pay Rs 12,500.",
        "Your gym membership renewal of Rs 8,999 for 6 months processed successfully.",
        "Library fine of Rs 150 for late return of books paid via UPI.",
    ],
}


def read_beta_csv(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    logger.info("Read %d existing rows from %s", len(rows), path)
    return rows


def get_existing_ids_and_texts(rows):
    ids = set()
    texts = set()
    for r in rows:
        ids.add(r["id"])
        texts.add(r.get("text_clean", r.get("text", "")).strip().lower())
    return ids, texts


def generate_samples(rows: List[Dict], category: str, templates: List[str],
                     target: int, is_scam: bool, language: str = "en") -> List[Dict]:
    existing_ids, existing_texts = get_existing_ids_and_texts(rows)
    existing = [r for r in rows if r["category"] == category]
    new_samples = []
    index = len(existing) + 1

    for template in templates:
        variants = generate_variants(template, max_variants=3)
        for text in variants:
            text_clean = make_text_clean(text)
            if text_clean in existing_texts:
                continue
            sample_id = make_id(category, index)
            if sample_id in existing_ids:
                index += 1
                sample_id = make_id(category, index)
            risk = "HIGH" if is_scam and "CRITICAL" in text.upper() else ("NONE" if not is_scam else "HIGH")
            sample = make_sample(text, category, is_scam, risk, language=language, index=index)
            new_samples.append(sample)
            existing_ids.add(sample_id)
            existing_texts.add(text_clean)
            index += 1
            if len(new_samples) >= (target - len(existing)):
                break
        if len(new_samples) >= (target - len(existing)):
            break
    return new_samples


def main():
    logger.info("=" * 60)
    logger.info("V2 DATASET EXPANSION (Beta → Gamma)")
    logger.info("=" * 60)

    rows = read_beta_csv(str(INPUT_PATH))
    total_before = len(rows)
    cat_counts_before = Counter(r["category"] for r in rows)

    new_all = 0
    for cat in sorted(SCAM_CATEGORIES | LEGIT_CATEGORIES):
        target = TARGETS.get(cat, 60)
        existing = sum(1 for r in rows if r["category"] == cat)
        if existing >= target:
            logger.info("  %s: %d >= %d target, SKIP", cat, existing, target)
            continue
        is_scam = cat in SCAM_CATEGORIES
        templates = SCAM_TEMPLATES.get(cat, []) if is_scam else LEGIT_TEMPLATES.get(cat, [])
        if not templates:
            logger.warning("  %s: no templates defined, SKIP", cat)
            continue
        new_samples = generate_samples(rows, cat, templates, target, is_scam)
        if new_samples:
            rows.extend(new_samples)
            new_all += len(new_samples)
            logger.info("  %s: %d -> %d (+%d)", cat, existing, existing + len(new_samples), len(new_samples))

    gamma_path = str(GAMMA_PATH)
    if not rows:
        logger.error("No rows to write!")
        return
    fieldnames = list(rows[0].keys())
    with open(gamma_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Saved %d rows to %s", len(rows), gamma_path)

    logger.info("\nSummary: %d -> %d (+%d)", total_before, len(rows), new_all)
    cat_counts_after = Counter(r["category"] for r in rows)
    for cat in sorted(cat_counts_after):
        before = cat_counts_before.get(cat, 0)
        after = cat_counts_after.get(cat, 0)
        logger.info("  %s: %d -> %d (+%d)", cat, before, after, after - before)
    logger.info("Total scam: %d (%d before)", sum(n for c, n in cat_counts_after.items() if c in SCAM_CATEGORIES),
                sum(n for c, n in cat_counts_before.items() if c in SCAM_CATEGORIES))
    logger.info("Total legit: %d (%d before)", sum(n for c, n in cat_counts_after.items() if c in LEGIT_CATEGORIES),
                sum(n for c, n in cat_counts_before.items() if c in LEGIT_CATEGORIES))

    stats_path = REPORT_DIR / "dataset_v2_gamma_statistics.md"
    scam_before = sum(n for c, n in cat_counts_before.items() if c in SCAM_CATEGORIES)
    legit_before = sum(n for c, n in cat_counts_before.items() if c in LEGIT_CATEGORIES)
    scam_after = sum(n for c, n in cat_counts_after.items() if c in SCAM_CATEGORIES)
    legit_after = sum(n for c, n in cat_counts_after.items() if c in LEGIT_CATEGORIES)
    lang_counts_after = Counter(r.get("language", "en") for r in rows)
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write(f"# Dataset v2 Gamma Statistics\n\n")
        f.write(f"**Samples:** {total_before} → {len(rows)} (+{len(rows) - total_before})\n")
        f.write(f"**Scam:** {scam_before} → {scam_after}\n")
        f.write(f"**Legit:** {legit_before} → {legit_after}\n\n")
        f.write("| Category | Before | After | +Change |\n")
        f.write("|----------|-------|-------|---------|\n")
        for cat in sorted(cat_counts_after):
            b = cat_counts_before.get(cat, 0)
            a = cat_counts_after.get(cat, 0)
            f.write(f"| {cat} | {b} | {a} | +{a-b} |\n")
        f.write(f"\n## Languages\n\n")
        f.write("| Language | Count |\n")
        f.write("|----------|-------|\n")
        for lang, cnt in sorted(lang_counts_after.items()):
            f.write(f"| {lang} | {cnt} |\n")
    logger.info("Statistics report saved to %s", stats_path)


if __name__ == "__main__":
    main()
