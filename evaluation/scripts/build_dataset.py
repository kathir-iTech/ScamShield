import json
import os
from typing import Any, Dict, List


def _sample(
    sid: str, text: str, pred: str, category: str, risk: str,
    decision: str, assessment: str, difficulty: str, lang: str,
    source: str, reason: str = "", entities: list = None,
    conf_min: float = 0.0, conf_max: float = 1.0,
    action: str = "", priority: str = "", notes: str = "",
) -> Dict[str, Any]:
    return {
        "id": sid,
        "text": text,
        "expected_prediction": pred,
        "expected_category": category,
        "expected_risk_level": risk,
        "expected_decision_level": decision,
        "expected_assessment_band": assessment,
        "expected_entities": entities or [],
        "expected_confidence_min": conf_min,
        "expected_confidence_max": conf_max,
        "difficulty": difficulty,
        "language": lang,
        "source_type": source,
        "ground_truth_reason": reason,
        "expected_action": action,
        "expected_priority": priority,
        "notes": notes,
    }


def build_dataset() -> List[Dict[str, Any]]:
    samples: List[Dict[str, Any]] = []

    # ── Bank KYC Scam (15) ──────────────────────────────────────────
    bank_kyc = [
        _sample("bank-kyc-001", "Your SBI account will be blocked today. Update KYC immediately: http://bit.ly/kyc-update", "scam", "Bank KYC Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "KYC update with shortened URL and bank impersonation", ["url", "bank_name"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("bank-kyc-002", "HDFC Bank: Your account has been deactivated due to incomplete KYC. Click https://hdfc-verify.tk to reactivate", "scam", "Bank KYC Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "Account deactivation threat with suspicious TLD", ["url", "suspicious_tld", "bank_name"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("bank-kyc-003", "Dear Customer, your ICICI bank a/c will be suspended. Update your Aadhaar KYC now. https://icici-update.xyz", "scam", "Bank KYC Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Account suspension threat with Aadhaar KYC request", ["url", "suspicious_tld", "bank_name"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("bank-kyc-004", "SBI Alert: Your account is blocked due to KYC not updated. Click: http://sbi-kyc.ml to update now", "scam", "Bank KYC Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "Blocked account with .ml domain", ["url", "suspicious_tld", "bank_name"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("bank-kyc-005", "Your Axis Bank ATM card will be deactivated. Update KYC: https://axisverify.tk", "scam", "Bank KYC Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Card deactivation with KYC link", ["url", "suspicious_tld", "bank_name"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("bank-kyc-006", "KYC update mandatory for your account. Failing to update will result in permanent block. https://sbi-kyc.gq", "scam", "Bank KYC Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "Permanent block threat with .gq domain", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("bank-kyc-007", "Alert: Your Kotak Mahindra account needs KYC renewal. Click: http://tiny.cc/kyc-kotak", "scam", "Bank KYC Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Shortened URL with bank impersonation", ["shortened_url", "bank_name"], 0.75, 0.95, "Block and report", "HIGH"),
        _sample("bank-kyc-008", "PNB: Your account is temporarily suspended. Complete KYC to restore. http://pnb-update.tk", "scam", "Bank KYC Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "easy", "en", "sms", "Suspension with generic template", ["url", "suspicious_tld", "bank_name"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("bank-kyc-009", "Canara Bank: Your aadhaar seeding incomplete. Update now or account will freeze. https://canara-kyc.ga", "scam", "Bank KYC Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Aadhaar seeding threat with .ga domain", ["url", "suspicious_tld", "bank_name"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("bank-kyc-010", "We have detected unusual activity. Your BOB account needs verification. http://bob-verify.tk", "scam", "Bank KYC Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Unusual activity fear tactic", ["url", "suspicious_tld", "bank_name"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("bank-kyc-011", "Dear IndusInd customer, your account will be disabled in 24hrs. Update KYC: https://indusind-alert.top", "scam", "Bank KYC Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "24hr deadline with .top domain", ["url", "suspicious_tld", "bank_name"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("bank-kyc-012", "Your SBI YONO access has been restricted. Please update your KYC profile. http://secure-sbi.xyz", "scam", "Bank KYC Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "YONO restricted with misleading domain", ["url", "suspicious_tld", "bank_name"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("bank-kyc-013", "RBI Mandatory: All bank accounts require KYC update by tomorrow. http://rbi-kyc.ml", "scam", "Bank KYC Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "RBI impersonation with .ml domain", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("bank-kyc-014", "Ungal SBI account KYC update pannitt illaina block aagum. https://sbi-update.tk", "scam", "Bank KYC Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "ta", "sms", "Tamil version of bank KYC scam", ["url", "suspicious_tld", "bank_name"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("bank-kyc-015", "Your HDFC account ku KYC mandatory. Click the link and update. http://tinyurl.com/hdfc-update", "scam", "Bank KYC Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "tangling", "sms", "Tanglish KYC with URL shortener", ["shortened_url", "bank_name"], 0.7, 0.95, "Do not interact", "HIGH"),
    ]
    samples.extend(bank_kyc)

    # ── UPI / Payment Scam (15) ────────────────────────────────────
    upi_samples = [
        _sample("upi-001", "Your GPay account has been credited Rs 4500. Claim now: http://gpay-cashback.tk", "scam", "UPI Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Fake credit with claim link", ["url", "suspicious_tld", "upi_id"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("upi-002", "PhonePe: You won Rs 10000 cashback! Click to redeem: https://phonepe-winner.top", "scam", "UPI Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Lottery-style UPI cashback", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("upi-003", "Your Paytm wallet has been blocked. Update KYC: https://paytm-verify.xyz", "scam", "UPI Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "easy", "en", "sms", "Wallet block KYC phishing", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("upi-004", "Neraya cashback! Rs 5000 credit pannirukkom. Claim panniko: http://tiny.cc/cashback", "scam", "UPI Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "ta", "sms", "Tamil UPI cashback with shortened URL", ["shortened_url"], 0.6, 0.9, "Do not interact", "HIGH"),
        _sample("upi-005", "UPI reference number UTR32984739. Payment of Rs 7200 received. Check now: http://payment-confirm.ml", "scam", "UPI Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Fake payment confirmation with .ml domain", ["url", "suspicious_tld", "transaction_id"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("upi-006", "Your BHIM UPI pin is expiring. Update now: https://bhim-upi.tk", "scam", "UPI Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "easy", "en", "sms", "UPI PIN expiry phishing", ["url", "suspicious_tld"], 0.75, 0.95, "Block and report", "HIGH"),
        _sample("upi-007", "Google Pay: Unusual login detected from Pune. Secure your account: http://gpay-secure.xyz", "scam", "UPI Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Unusual login alert phishing", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("upi-008", "PhonePe transaction failed! Refund available. Process: http://refund-phonepe.tk", "scam", "UPI Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Refund phishing with .tk domain", ["url", "suspicious_tld"], 0.6, 0.9, "Do not interact", "NORMAL"),
        _sample("upi-009", "Your UPI account has been credited Rs 9999. Click to check balance: https://reward-claim.ga", "scam", "UPI Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Fake credit large amount", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("upi-010", "Paytm cashback offer! Rs 2500 unclaimed. http://paytm-offer.top", "scam", "UPI Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "easy", "en", "sms", "Unclaimed cashback with .top", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("upi-011", "Amazon Pay: You have been selected for Rs 5000 gift card. Claim: https://amazon-gift.tk", "scam", "UPI Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Amazon gift card phishing", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("upi-012", "GPay la Rs 8000 credit aagirukku. Ippa linka click panni claim pannungo: https://gpay-cash.tk", "scam", "UPI Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "ta", "sms", "Tamil GPay credit scam", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("upi-013", "PhonePe account upgrade pannikunga. Unlimited cashback offer! http://phonepe-upgrade.top", "scam", "UPI Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "tangling", "sms", "Tanglish PhonePe upgrade scam", ["url", "suspicious_tld"], 0.6, 0.85, "Do not interact", "NORMAL"),
        _sample("upi-014", "Alert: Rs 15000 withdrawn from your Paytm wallet. Dispute: http://paytm-dispute.tk", "scam", "UPI Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "medium", "en", "sms", "Fake withdrawal alert phishing", ["url", "suspicious_tld"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("upi-015", "Your Google Pay daily limit has been increased to Rs 50000. Verify: https://gpay-limit.tk", "scam", "UPI Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "hard", "en", "sms", "Limit increase phishing - subtle", ["url", "suspicious_tld"], 0.5, 0.8, "Verify independently", "NORMAL"),
    ]
    samples.extend(upi_samples)

    # ── Lottery / Prize Scam (12) ──────────────────────────────────
    lotteries = [
        _sample("lottery-001", "CONGRATULATIONS! You won Rs 25,00,000 in KBC Lucky Draw. Call 1800-123-4567 to claim.", "scam", "Lottery Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "KBC lottery with toll-free number", ["phone"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("lottery-002", "Amazon Mega Draw! You won a brand new iPhone 15. Contact: claim@amazon-promo.tk", "scam", "Lottery Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Amazon iPhone lottery", ["email", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("lottery-003", "KBC winner 2025! Your cheque of Rs 15,00,000 is ready. Processing fee Rs 2500 required. Call now!", "scam", "Lottery Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "Advance fee lottery scam", [], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("lottery-004", "Flipkart Big Billion Draw! You won Rs 50,000. Pay processing fee Rs 199 to claim: http://flipkart-winner.xyz", "scam", "Lottery Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Flipkart lottery with fee", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("lottery-005", "You have been selected for Rs 1 crore lottery by reliance. Call 1900-123-456 to claim immediately!", "scam", "Lottery Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "medium", "en", "sms", "Reliance crope lottery", ["phone"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("lottery-006", "Congratulations! Nikeil message la neenga lottery winner aaga irukinga! Rs 10 lakhs claim panniko!", "scam", "Lottery Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "ta", "sms", "Tamil lottery scam without URL", [], 0.65, 0.9, "Do not interact", "HIGH"),
        _sample("lottery-007", "HDFC Bank: Your transaction won a lucky draw of Rs 50,000! Contact http://hdfc-draw.tk", "scam", "Lottery Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Bank transaction lucky draw", ["url", "suspicious_tld", "bank_name"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("lottery-008", "Your phone number won a lottery of Rs 75,000. This is an international lottery. Claim: http://uk-lottery.ml", "scam", "Lottery Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "International lottery phishing", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("lottery-009", "Tata Group: You won Rs 5 lakhs in our customer appreciation draw. Contact tata-promo@outlook.com", "scam", "Lottery Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "email", "Company appreciation lottery", ["email"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("lottery-010", "Prize money Rs 10,00,000 unclaimed! Last day today. Call 090-1234-5678 immediately!", "scam", "Lottery Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Unclaimed prize with urgency", ["phone"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("lottery-011", "Big Bazaar Lucky Draw! Neenga winner! Rs 25,000 gift voucher. http://bigbazaar-offer.ga", "scam", "Lottery Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "tangling", "sms", "Tanglish Big Bazaar lottery", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "HIGH"),
        _sample("lottery-012", "Congratulations! Your email has won a cash prize of £500,000 from UK National Lottery. Contact our agent.", "scam", "Lottery Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "email", "UK lottery advance fee", [], 0.7, 0.95, "Block and report", "HIGH"),
    ]
    samples.extend(lotteries)

    # ── Investment / Crypto Scam (12) ──────────────────────────────
    investments = [
        _sample("invest-001", "Double your money in 7 days! Guaranteed 200% returns. Invest now: http://quick-profit.ml", "scam", "Investment Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Ponzi scheme with guaranteed returns", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("invest-002", "Bitcoin trading: Earn Rs 25,000 daily. Minimum investment Rs 1000. Join: https://crypto-profit.xyz", "scam", "Investment Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Crypto daily earning scam", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("invest-003", "SEBI approved investment scheme! 35% monthly returns. Limited seats. Call 1800-123-4567", "scam", "Investment Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "medium", "en", "sms", "Fake SEBI approval with phone", ["phone"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("invest-004", "Mutual fund guaranteed returns! 50% profit in 3 months. Start with Rs 5000. http://mutual-fund.top", "scam", "Investment Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Mutual fund with guaranteed returns", ["url", "suspicious_tld"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("invest-005", "Cryptocurrency investment! Get 10x returns. Bitcoin ethereum trading. WhatsApp group: https://t.me/crypto-invest", "scam", "Crypto Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "medium", "en", "telegram", "Crypto 10x returns via Telegram", ["social_handle"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("invest-006", "Work from home data entry. Earn Rs 500-2000 daily. No investment required. Contact: job@home-work.tk", "scam", "Investment Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "WFH data entry with suspicious email", ["email", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("invest-007", "Stock market tips! 100% accuracy. 7 day free trial. SMS JOIN to 56789", "scam", "Investment Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "hard", "en", "sms", "Stock tips without URL", [], 0.5, 0.8, "Verify independently", "NORMAL"),
        _sample("invest-008", "NFT investment! Limited edition digital art. 1000x returns. Mint now: http://nft-drop.tk", "scam", "Crypto Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "social", "NFT scam with .tk domain", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("invest-009", "RBI bond scheme! 40% interest. Government approved. http://rbi-scheme.ml", "scam", "Investment Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "RBI impersonation bond scam", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("invest-010", "Passive income: Earn Rs 50,000 monthly from crypto trading bot. Fully automated. https://trading-bot.xyz", "scam", "Crypto Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Automated trading bot scam", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("invest-011", "Share market la nalla profit! Weekly 20% guaranteed. Join our Telegram: t.me/share_tips", "scam", "Investment Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "hard", "ta", "telegram", "Tamil stock tips Telegram", ["social_handle"], 0.55, 0.85, "Verify independently", "NORMAL"),
        _sample("invest-012", "Crypto mining cloud service! Earn 0.05 BTC weekly. Start with Rs 2000 only. http://crypto-mine.ga", "scam", "Crypto Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Cloud mining scam", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
    ]
    samples.extend(investments)

    # ── Courier / Customs / Delivery Scam (12) ────────────────────
    deliveries = [
        _sample("delivery-001", "Your parcel from Dubai customs has been held. Release fee Rs 15000 required. http://dhl-customs.tk", "scam", "Courier Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "DHL customs release fee", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("delivery-002", "FedEx: Your package contains illegal items! Pay fine Rs 25000 to avoid legal action. http://fedex-alert.xyz", "scam", "Customs Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "Illegal package fine threat", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("delivery-003", "Blue Dart: Your international shipment is stuck at customs. Clearance fee Rs 8000. Pay now: http://dart-customs.ml", "scam", "Courier Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Blue Dart customs clearance", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("delivery-004", "Amazon international parcel stopped at Mumbai customs. Pay Rs 12000 release fee: https://amazon-customs.tk", "scam", "Customs Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "medium", "en", "sms", "Amazon customs with specific amount", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("delivery-005", "Urgent: Your shipment tracking ID: SH2024IN9065 requires customs clearance. http://track-customs.top", "scam", "Courier Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Shipment tracking with fake tracking ID", ["url", "suspicious_tld", "tracking_id"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("delivery-006", "Your parcel contains undeclared goods. Customs department has seized it. Pay penalty: http://customs-india.tk", "scam", "Customs Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "Seized parcel with .tk domain", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("delivery-007", "DTDC: Your package weight mismatch detected. Additional shipping fee Rs 3500. http://dtdc-billing.xyz", "scam", "Courier Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Weight mismatch fee scam", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("delivery-008", "Speed Post: Your parcel contains gold jewelry worth Rs 5 lakhs. Customs verification needed. http://speedpost-in.ml", "scam", "Courier Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Gold jewelry in parcel scam", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("delivery-009", "Your Amazon order RB7845NH has been stopped by customs. Pay import fee Rs 9000. http://tiny.cc/amazon-customs", "scam", "Customs Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Amazon order with specific ID", ["shortened_url"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("delivery-010", "Courier company: Unga parcel la illegal items irukku! Fine pay pannanum. http://customs-alert.ga", "scam", "Customs Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "medium", "ta", "sms", "Tamil customs illegal items threat", ["url", "suspicious_tld"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("delivery-011", "DHL tracking: Package held at Chennai customs. Release fee Rs 12000 required. Track: https://dhl-india.top", "scam", "Courier Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "DHL with city-specific customs", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("delivery-012", "Your international courier requires insurance payment of Rs 5000. Pay here: http://courier-insure.tk", "scam", "Courier Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Insurance fee add-on scam", ["url", "suspicious_tld"], 0.6, 0.85, "Do not interact", "NORMAL"),
    ]
    samples.extend(deliveries)

    # ── Job Scam (12) ─────────────────────────────────────────────
    jobs = [
        _sample("job-001", "Urgent hiring! Work from home data entry. Salary Rs 25000/month. Registration fee Rs 999. http://job-hiring.tk", "scam", "Job Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "WFH job with registration fee", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("job-002", "Amazon work from home job! Earn Rs 50000 monthly. No experience needed. Apply: https://amazon-jobs.xyz", "scam", "Job Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "easy", "en", "sms", "Amazon WFH with unrealistic pay", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("job-003", "Part-time job: Rs 2000 per day. Simple online work. Register with Rs 499 refundable deposit. http://part-time.top", "scam", "Job Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Part-time job deposit scam", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("job-004", "Data entry operators required. Daily payment Rs 1500. Processing fee Rs 599. http://dataentry.ml", "scam", "Job Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "easy", "en", "sms", "Data entry processing fee", ["url", "suspicious_tld"], 0.8, 1.0, "Do not interact", "HIGH"),
        _sample("job-005", "Flipkart product review job! Earn Rs 100 per review. Free registration: https://flipkart-review.ga", "scam", "Job Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Product review job scam", ["url", "suspicious_tld"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("job-006", "YouTube video editing job! Rs 30000 per month. Training provided. Fee Rs 2000. http://youtube-jobs.top", "scam", "Job Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Video editing job training fee", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("job-007", "Overseas job in Dubai! Salary 1.5 lakhs. Visa processing fee Rs 15000. Contact: hr@dubai-jobs.tk", "scam", "Job Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Dubai job visa fee scam", ["email", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("job-008", "Call center job! Work from home. Good salary. Exam fee Rs 299. http://callcenter-hire.tk", "scam", "Job Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Call center exam fee scam", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("job-009", "Vela venuma? Data entry, part time. Monthly Rs 30,000. Registration fee Rs 999. http://tamil-jobs.tk", "scam", "Job Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "ta", "sms", "Tamil job scam registration fee", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "HIGH"),
        _sample("job-010", "Excellent opportunity! MNC company hiring. Work from home or office. Registration Rs 1499. http://mnc-hire.xyz", "scam", "Job Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "MNC hiring registration fee", ["url", "suspicious_tld"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("job-011", "Simple copy paste job! Rs 2000 per day. No investment. Register free: http://copy-work.ml", "scam", "Job Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Copy-paste job scam", ["url", "suspicious_tld"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("job-012", "Telegram part-time job! Add group members and earn Rs 5000 daily. Join: https://t.me/earn_online", "scam", "Job Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "hard", "en", "telegram", "Telegram group promotion job", ["social_handle"], 0.55, 0.85, "Verify independently", "NORMAL"),
    ]
    samples.extend(jobs)

    # ── Government Scheme Scam (12) ────────────────────────────────
    govt = [
        _sample("govt-001", "PM Modi: Rs 5000 monthly pension scheme. Register now: https://pm-scheme.tk", "scam", "Government Scheme Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "PM pension scheme with .tk domain", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("govt-002", "Central Government: Rs 15000 subsidy for all citizens. Apply: http://govt-subsidy.xyz", "scam", "Government Scheme Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Government subsidy scam", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("govt-003", "Aadhaar linking mandatory! Your PAN-Aadhaar not linked. Link now: http://aadhaar-link.ml", "scam", "Government Scheme Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "PAN-Aadhaar linking phishing", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("govt-004", "PM Awas Yojana: You have been selected for housing subsidy. Pay processing fee Rs 5000: http://pmay-scheme.top", "scam", "Government Scheme Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "PM Awas Yojana processing fee", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("govt-005", "Ayushman Bharat: Health insurance of Rs 5 lakhs approved. Registration fee Rs 999: http://ayushman.ga", "scam", "Government Scheme Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Ayushman Bharat registration fee", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("govt-006", "NREGA job card: 100 days work guaranteed. Apply with Rs 250 processing: http://nrega-register.tk", "scam", "Government Scheme Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "NREGA processing fee scam", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("govt-007", "Mahatma Gandhi National Pension: You are eligible for Rs 2000 monthly pension. Register: https://pension-scheme.ml", "scam", "Government Scheme Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "National pension eligibility scam", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("govt-008", "Income Tax refund of Rs 8500 is pending. Update your bank details: http://itr-refund.tk", "scam", "Government Scheme Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "ITR refund phishing with .tk domain", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("govt-009", "Sarkari yojna: Rs 5000 har mahine! Apply karein: http://sarkari-scheme.xyz", "scam", "Government Scheme Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "tangling", "sms", "Hindi-English scheme scam", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "HIGH"),
        _sample("govt-010", "CSC centre: Digital India scheme! Laptop free me paaye. Registration Rs 999. http://csc-scheme.tk", "scam", "Government Scheme Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "tangling", "sms", "CSC free laptop registration fee", ["url", "suspicious_tld"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("govt-011", "Aadhaar card update pannikunga! Payment Rs 500. http://aadhaar-update.ml", "scam", "Government Scheme Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "ta", "sms", "Tamil Aadhaar update payment", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "HIGH"),
        _sample("govt-012", "Your electricity bill payment failed! Immediate disconnection warning. Pay now: http://tneb-bill.tk", "scam", "Electricity Bill Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "TNEB disconnection threat", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
    ]
    samples.extend(govt)

    # ── OTP / Account Suspension (10) ──────────────────────────────
    otp_samples = [
        _sample("otp-001", "Your SBI account has been compromised. Share OTP 784512 to secure your account immediately!", "scam", "Bank KYC Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "Direct OTP request in SMS", ["otp_code"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("otp-002", "Alert: 15000 withdrawn from your account. OTP 321654 required to reverse transaction.", "scam", "OTP Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "OTP reversal scam", ["otp_code", "currency_amount"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("otp-003", "Your Amazon account has been hacked! Your order of iPhone 15 is being placed. OTP: 542389. Share to cancel.", "scam", "Phishing", "HIGH", "HIGH RISK", "Suitable for immediate action", "medium", "en", "sms", "Fake Amazon hack OTP scam", ["otp_code"], 0.75, 0.95, "Do not interact", "URGENT"),
        _sample("otp-004", "Google verification: Your account will be deleted. OTP 984312. Forward to 9988776655 to keep active.", "scam", "Phishing", "HIGH", "HIGH RISK", "Suitable for immediate action", "medium", "en", "sms", "Account deletion OTP scam", ["otp_code", "phone"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("otp-005", "Your social media account reported for fraud. OTP: 673421. Send to 9988776655 to verify identity.", "scam", "OTP Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Social media account verification OTP", ["otp_code", "phone"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("otp-006", "Dear user, your account will be suspended. OTP 782345 required for verification. Reply with OTP.", "scam", "Account Suspension", "HIGH", "HIGH RISK", "Suitable for immediate action", "medium", "en", "sms", "Account suspension OTP harvesting", ["otp_code"], 0.75, 0.95, "Block and report", "URGENT"),
        _sample("otp-007", "Netflix: Your subscription is suspended! Update payment: http://netflix-renew.tk", "scam", "Subscription Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Netflix subscription phishing", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("otp-008", "Your Apple ID has been locked. Verify here: https://apple-verify.tk", "scam", "Phishing", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Apple ID lock phishing", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("otp-009", "Facebook: Someone tried to login from Kolkata. Secure your account: http://fb-secure.tk", "scam", "Phishing", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "email", "Facebook login alert phishing", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("otp-010", "Your email account password expired. Update now: https://email-update.ml", "scam", "Phishing", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "email", "Email password expiry phishing", ["url", "suspicious_tld"], 0.6, 0.85, "Do not interact", "NORMAL"),
    ]
    samples.extend(otp_samples)

    # ── QR Code Scam (8) ───────────────────────────────────────────
    qr_samples = [
        _sample("qr-001", "Scan this QR code to claim your Rs 5000 Paytm cashback! http://paytm-qr.tk", "scam", "QR Code Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "QR code cashback with link", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("qr-002", "QR code scan panni Rs 10,000 gift voucher vangikunga! http://gift-qr.xyz", "scam", "QR Code Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "ta", "sms", "Tamil QR code gift voucher", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("qr-003", "Electricity bill pay panna QR code scan pannunga. 50% discount! http://bill-qr.top", "scam", "QR Code Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "ta", "sms", "Electricity bill QR discount scam", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("qr-004", "Free recharging! Scan QR and get Rs 200 free mobile recharge. Limited offer: http://free-recharge.tk", "scam", "QR Code Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Free recharge QR scam", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("qr-005", "Google Pay QR code scanner! Scan any QR and earn rewards. Download: http://gpay-qr.ml", "scam", "QR Code Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Fake GPay QR download link", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("qr-006", "Your parcel delivery needs QR payment of Rs 500 for customs. Scan: http://delivery-qr.tk", "scam", "QR Code Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Parcel QR customs payment", ["url", "suspicious_tld"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("qr-007", "QR code scanner app download panni 2000rs daily earn pannunga! http://earn-qr.tk", "scam", "QR Code Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "tangling", "sms", "Tanglish QR earning app scam", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("qr-008", "Zomato: Scan this QR code for 80% discount on your next order! https://zomato-offer.ga", "scam", "QR Code Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Zomato QR discount scam", ["url", "suspicious_tld"], 0.6, 0.85, "Do not interact", "NORMAL"),
    ]
    samples.extend(qr_samples)

    # ── Fake Customer Care / Support (10) ──────────────────────────
    fake_support = [
        _sample("support-001", "SBI customer care: Your complaint has been registered. Call 1800-123-4567 for immediate resolution.", "scam", "Fake Customer Care", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Fake SBI customer care number", ["phone"], 0.7, 0.95, "Verify independently", "HIGH"),
        _sample("support-002", "Amazon helpdesk: Your order has been cancelled. Refund available. Call 1900-123-456 to process.", "scam", "Fake Customer Care", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Fake Amazon customer care refund", ["phone"], 0.65, 0.9, "Verify independently", "NORMAL"),
        _sample("support-003", "Paytm customer service: Your wallet transaction failed. Call our toll-free 1800-999-8888 for refund.", "scam", "Fake Customer Care", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Fake Paytm support refund", ["phone"], 0.65, 0.9, "Verify independently", "NORMAL"),
        _sample("support-004", "Your credit card has been charged Rs 50000 for Amazon purchase. Dispute: Call 1800-111-2222", "scam", "Fake Customer Care", "HIGH", "HIGH RISK", "Suitable for immediate action", "medium", "en", "sms", "Fake card charge dispute number", ["phone", "currency_amount"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("support-005", "IRCTC helpdesk: Your train ticket is cancelled. Refund processing. Call 1800-111-3333", "scam", "Fake Customer Care", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Fake IRCTC ticket cancellation refund", ["phone"], 0.6, 0.85, "Verify independently", "NORMAL"),
        _sample("support-006", "Google Pay support: Unusual activity on your account. Call 1800-123-9999 immediately to secure.", "scam", "Fake Customer Care", "HIGH", "HIGH RISK", "Suitable for immediate action", "medium", "en", "sms", "Fake GPay support security alert", ["phone"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("support-007", "PhonePe customer care: Your Rs 25000 payment is stuck. Call 1800-222-4444 to resolve.", "scam", "Fake Customer Care", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Fake PhonePe stuck payment support", ["phone", "currency_amount"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("support-008", "Swift customer support: Your parcel is held at customs. Call 1800-333-5555 for clearance.", "scam", "Fake Customer Care", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Fake courier support customs clearance", ["phone"], 0.65, 0.9, "Verify independently", "NORMAL"),
        _sample("support-009", "Microsoft support: Your PC has a virus! Call 1800-444-6666 immediately for free support.", "scam", "Fake Customer Care", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Fake Microsoft tech support call", ["phone"], 0.65, 0.9, "Do not interact", "HIGH"),
        _sample("support-010", "Your card has been blocked due to suspicious transactions. Call SBI support 1800-555-7777 to unblock.", "scam", "Fake Customer Care", "HIGH", "HIGH RISK", "Suitable for immediate action", "medium", "en", "sms", "Card block customer care scam", ["phone", "bank_name"], 0.75, 0.95, "Do not interact", "HIGH"),
    ]
    samples.extend(fake_support)

    # ── Electricity Bill / Utility Scam (6) ────────────────────────
    utilities = [
        _sample("utility-001", "TNEB: Your electricity connection will be disconnected tonight! Pay pending bill Rs 4500: http://tneb-bill.tk", "scam", "Electricity Bill Scam", "CRITICAL", "CRITICAL", "Suitable for immediate action", "easy", "en", "sms", "Immediate disconnection threat", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("utility-002", "Electricity board: Your meter has been tampered. Pay penalty Rs 25000 to avoid FIR. http://elect-penalty.xyz", "scam", "Electricity Bill Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Meter tampering fine threat", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("utility-003", "BSES: Your electricity bill payment failed. Immediate disconnection. Pay now: http://bses-pay.top", "scam", "Electricity Bill Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "BSES disconnection bill scam", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("utility-004", "Current bill pay pannathinga! Disconnect panniduvinga. Link: http://tneb-alert.ga", "scam", "Electricity Bill Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "ta", "sms", "Tamil TNEB disconnection threat", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "HIGH"),
        _sample("utility-005", "LPG subsidy of Rs 1800 is pending in your name. Update bank details: http://lpg-subsidy.tk", "scam", "Government Scheme Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "LPG subsidy bank update scam", ["url", "suspicious_tld"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("utility-006", "Gas connection: Unga subsidy amount Rs 2000 credit aagirukku. Bank details update pannunga: http://gas-subsidy.ml", "scam", "Government Scheme Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "ta", "sms", "Tamil LPG subsidy bank update scam", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "HIGH"),
    ]
    samples.extend(utilities)

    # ── Loan Scam (8) ──────────────────────────────────────────────
    loans = [
        _sample("loan-001", "Personal loan approved! Rs 5 lakhs at 2% interest. Processing fee Rs 2500. Call 1800-123-4567", "scam", "Loan Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Pre-approved loan processing fee", ["phone"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("loan-002", "Instant loan up to Rs 10 lakhs! No paperwork. Low EMI. Processing fee Rs 999. http://loan-offer.tk", "scam", "Loan Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Instant loan with .tk domain", ["url", "suspicious_tld"], 0.85, 1.0, "Block and report", "URGENT"),
        _sample("loan-003", "Bajaj Finserv: Your pre-approved loan of Rs 3 lakhs is ready. Processing fee Rs 1499. http://bajaj-loan.xyz", "scam", "Loan Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Bajaj loan impersonation", ["url", "suspicious_tld"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("loan-004", "Loan 1 minute me! Aadhaar card se. Rs 50000 instantly. Fee Rs 499. http://instant-loan.ml", "scam", "Loan Scam", "HIGH", "HIGH RISK", "Suitable for immediate action", "easy", "en", "sms", "Instant Aadhaar loan scam", ["url", "suspicious_tld"], 0.8, 1.0, "Block and report", "URGENT"),
        _sample("loan-005", "Business loan up to Rs 50 lakhs! Low interest 5%. Processing fee 1%. Contact: loan@easy-finance.tk", "scam", "Loan Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Business loan with suspicious email", ["email", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("loan-006", "Loan app: Quick approval, minimal documents. EMI starts after 90 days. Download: http://loan-app.tk", "scam", "Loan Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Fraud loan app download link", ["url", "suspicious_tld"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("loan-007", "Gold loan: No income proof needed. Rs 2 lakhs loan. Processing fee Rs 1999. Call 1800-777-8888", "scam", "Loan Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Gold loan processing fee scam", ["phone"], 0.65, 0.9, "Do not interact", "NORMAL"),
        _sample("loan-008", "Home loan sanction pannirukkom! Rs 20 lakhs. Processing fee Rs 5000 maatrum. http://home-loan.top", "scam", "Loan Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "ta", "sms", "Tamil home loan processing fee scam", ["url", "suspicious_tld"], 0.7, 0.95, "Do not interact", "HIGH"),
    ]
    samples.extend(loans)

    # ── Legitimate / Safe Messages (20) ────────────────────────────
    legitimate = [
        _sample("legit-001", "Your OTP for SBI transaction is 456782. Do not share this with anyone.", "safe", "Legitimate", "LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate OTP message from bank", [], 0.0, 0.3, "Ignore", "LOW"),
        _sample("legit-002", "Your Aadhaar OTP 783421 is valid for UIDAI authentication. Valid for 10 minutes.", "safe", "Legitimate", "LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate Aadhaar OTP from UIDAI", [], 0.0, 0.3, "Ignore", "LOW"),
        _sample("legit-003", "HDFC Bank: Rs 15000 credited to account 4567 from NEFT transfer. Available balance: Rs 45200.", "safe", "Legitimate", "VERY LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate credit message from bank", ["bank_name", "currency_amount"], 0.0, 0.2, "Ignore", "LOW"),
        _sample("legit-004", "Your Flipkart order OD784512345 has been shipped. Track: https://flipkart.com/track", "safe", "Legitimate", "LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate order shipping message", ["tracking_id", "url"], 0.0, 0.2, "Ignore", "LOW"),
        _sample("legit-005", "Amazon: Your package will be delivered tomorrow between 10AM-2PM. Track here: https://amazon.in/track", "safe", "Legitimate", "VERY LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate Amazon delivery notification", [], 0.0, 0.15, "Ignore", "LOW"),
        _sample("legit-006", "Swiggy: Your order from Saravana Bhavan has been confirmed. ETA 30 mins.", "safe", "Legitimate", "VERY LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate food delivery message", [], 0.0, 0.1, "Ignore", "LOW"),
        _sample("legit-007", "IRCTC: Your train ticket 2456789 for Chennai Express on 15th March is confirmed. PNR: 4785213698", "safe", "Legitimate", "VERY LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate train ticket confirmation", ["tracking_id"], 0.0, 0.15, "Ignore", "LOW"),
        _sample("legit-008", "Your monthly mobile bill of Rs 499 has been paid via auto-debit. Receipt: 7845129630", "safe", "Legitimate", "VERY LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate bill payment receipt", ["currency_amount"], 0.0, 0.15, "Ignore", "LOW"),
        _sample("legit-009", "Income Tax: Your ITR for FY 2024-25 has been successfully filed. Acknowledgement: 478596321478", "safe", "Legitimate", "VERY LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate ITR filing confirmation", ["transaction_id"], 0.0, 0.15, "Ignore", "LOW"),
        _sample("legit-010", "Meeting reminder: Project review tomorrow at 10AM in conference room 3. Please bring status reports.", "safe", "Legitimate", "VERY LOW", "SAFE", "Suitable for normal communication", "easy", "en", "email", "Legitimate meeting reminder", [], 0.0, 0.1, "Ignore", "LOW"),
        _sample("legit-011", "Your appointment with Dr. Patel on 20th March at 11:30 AM is confirmed. Apollo Clinic, T Nagar.", "safe", "Legitimate", "VERY LOW", "SAFE", "Suitable for normal communication", "easy", "en", "sms", "Legitimate doctor appointment", [], 0.0, 0.1, "Ignore", "LOW"),
        _sample("legit-012", "Zomato: Your order #7845 has been delivered! Rate your delivery experience. Have a great day!", "safe", "Legitimate", "VERY LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate Zomato delivery message", [], 0.0, 0.1, "Ignore", "LOW"),
        _sample("legit-013", "Your password was changed successfully. If this was not you, contact support immediately.", "safe", "Legitimate", "LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "email", "Legitimate password change notification", [], 0.0, 0.2, "Monitor", "LOW"),
        _sample("legit-014", "Library reminder: The book 'Wings of Fire' is due for return by 25th March. Late fee applies after that.", "safe", "Legitimate", "VERY LOW", "SAFE", "Suitable for normal communication", "easy", "en", "sms", "Legitimate library book due reminder", [], 0.0, 0.1, "Ignore", "LOW"),
        _sample("legit-015", "Your Netflix subscription of Rs 649 has been renewed. Valid until 15th April 2025.", "safe", "Legitimate", "VERY LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate subscription renewal", ["currency_amount"], 0.0, 0.2, "Ignore", "LOW"),
        _sample("legit-016", "Unlimited 5G data plan activated! Rs 299 for 28 days. Valid on your Airtel number.", "safe", "Legitimate", "LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate telecom plan activation", [], 0.0, 0.2, "Ignore", "LOW"),
        _sample("legit-017", "Your Uber ride to Chennai Airport is confirmed. Driver Rajesh will arrive in 5 mins. Plate: TN07AB1234.", "safe", "Legitimate", "VERY LOW", "SAFE", "Suitable for normal communication", "easy", "en", "sms", "Legitimate Uber ride confirmation", [], 0.0, 0.1, "Ignore", "LOW"),
        _sample("legit-018", "Weekly grocery delivery from BigBasket will arrive tomorrow 7-9AM. Order BB784512.", "safe", "Legitimate", "VERY LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate grocery delivery notification", [], 0.0, 0.1, "Ignore", "LOW"),
        _sample("legit-019", "Your EPFO passbook has been updated. View your PF balance on the UMANG app or EPFO portal.", "safe", "Legitimate", "LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate EPFO passbook update", [], 0.0, 0.2, "Monitor", "LOW"),
        _sample("legit-020", "Your credit card bill of Rs 12500 is due on 5th April. Auto-pay is enabled. Sufficient balance confirmed.", "safe", "Legitimate", "VERY LOW", "LOW RISK", "Suitable for normal communication", "easy", "en", "sms", "Legitimate credit card bill notification", ["currency_amount"], 0.0, 0.15, "Ignore", "LOW"),
    ]
    samples.extend(legitimate)

    # ── Mixed / Ambiguous / Edge Cases (10) ────────────────────────
    mixed = [
        _sample("mixed-001", "Your account has been credited with Rs 1000. Thank you for being a valued customer.", "safe", "Legitimate", "LOW", "LOW RISK", "Suitable for normal communication", "medium", "en", "sms", "Generic credit - looks like bank message", ["currency_amount"], 0.0, 0.3, "Ignore", "LOW"),
        _sample("mixed-002", "Dear customer, your policy premium is due. Pay Rs 5000 to avoid lapse. http://insurance-pay.tk", "scam", "Loan Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Insurance payment with suspicious link", ["url", "suspicious_tld", "currency_amount"], 0.7, 0.95, "Do not interact", "HIGH"),
        _sample("mixed-003", "Free consultation! Our financial advisor will call you. Reply YES for callback.", "safe", "Legitimate", "LOW", "LOW RISK", "Suitable for normal communication", "hard", "en", "sms", "Legal consultation service - no scam indicators", [], 0.0, 0.2, "Ignore", "LOW"),
        _sample("mixed-004", "Win a free iPhone! Click the link and participate. http://survey-free.tk", "scam", "Lottery Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Free iPhone survey link", ["url", "suspicious_tld"], 0.6, 0.85, "Do not interact", "NORMAL"),
        _sample("mixed-005", "Neraya lucky draw! Unga phone number winner aagirukku! Rs 5000 cash prize. Call pannunga now!", "scam", "Lottery Scam", "MEDIUM", "SUSPICIOUS", "Further assessment required", "hard", "ta", "sms", "Tamil lucky draw - no URL, just phone", [], 0.55, 0.85, "Do not interact", "NORMAL"),
        _sample("mixed-006", "Hi, remember me? I got your number from Suresh. Need to discuss something urgent. Please call back.", "safe", "Legitimate", "LOW", "SAFE", "Suitable for normal communication", "hard", "en", "sms", "Personal message from acquaintance", [], 0.0, 0.15, "Ignore", "LOW"),
        _sample("mixed-007", "Free laptop! Government scheme for students. Register with Rs 200 registration fee: http://student-scheme.tk", "scam", "Government Scheme Scam", "HIGH", "HIGH RISK", "Suitable for security investigation", "medium", "en", "sms", "Student scheme scam with registration fee", ["url", "suspicious_tld"], 0.75, 0.95, "Do not interact", "HIGH"),
        _sample("mixed-008", "Thank you for your recent purchase. Your feedback matters. Complete survey and get 10% off next order.", "safe", "Legitimate", "LOW", "LOW RISK", "Suitable for normal communication", "hard", "en", "email", "Genuine post-purchase survey request", [], 0.0, 0.2, "Ignore", "LOW"),
        _sample("mixed-009", "Congratulations! You have been pre-selected for our credit card with Rs 5 lakh limit. Terms apply.", "safe", "Legitimate", "LOW", "LOW RISK", "Suitable for normal communication", "hard", "en", "sms", "Genuine credit card pre-approval", [], 0.0, 0.25, "Monitor", "LOW"),
        _sample("mixed-010", "Your vehicle insurance expires in 7 days. Renew now to avoid penalty. https://renew-insure.tk", "scam", "Phishing", "MEDIUM", "SUSPICIOUS", "Further assessment required", "medium", "en", "sms", "Insurance renewal with suspicious domain", ["url", "suspicious_tld"], 0.6, 0.85, "Verify independently", "NORMAL"),
    ]
    samples.extend(mixed)

    return samples


def generate_benchmark(output_path: str) -> None:
    samples = build_dataset()
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

    scam = sum(1 for s in samples if s["expected_prediction"] == "scam")
    safe = sum(1 for s in samples if s["expected_prediction"] == "safe")
    categories = {}
    langs = {}
    difficulties = {}
    for s in samples:
        cat = s["expected_category"]
        categories[cat] = categories.get(cat, 0) + 1
        lang = s["language"]
        langs[lang] = langs.get(lang, 0) + 1
        diff = s["difficulty"]
        difficulties[diff] = difficulties.get(diff, 0) + 1

    print(f"Dataset generated: {len(samples)} samples")
    print(f"  Output: {output_path}")
    print(f"  Scam: {scam}, Safe: {safe}")
    print(f"  Categories: {len(categories)}")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count}")
    print(f"  Languages: {langs}")
    print(f"  Difficulties: {difficulties}")


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "datasets", "benchmark.json"
    )
    generate_benchmark(path)
