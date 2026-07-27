__all__ = [
    "CATEGORY_KEYWORDS", "UNKNOWN_CATEGORY", "CATEGORY_THREATS", "CATEGORY_RECOMMENDATIONS",
    "FAMILY_FINANCIAL_FRAUD", "FAMILY_CREDENTIAL_THEFT", "FAMILY_SOCIAL_ENGINEERING",
    "FAMILY_CONSUMER_FRAUD", "FAMILY_LEGITIMATE",
    "SUBFAMILY_BANKING", "SUBFAMILY_UPI", "SUBFAMILY_LOAN", "SUBFAMILY_INVESTMENT",
    "SUBFAMILY_CRYPTO", "SUBFAMILY_KYC", "SUBFAMILY_OTP", "SUBFAMILY_FAKE_LOGIN",
    "SUBFAMILY_IDENTITY_THEFT", "SUBFAMILY_FAKE_SUPPORT", "SUBFAMILY_GOVERNMENT",
    "SUBFAMILY_DELIVERY", "SUBFAMILY_CUSTOMS", "SUBFAMILY_LOTTERY", "SUBFAMILY_SUBSCRIPTION",
    "SUBFAMILY_PRIZE", "SUBFAMILY_SAFE", "SUBFAMILY_GENERAL",
    "ATTACKER_GOALS", "VICTIM_IMPACTS",
]

from typing import Dict, Tuple

CATEGORY_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "Bank KYC Scam": (
        "kyc", "aadhaar", "aadhar", "sbi", "hdfc", "icici", "axis", "kotak",
        "pnb", "canara", "bob", "indusind", "bank", "account will be",
        "deactivate", "blocked", "freeze", "suspended",
    ),
    "Lottery Scam": (
        "lottery", "won", "prize", "winner", "jackpot", "claim",
        "cashback", "refund",
    ),
    "Job Scam": (
        "work from home", "part-time", "data entry", "registration fee",
        "exam fee", "job", "salary", "processing fee",
    ),
    "UPI Scam": (
        "upi", "gpay", "phonepe", "paytm", "bhim", "amazon pay", "qr code",
    ),
    "Investment Scam": (
        "investment", "profit", "guaranteed", "return", "earn", "income",
        "scheme", "installment",
    ),
    "Courier Scam": (
        "courier", "parcel", "customs", "clearance", "release fee",
        "shipment", "package", "import",
    ),
    "Government Scheme Scam": (
        "pm", "modi", "sarkari", "government of india", "central govt",
        "subsidy", "pension", "nrega", "ayushman",
    ),
    "Electricity Bill Scam": (
        "electricity", "bill", "tneb", "disconnection", "disconnected",
    ),
    "Customs Scam": (
        "customs", "clearance", "illegal", "release fee", "seized",
    ),
    "Loan Scam": (
        "loan", "emi", "processing fee", "personal loan", "credit",
    ),
    "Fake Customer Care": (
        "customer care", "toll free", "helpdesk", "support", "helpline",
        "customer service",
    ),
    "QR Code Scam": (
        "qr code", "scan",
    ),
    "Crypto Scam": (
        "bitcoin", "crypto", "cryptocurrency", "blockchain", "btc", "eth",
    ),
}

UNKNOWN_CATEGORY: str = "Unknown Scam"

CATEGORY_THREATS: Dict[str, Dict[str, str]] = {
    "Bank KYC Scam": {"primary": "Financial Theft", "secondary": "Identity Theft", "victim_impact": "Bank Account Compromise"},
    "Lottery Scam": {"primary": "Financial Fraud", "secondary": "Advance Fee Fraud", "victim_impact": "Monetary Loss"},
    "Job Scam": {"primary": "Employment Fraud", "secondary": "Identity Theft", "victim_impact": "Loss of Personal Data and Money"},
    "UPI Scam": {"primary": "Financial Theft", "secondary": "Credential Harvesting", "victim_impact": "UPI Account Drain"},
    "Investment Scam": {"primary": "Investment Fraud", "secondary": "Ponzi Scheme", "victim_impact": "Long-term Financial Loss"},
    "Courier Scam": {"primary": "Advance Fee Fraud", "secondary": "Impersonation Fraud", "victim_impact": "Monetary Loss via Fake Fees"},
    "Government Scheme Scam": {"primary": "Government Impersonation", "secondary": "Identity Theft", "victim_impact": "Misuse of Aadhaar/Personal Data"},
    "Electricity Bill Scam": {"primary": "Utility Fraud", "secondary": "Impersonation Fraud", "victim_impact": "False Payment Collection"},
    "Customs Scam": {"primary": "Advance Fee Fraud", "secondary": "Impersonation Fraud", "victim_impact": "Loss of Money via Fake Customs Fees"},
    "Loan Scam": {"primary": "Loan Fraud", "secondary": "Advance Fee Fraud", "victim_impact": "Upfront Fee Loss and Identity Theft"},
    "Fake Customer Care": {"primary": "Technical Support Fraud", "secondary": "Remote Access Scam", "victim_impact": "Account Takeover and Financial Loss"},
    "QR Code Scam": {"primary": "Payment Fraud", "secondary": "Credential Harvesting", "victim_impact": "UPI/Bank Account Drain"},
    "Crypto Scam": {"primary": "Cryptocurrency Fraud", "secondary": "Investment Fraud", "victim_impact": "Loss of Cryptocurrency Assets"},
    "Unknown Scam": {"primary": "Unsolicited Message", "secondary": "Social Engineering", "victim_impact": "Potential Financial or Data Loss"},
}

CATEGORY_RECOMMENDATIONS: Dict[str, Tuple[str, ...]] = {
    "Bank KYC Scam": (
        "Do not click any links claiming KYC update",
        "Never share OTP, PIN, or password with anyone",
        "Contact your bank directly using the official customer care number",
        "Report to cybercrime.gov.in or forward message to 1930",
    ),
    "Lottery Scam": (
        "Lotteries requiring payment to claim prizes are always fake",
        "Do not respond to unsolicited prize notifications",
        "Never pay advance fees to claim winnings",
        "Block and report the sender",
    ),
    "Job Scam": (
        "Legitimate employers never charge registration or exam fees",
        "Verify the company independently before sharing personal data",
        "Do not pay any upfront fees for job offers",
        "Report suspicious job offers to cybercrime.gov.in",
    ),
    "UPI Scam": (
        "Never share UPI PIN or scan unknown QR codes",
        "Do not approve payment requests from unknown senders",
        "Verify payment requests through the official app only",
        "Report fraud to your bank and cybercrime.gov.in immediately",
    ),
    "Investment Scam": (
        "Unsolicited investment offers promising high returns are scams",
        "Verify the investment scheme with SEBI before investing",
        "Never invest based on SMS or WhatsApp messages",
        "Report fraudulent schemes to SEBI and cybercrime.gov.in",
    ),
    "Courier Scam": (
        "Customs or courier companies never request payment via SMS",
        "Track parcels using official courier websites only",
        "Do not pay any release fee or customs charge through SMS links",
        "Report courier scams to cybercrime.gov.in",
    ),
    "Government Scheme Scam": (
        "Government schemes never ask for OTP or bank details via SMS",
        "Verify scheme details on official government websites only",
        "Do not share Aadhaar or bank account details in response to SMS",
        "Report impersonation of government officials to cybercrime.gov.in",
    ),
    "Electricity Bill Scam": (
        "Electricity boards do not threaten immediate disconnection via SMS",
        "Verify outstanding bills on the official electricity board portal",
        "Do not make payments through links in SMS messages",
        "Report fraudulent disconnection threats to the local electricity office",
    ),
    "Customs Scam": (
        "Customs departments do not request clearance fees via SMS",
        "Do not pay any fees to release parcels through SMS instructions",
        "Verify shipment status on official courier tracking portals",
        "Report customs fraud to cybercrime.gov.in",
    ),
    "Loan Scam": (
        "Legitimate lenders do not ask for advance processing fees",
        "Verify the lender's registration with RBI before proceeding",
        "Never share bank account or KYC details via SMS",
        "Report illegal lending apps and SMS to cybercrime.gov.in",
    ),
    "Fake Customer Care": (
        "Always use the official customer care number from the company website",
        "Never share OTP, password, or remote access to your phone",
        "Customer care agents never ask for UPI PIN or banking passwords",
        "Report fake customer care numbers to the platform and cybercrime.gov.in",
    ),
    "QR Code Scam": (
        "Never scan QR codes from unknown or unsolicited messages",
        "Verify the payment screen before entering UPI PIN",
        "QR code payments should only be used for in-person transactions",
        "Report QR code fraud to your bank immediately",
    ),
    "Crypto Scam": (
        "Unsolicited cryptocurrency investment offers are always scams",
        "Verify any crypto scheme with SEBI or RBI before investing",
        "Never share wallet private keys or recovery phrases",
        "Report crypto scams to cybercrime.gov.in",
    ),
    "Unknown Scam": (
        "Do not click any links in unsolicited messages",
        "Never share OTP, passwords, or banking details via SMS",
        "Verify the sender independently before taking any action",
        "Report suspicious messages to cybercrime.gov.in or forward to 1930",
    ),
}

FAMILY_FINANCIAL_FRAUD: str = "Financial Fraud"
FAMILY_CREDENTIAL_THEFT: str = "Credential Theft"
FAMILY_SOCIAL_ENGINEERING: str = "Social Engineering"
FAMILY_CONSUMER_FRAUD: str = "Consumer Fraud"
FAMILY_LEGITIMATE: str = "Legitimate"

SUBFAMILY_BANKING: str = "Banking"
SUBFAMILY_UPI: str = "UPI"
SUBFAMILY_LOAN: str = "Loan"
SUBFAMILY_INVESTMENT: str = "Investment"
SUBFAMILY_CRYPTO: str = "Crypto"
SUBFAMILY_KYC: str = "KYC"
SUBFAMILY_OTP: str = "OTP"
SUBFAMILY_FAKE_LOGIN: str = "Fake Login"
SUBFAMILY_IDENTITY_THEFT: str = "Identity Theft"
SUBFAMILY_FAKE_SUPPORT: str = "Fake Support"
SUBFAMILY_GOVERNMENT: str = "Government"
SUBFAMILY_DELIVERY: str = "Delivery"
SUBFAMILY_CUSTOMS: str = "Customs"
SUBFAMILY_LOTTERY: str = "Lottery"
SUBFAMILY_SUBSCRIPTION: str = "Subscription"
SUBFAMILY_PRIZE: str = "Prize"
SUBFAMILY_SAFE: str = "Safe"
SUBFAMILY_GENERAL: str = "General"

ATTACKER_GOALS: Dict[str, str] = {
    "Bank KYC Scam": "Harvest banking credentials and OTPs to gain unauthorized account access.",
    "Lottery Scam": "Trick victim into paying advance fees for a non-existent prize.",
    "Job Scam": "Collect personal data and registration fees from job seekers.",
    "UPI Scam": "Initiate fraudulent UPI payments or steal UPI credentials.",
    "Investment Scam": "Convince victim to invest in a fraudulent scheme with promised high returns.",
    "Courier Scam": "Extract advance fee payments for fake customs clearance.",
    "Government Scheme Scam": "Impersonate government to steal Aadhaar or bank details.",
    "Electricity Bill Scam": "Collect payment for fake electricity dues.",
    "Customs Scam": "Demand fraudulent customs clearance fees for seized parcels.",
    "Loan Scam": "Collect upfront processing fees for fake loan approvals.",
    "Fake Customer Care": "Gain remote access or credentials by impersonating support staff.",
    "QR Code Scam": "Redirect payment via fraudulent QR codes to attacker accounts.",
    "Crypto Scam": "Convince victim to transfer cryptocurrency to a fraudulent wallet.",
}

VICTIM_IMPACTS: Dict[str, str] = {
    "Bank KYC Scam": "Unauthorized bank access, fund theft, and identity compromise.",
    "Lottery Scam": "Direct monetary loss from advance fee payments.",
    "Job Scam": "Loss of registration fee and potential identity theft.",
    "UPI Scam": "Direct financial loss via unauthorized UPI transactions.",
    "Investment Scam": "Long-term financial loss from fraudulent investments.",
    "Courier Scam": "Monetary loss through fake customs fee payments.",
    "Government Scheme Scam": "Misuse of Aadhaar and personal identification documents.",
    "Electricity Bill Scam": "Loss of payment to fraudulent collection channels.",
    "Customs Scam": "Monetary loss via fraudulent clearance fee demands.",
    "Loan Scam": "Upfront fee loss and potential identity misuse.",
    "Fake Customer Care": "Account takeover and unauthorized financial transactions.",
    "QR Code Scam": "Immediate bank account or UPI wallet drain.",
    "Crypto Scam": "Irreversible loss of cryptocurrency assets.",
}
