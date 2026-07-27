import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def scam_samples():
    return {
        "bank_kyc": [
            "URGENT: Your SBI account will be deactivated. Update KYC immediately: https://sbi-kyc.xyz",
            "Your HDFC bank account has been blocked due to incomplete KYC. Update now: http://hdfc-verify.tk",
            "Axis Bank Alert: Your debit card is suspended. Complete KYC verification at https://axis-update.cf",
            "ICICI Bank: Your account will be frozen in 24 hours. Submit KYC documents at https://icici-verify.xyz",
            "SBI Alert: Your account is deactivated. Update Aadhaar linked KYC immediately to avoid permanent closure.",
        ],
        "lottery": [
            "Congratulations! You won 50 Lakh in our mega lottery. Call +91-9876543210 now to claim your prize!",
            "You have won 25 Lakhs in the Amazon iPhone giveaway. Pay 2000 processing fee to claim your prize.",
            "WINNER: You won 1 Crore in the Flipkart Diwali draw. Contact agent within 24 hours.",
            "Congratulations! Your mobile number won 15 Lakh in the Tata Motors lucky draw. Call now to claim.",
            "You won a free iPhone 15! Click https://free-iphone-winner.tk to claim your gift now.",
        ],
        "job": [
            "Work from home job - earn 50000/month. Registration fee 500 required.",
            "Part time data entry job. Earn 30000 per month. Register with 1000 processing fee.",
            "URGENT HIRING: Online work from home. Salary 40000/month. Pay 2000 for training materials.",
            "Make money from home! Earn 1000 per day. Join our franchise for just 500 rupees.",
            "Amazon work from home jobs. Earn 45000 monthly. Registration fee 1500 refundable.",
        ],
        "upi": [
            "Your UPI transaction of 15000 is pending. Confirm now to avoid penalty: https://paytm-upi.tk",
            "PhonePe: 8500 INR debited from your account. Not you? Call 1800-XXX-XXXX immediately.",
            "Google Pay: Your account sent 12000 to an unknown beneficiary. Dispute now: https://gpay-secure.cf",
            "UPI transaction failed. Update your UPI PIN to complete refund: http://upi-verify.xyz",
            "Your BHIM UPI account has been temporarily blocked. Verify identity at https://bhim-secure.tk",
        ],
        "investment": [
            "URGENT: Double your investment in 30 days! Guaranteed returns. Limited offer. Contact now.",
            "Get 5% daily returns on your investment. Minimum 10000. No risk, guaranteed profit.",
            "Forex trading: Turn 5000 into 50000 in one month. Join our expert group. Registration fee required.",
            "Mutual fund with 30% monthly returns guaranteed. Limited seats. Invest minimum 25000 today.",
            "Stock market tips - 500% returns guaranteed. Pay 5000 for lifetime membership. Act now!",
        ],
        "courier": [
            "Your courier parcel from Dubai is held at customs. Pay 5000 release fee to clear it.",
            "DHL: Your international package is detained. Pay 3500 for customs clearance.",
            "Your Amazon parcel from USA is stuck at Mumbai customs. Release fee 4000 required.",
            "FedEx: Shipment containing valuables detained by customs. Pay 6000 for clearance.",
            "Your imported goods are held at Chennai port. Customs release fee 8000 needed.",
        ],
        "government_scheme": [
            "PM Modi's new subsidy scheme: Get 50000 in your account. Click http://modi-scheme.tk to apply.",
            "Government of India: You are eligible for PM Awas Yojana subsidy of 2.5 Lakh. Register now.",
            "Ayushman Bharat: Free health insurance of 5 Lakh. Update your documents to activate.",
            "PM Kisan Samman Nidhi: Your 6000 installment is pending. Verify account at https://pmkisan.cf",
            "Sarkari Yojana: 50000 direct benefit transfer approved. Click to claim: http://govt-benefit.xyz",
        ],
        "electricity_bill": [
            "TNEB: Your electricity bill is overdue. Disconnection in 24 hours. Pay now via https://tneb-bill.tk",
            "Electricity Board: Your power connection will be disconnected for non-payment. Make immediate payment.",
            "MSEDCL Alert: Final notice before disconnection. Click http://mahavitaran-bill.cf to pay.",
            "BESCOM: Your electricity bill payment failed. Reconnect fee of 500 applicable. Pay at https://bescom-pay.xyz",
            "TANGEDCO: Disconnection notice served. Pay outstanding 2500 immediately to avoid power cut.",
        ],
        "customs": [
            "Customs seized your parcel. Pay 25000 clearance fee.",
            "Customs Department: Your shipment contains undeclared items. Pay 12000 penalty to release.",
            "International package held by customs. Illegal contents detected. Pay 15000 for clearance.",
            "Your shipment from China is detained by Indian Customs. Clearance fee 30000 required.",
            "Customs alert: Prohibited items found in your parcel. Pay 20000 fine to avoid legal action.",
        ],
        "loan": [
            "Personal loan approved! 10 Lakh at 2% interest. Pay 2000 processing fee.",
            "Loan of 5 Lakhs pre-approved for you. 0% EMI for 12 months. Processing fee 1500.",
            "Instant loan up to 25 Lakhs. No CIBIL required. Pay 3000 for fast processing.",
            "Business loan of 50 Lakhs sanctioned. Disbursement after 5000 processing fee.",
            "Home loan at 3% interest approved. Pay 10000 for documentation and processing.",
        ],
        "fake_customer_care": [
            "Your Amazon account compromised! Call our customer care at 1800-123-4567.",
            "Microsoft Alert: Your computer has a virus. Call our support immediately at +1-800-XXX-XXXX.",
            "Netflix: Your account is suspended. Call customer care at 1800-XXX-XXXX to reactivate.",
            "Google Support: Suspicious login detected. Call 1800-XXX-XXXX to secure your account.",
            "Your Apple ID has been locked. Call Apple Care at 1-800-XXX-XXXX for verification.",
        ],
        "qr_code": [
            "Scan the QR code below to receive 5000 cashback from PhonePe.",
            "QR code attached for instant lottery credit. Scan now to claim your prize.",
            "Flipkart gift voucher QR code. Scan to redeem 2500 worth of shopping credit.",
            "Pay your bill using this QR code for instant 50% discount: [QR]",
            "QR code for COVID-19 financial aid. Scan to receive 10000 from government scheme.",
        ],
        "crypto": [
            "Bitcoin investment! Turn 10000 into 1 Lakh in one week.",
            "Invest in our crypto trading platform. Earn 10% daily returns. Minimum investment 5000.",
            "BitDoubler: Double your Bitcoin in 24 hours. Trusted by 50000+ investors.",
            "Ethereum mining pool membership. Earn 0.5 ETH per day. Registration fee 0.1 BTC.",
            "Crypto signal group: 95% win rate. Lifetime membership 10000 INR only.",
        ],
    }


@pytest.fixture(scope="session")
def safe_samples():
    return [
        "Hi mom, I reached home safely. Will call you in the evening.",
        "Your meeting with HR is scheduled for 3 PM tomorrow. Please be on time.",
        "The project deadline has been extended to next Friday. Update your task list accordingly.",
        "Flight 6E-123 to Mumbai is boarding at Gate 12. Please proceed to boarding.",
        "Your train PNR confirmation for booking #87654321 has been received.",
        "Reminder: Team standup meeting at 9:30 AM in Conference Room B.",
        "Your Swiggy One membership has been renewed. Valid until December 2026.",
        "Passport application status: Your passport is ready for collection at the Passport Seva Kendra.",
        "Dear student, your semester exam results have been published on the university portal.",
        "Gas booking confirmed for cylinder #98765. Delivery within 5 working days.",
        "Hi, can we reschedule our meeting to Friday afternoon?",
        "Don't forget to bring the project documents to the client presentation tomorrow.",
        "Your parking permit renewal has been approved. Valid until March 2027.",
        "The grocery delivery will arrive between 6 PM and 8 PM tonight.",
        "Library book due date reminder: please return 'Introduction to Machine Learning' by Friday.",
        "Weather alert: Heavy rainfall expected in your area tomorrow. Stay safe.",
        "Your gym membership renewal is due next month. Early renewal gets 10% discount.",
        "Movie tickets confirmed for Saturday 7 PM show at PVR Cinemas.",
        "School parent-teacher meeting scheduled for 10 AM on Saturday.",
        "Your internet plan auto-renews on 5th of next month. Current speed 100 Mbps.",
    ]


@pytest.fixture(scope="session")
def language_samples():
    return {
        "en": {
            "scam": [
                "URGENT: Your bank account is compromised. Call immediately to secure your funds.",
                "Congratulations! You won a luxury car. Claim your prize by paying registration fee.",
            ],
            "safe": [
                "I will meet you at the coffee shop near the office at 5 PM.",
                "Please find the quarterly report attached for your review.",
            ],
        },
        "hi-en": [
            "Aapka SBI account block ho gaya hai. KYC update karein: https://sbi-secure.tk",
            "Aapne 25 lakh jeete hain. Claim karne ke liye 2000 registration fee pay karein.",
            "Ghar baithe job karein, 50000 mahina salary. Registration fee 500.",
            "UPI transaction failed. Kripya apna PIN update karein: http://paytm-upi.cf",
            "PM Modi sarkari yojana: 50000 aapke khate mein. Abhi register karein.",
            "Bijli bill pending hai. Aaj hi pay nahi kiya to connection cut ho jayega.",
            "Aapka courier parcel customs mein phansa hai. 5000 clearance fee pay karein.",
            "Personal loan 10 lakh 2% interest par approved. 2000 processing fee pay karein.",
            "Bitcoin mein invest karein. 1 lakh banao 10000 se ek hafte mein.",
            "Customer care: Aapka Amazon account compromised hai. Turant call karein 1800-XXX-XXXX.",
        ],
        "ta": [
            "உங்கள் SBI கணக்கு முடக்கப்பட்டுள்ளது. உடனடியாக KYC புதுப்பிக்கவும்: https://sbi-kyc.tk",
            "வாழ்த்துக்கள்! நீங்கள் 50 லட்சம் லாட்டரி வென்றுள்ளீர்கள். 2000 கட்டணம் செலுத்தி பரிசை கோரவும்.",
            "வீட்டில் இருந்தபடியே வேலை செய்யுங்கள். மாதம் 50000 சம்பளம். பதிவு கட்டணம் 500.",
            "உங்கள் UPI பரிவர்த்தனை தோல்வியடைந்தது. உடனடியாக UPI PIN புதுப்பிக்கவும்: https://gpay-verify.cf",
            "புதிய மோடி அரசு திட்டம்: உங்கள் கணக்கில் 50000 ரூபாய் வரவு வைக்கப்படும்.",
            "மின்சார கட்டணம் நிலுவையில் உள்ளது. 24 மணி நேரத்தில் இணைப்பு துண்டிக்கப்படும்.",
            "உங்கள் சர்வதேச பொட்டலம் சுங்கத்தில் நிறுத்தி வைக்கப்பட்டுள்ளது. 5000 அனுமதி கட்டணம் செலுத்தவும்.",
            "தனிநபர் கடன் 10 லட்சம் 2% வட்டியில் அங்கீகரிக்கப்பட்டுள்ளது. 2000 செயலாக்க கட்டணம்.",
            "பிட்காயின் முதலீடு! 10000 ஐ 1 லட்சமாக மாற்றவும் ஒரே வாரத்தில்.",
            "உங்கள் Amazon கணக்கு ஹேக் செய்யப்பட்டுள்ளது. உடனடியாக 1800-XXX-XXXX ஐ அழைக்கவும்.",
        ],
        "tangling": [
            "Unga SBI account block aagirukku. Udanadi KYC update pannunga: https://sbi-secure.tk",
            "Congratulations! Ungaluku 25 lakh lottery vittirukku. Claim panna 2000 registration fee kattanum.",
            "Veetla iruntha job pannalam. 50000/month salary. Registration fee 500.",
            "Unga UPI transaction failed aagirukku. Udanadi UPI PIN update pannunga.",
            "PM Modi subsidy scheme: Unga account ku 50000 varum. Ippave register pannunga.",
            "Electricity bill outstanding irukku. Innaike pay pannala na connection cut aagidum.",
            "Unga courier parcel customs la stuck aagirukku. 5000 clearance fee kattanum.",
            "Personal loan 10 lakh 2% interest ku approved aagirukku. 2000 processing fee.",
            "Bitcoin investment! 10000 ah 1 lakh ah maathalam oru week la.",
            "Unga Amazon account compromised aagirukku. Customer care ku call pannunga 1800-XXX-XXXX.",
        ],
    }
