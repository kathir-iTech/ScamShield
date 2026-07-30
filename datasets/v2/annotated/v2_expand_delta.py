import csv, json, logging, os, random, re, sys, copy
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("v2-delta")

random.seed(42)

GAMMA_PATH = Path(r"D:\Developer\Desktop\ScamShield\datasets\v2\annotated\dataset_v2_gamma.csv")
OUTPUT_PATH = Path(r"D:\Developer\Desktop\ScamShield\datasets\v2\annotated\dataset_v2_gamma.csv")
BACKEND_COPY = Path(r"D:\Developer\Desktop\ScamShield\backend\data\dataset_v2_gamma.csv")

SCAM_WORDS = ["alert", "urgent", "immediately", "suspend", "deactivate", "block", "freeze", "action required", "security", "fraud", "unauthorized", "verify", "OTP", "limited period", "legal action", "arrest warrant", "income tax", "refund", "credit", "winning", "lottery", "reward", "cashback", "gift", "exclusive offer"]

def load_existing(path):
    texts = set()
    rows = []
    max_ids = defaultdict(int)
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.add(row.get("text", "").strip().lower())
            rows.append(row)
            cat = row["category"]
            idx = int(row["id"].split("_")[-1]) if "_" in row["id"] else 0
            if idx > max_ids[cat]:
                max_ids[cat] = idx
    return rows, texts, max_ids

def make_id(category, index):
    return f"{category}_{index:04d}"

def make_sample(text, category, is_scam, risk, language="en", source="synthetic", index=0):
    text_clean = text.strip().lower()
    gt = "scam" if is_scam else "legitimate"
    entities = {
        "urls": re.findall(r'https?://[^\s,]+', text),
        "phones": re.findall(r'\b\d{4,6}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b', text),
        "emails": re.findall(r'\b[\w.%-]+@[\w.-]+\.[A-Za-z]{2,4}\b', text),
    }
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
        "annotation_notes": "Delta expansion for weak category.",
        "created_at": now,
        "updated_at": now,
    }

OTP_SCAM_TEXTS = [
    "IRCTC: OTP 945612 for booking cancellation of PNR 4567890123. If not authorised, share OTP with support.",
    "Google verification code is 482916. Do not share this code. If you received this by mistake, forward to 9988776655.",
    "Telegram: Login OTP 782345. Someone is trying to access your account from Hyderabad. Forward OTP to stop.",
    "SBI OTP 891234 for transfer of Rs 45,000 to account XX6789. If not you, call 1800-425-3800 immediately.",
    "GPay transaction OTP: 623489. Amount: Rs 12,500 to Paytm merchant. Not you? Share OTP to reverse.",
    "Facebook: OTP 784512 for password reset. If not you, reply with OTP to secure your account.",
    "Amazon OTP: 563412 for login from Delhi. If not you, call Amazon support at 1800-3000-1234.",
    "Paytm: OTP 890123 for wallet transfer of Rs 25,000. Not you? Send OTP to block transaction.",
    "Aadhaar OTP: 452389 for updating mobile number. If not requested, call 1947 immediately.",
    "WhatsApp: Your OTP is 673489. Do not share. If not you, forward to 9876543210 to deactivate.",
    "Flipkart: OTP 561234 for order cancellation of Rs 12,499. Not authorised? Share OTP to seller.",
    "PhonePe: OTP 345678 for adding new beneficiary Rahul. If not you, forward OTP to block.",
    "Netflix: OTP 234567 for account recovery. If you did not request this, share OTP to lock account.",
    "Instagram: OTP 789012 for login from unknown device. Reply with OTP to secure your account.",
    "Microsoft: OTP 901234 for account password reset. Forward to 9988776655 if not you.",
    "Aapka Google OTP 456789 hai. Kisi ke saath share na karein. Galati se aaya hai to 9988776655 par forward karein.",
    "Amazon pe order cancel karne ke liye OTP 567890. Share karo delivery boy ke saath.",
    "PhonePe se Rs 5,000 transfer karne ke liye OTP 678901. Not you? 1800-123-4567 pe call karein.",
    "Facebook account hack ho gaya hai. OTP 789012 forward karo is number pe 9988776655 for recovery.",
    "Google pay transaction OTP 890123. Payment of Rs 15,000 to Ajay. Not you? Call immediately.",
    "LinkedIn: Your account will be permanently deleted. OTP 901234. Share to cancel deletion.",
    "Twitter: OTP 123456 for verification. Forward to 9876543210 if you did not request.",
    "Snapchat: OTP 234567 for password change. Kisi ko na bataye. Galat hai to forward karein.",
    "Zomato: OTP 345678 for account deactivation. Not requested? Share OTP with agent to stop.",
    "Swiggy: OTP 456789 for refund of Rs 450. Share with our executive for processing.",
    "IRCTC OTP 567890 hai. PNR cancellation ke liye. Kisi ko share na karein.",
    "PayPal: OTP 678901 for transaction of $450. Not you? Call 1800-123-456 immediately.",
    "WhatsApp verification code 789012. Do not share this code with anyone. If not you, forward to 9988776655.",
    "Tinder: OTP 890123 for account recovery. If you did not request, forward OTP to deactivate.",
    "Telegram group: OTP 901234 to join premium channel. Forward to admin if not requested.",
    "Amazon OTP 123478 for delivery reschedule. Share with delivery partner if needed.",
    "GPay autopay OTP 234589 for Rs 2,500 monthly. Cancel by sharing OTP to 1800-180-1234.",
    "SBI Card: OTP 345690 for online transaction Rs 67,000. If not you, call 1800-123-4567 now.",
    "HDFC OTP 456701 for adding payee Rahul Sharma. If not you, please call immediately.",
    "ICICI: OTP 567812 for fund transfer Rs 1,25,000. Not you? Block now at http://icici-block.xyz.",
    "Your Apple ID verification code: 678923. Do not share. Forward to support if unexpected.",
    "Razorpay: OTP 789034 for subscription of Rs 999/month. Not you? Share OTP to cancel.",
    "Google Ads: OTP 890145 for account suspension. If not you, call Google support.",
    "CoinDCX: OTP 901256 for crypto withdrawal of 0.5 BTC. Not authorised? Call immediately.",
    "Zerodha: OTP 123467 for demat account transfer. Forward OTP to block if not you.",
    "Upstox: OTP 234578 for adding bank account. Not you? Call 1800-120-4567 right now.",
    "CRED: OTP 345689 for credit card bill payment Rs 34,000. Share to reverse if not you.",
    "MobiKwik: OTP 456790 for wallet reload Rs 5,000. Not requested? Call support now.",
    "FreeCharge: OTP 567801 for transaction Rs 2,500. Forward to 9988776655 if not authorised.",
    "Airtel Payments Bank: OTP 678912 for account opening. If not you, call 121 immediately.",
    "Jio Payments Bank: OTP 789023 for KYC update. Forward OTP to 9876543210 if not requested.",
    "RBL Bank: OTP 890134 for credit card issuance. Not you? Share OTP to cancel application.",
    "IDFC Bank: OTP 901245 for adding nominee. Forward to 9988776655 if not authorised.",
    "Yes Bank: OTP 123456 for online banking registration. Call 1800-258-4567 if not you.",
    "Kotak 811: OTP 234567 for mobile number change. Share OTP with executive to verify.",
    "Axis Bank: OTP 345678 for resetting net banking password. Share OTP to block if not you.",
    "PNB OTP 456789 for account reactivation. Forward to 1800-120-1234 if not requested.",
    "BOB OTP 567890 for linking Aadhaar with account. Forward OTP if not you.",
    "Canara Bank OTP 678901 for updating address. Share OTP with our representative.",
    "Indian Bank OTP 789012 for e-statement generation. Not you? Call branch immediately.",
    "Bank of India OTP 890123 for adding SMS banking. Forward priority if not you.",
]

LEGIT_PERSONAL_TEXTS = [
    "Hey, are we still on for dinner tonight? I'll book the table at 7.",
    "Mom, I reached the hotel safely. Will call you in the morning. Love you.",
    "Can you please pick up some groceries on your way back? We need milk and bread.",
    "Happy birthday! Hope you have an amazing day. Let's celebrate this weekend.",
    "Please send me the photos from yesterday's party. I want to share them with everyone.",
    "I'll be late today. Stuck in traffic near the airport. Will update you.",
    "The meeting has been moved to 3 PM. Please inform the rest of the team.",
    "Your appointment with Dr. Sharma is confirmed for tomorrow at 10 AM. Please arrive 15 minutes early.",
    "Rahul's wedding is on 15th December. We need to book our flights soon.",
    "Can you pick up the kids from school today? I have a late meeting.",
    "The wifi isn't working at home. Can you call the ISP when you get a chance?",
    "I'm ordering pizza tonight. What toppings do you want?",
    "Your parcel has been delivered to the neighbour. Please collect it from them.",
    "Don't forget we have a dentist appointment on Friday at 11 AM.",
    "The car needs servicing. I've booked it for Saturday morning at 9.",
    "Can you transfer Rs 2,000 to my account? I need to pay the plumber.",
    "The landlord is coming tomorrow to fix the water heater. Please be home.",
    "Your flight AI 202 to Mumbai is on time. Gate 12, boarding at 6:30 PM.",
    "I've sent you the project files via email. Please review them before tomorrow.",
    "The electricity bill has been paid for this month. Check the app for receipt.",
    "Can you believe they cancelled the concert? I'm so disappointed.",
    "Let's plan a trip to Goa next month. I'll check the hotel prices.",
    "Your prescription is ready at Apollo Pharmacy. Please collect before 8 PM.",
    "The gym is closed tomorrow for maintenance. We can go for a run instead.",
    "I'm at the coffee shop near your office. Join me if you're free.",
    "The plumber will come tomorrow at 10 AM. Please make sure someone is home.",
    "Can you check if we have enough rice and dal? I'll pick up whatever is needed.",
    "Your sister called. She wants us to come for dinner on Sunday.",
    "The movie tickets are booked for 7 PM show. Reach by 6:30 so we can grab coffee.",
    "I forgot my lunch at home. Can you drop it at my office?",
    "The AC repair guy is coming between 2-4 PM. Please be there to let him in.",
    "Can you water the plants while I'm away? They need watering every other day.",
    "Your library books are due tomorrow. Please return them on time.",
    "I'm cooking your favourite dish tonight. Come home early if you can.",
    "The internet bill is due tomorrow. I'll pay it online tonight.",
    "Can you send me the address of the party? I'll GPS it.",
    "Your glasses are ready for pickup at the optician. They called today.",
    "I've booked a cab for us to the airport. It will arrive at 5 AM sharp.",
    "The kids have a parent-teacher meeting on Saturday at 10 AM.",
    "Can you drop the car for washing tomorrow morning? I'll pick it up in the evening.",
    "Your train to Chennai departs at 9:15 PM from platform 3. Have a safe journey.",
    "I need the recipe for that pasta you made last week. It was delicious.",
    "The bank called about a cheque bounce. Can you check your account balance?",
    "Can you buy a gift for Ananya's wedding? I'll transfer you the money.",
    "Your passport renewal is due next month. Start the application online.",
    "The neighbours are complaining about the noise. Can you keep it down?",
    "I finished the book you recommended. It was amazing! Got any more suggestions?",
    "Can you pick up my dry cleaning from the shop near the metro station?",
    "The cake is in the oven. Please check it in 20 minutes and turn off the oven.",
    "Your annual health check-up is due. I've booked it for next Tuesday.",
]

LEGIT_SHOPPING_TEXTS = [
    "Your Amazon order #OD1234567890 has been shipped. Expected delivery: 5 Aug.",
    "Flipkart: Your order of Samsung Galaxy M35 has been dispatched. Track at http://flipkart.com/track.",
    "Myntra: Your order #MY1234567890 is out for delivery. Pay Rs 2,499 on delivery.",
    "Ajio: 50% off on your favourite brands. Use code AJIO50. Shop now at http://ajio.com.",
    "Amazon: Your return of product #RT7890123456 has been picked up. Refund will be processed in 5-7 days.",
    "Meesho: Your order of Rs 349 has been confirmed. Expected delivery: 8-10 Aug.",
    "Nykaa: Your order of skincare products is on the way. Track at http://nykaa.com/order.",
    "Tata CLiQ: Your order of OnePlus Nord CE4 has been shipped. Track at http://tatacliq.com/track.",
    "Snapdeal: Your order is being packed. Will ship within 24 hours.",
    "1mg: Your medicine order is confirmed. Prescription will be verified by our pharmacist.",
    "Zepto: Your order of Rs 567 is on its way! Delivery in 10 minutes.",
    "Blinkit: Your grocery order of Rs 892 has been picked. ETA: 12 minutes.",
    "Swiggy Instamart: Your order of Rs 450 is being prepared. Delivery by 8:15 PM.",
    "BigBasket: Your weekly order of Rs 1,250 is out for delivery. Slot: 9-11 AM.",
    "Amazon Fresh: Your order of fruits and vegetables has been delivered.",
    "Flipkart: Your exchange of iPhone 12 has been completed. Refund of Rs 18,000 initiated.",
    "Myntra: Your size exchange request has been approved. Pickup scheduled for 3 Aug.",
    "Ajio: Your wishlist item is now 70% off! Grab it before stock runs out.",
    "Amazon: Price dropped on your saved item: Sony TV now Rs 10,000 off! Check now.",
    "Tata Neu: 5% NeuCoins on your next purchase. Shop at http://tataneu.com.",
    "Urbanic: Your order 40% off summer sale. Use code SUMMER40 at checkout.",
    "Lenskart: Your new glasses are ready for delivery. Track at http://lenskart.com/order.",
    "Pepperfry: Your furniture order will be delivered on 10 Aug. Assembly included.",
    "FNP: Your flower delivery for Aug 5 has been confirmed. Recipient will be notified.",
    "Zivame: Your order of Rs 1,299 is out for delivery. Cash on delivery available.",
    "Amazon Pantry: Your monthly grocery delivery is scheduled for 5 Aug between 6-9 AM.",
    "Flipkart: Your mobile accessories order has reached your nearest hub. Delivering tomorrow.",
    "ShopClues: Your order is shipped. Estimated delivery: 8 Aug. Track online.",
    "Paytm Mall: Your order of Rs 599 has been delivered. Rate the product please.",
    "Purplle: Your makeup order is confirmed. Get ready to glam!",
    "Cult.fit: Your gym kit order dispatched. Start your fitness journey!",
    "Decathlon: Your order of sports shoes has been shipped. Track now.",
]

LEGIT_TELECOM_TEXTS = [
    "Airtel: Your monthly recharge of Rs 599 is successful. Plan valid till 15 Sep. Data: 2GB/day.",
    "Jio: 1.5GB/day data added. Balance: 18.5GB. Validity: 28 days. Recharge at http://jio.com.",
    "VI: Your plan of Rs 299 renewed. Unlimited calls + 1GB/day till 22 Sep.",
    "BSNL: Your FTTH plan of Rs 799 renewed successfully. Speed: 30 Mbps unlimited.",
    "Airtel Xstream: Your broadband bill of Rs 999 generated. Due date: 10 Sep.",
    "JioFiber: Your plan renewed. 100 Mbps unlimited. Next billing: 5 Sep.",
    "TRAI: Your DND registration is active. You will not receive promotional calls for 30 days.",
    "Your mobile number has been successfully ported to Jio. Services active from 6 AM tomorrow.",
    "VI: International roaming pack activated. Validity: 7 days. 100 mins + 1GB/day.",
    "Airtel: Your data usage is 85% of 50GB monthly limit. Top up at http://airtel.in.",
    "Jio: Your account credited with Rs 100 cashback. Valid on next recharge above Rs 299.",
    "BSNL: Your landline bill of Rs 650 for August is due. Pay at http://bsnl.in.",
    "TRAI: Your incoming calls will not be affected by SIM expiry. Recharge by 20 Aug.",
    "Airtel Black: Your combined plan of broadband + DTH + mobile renewed. Rs 1,299/month.",
    "Jio: Rs 299 add-on pack activated. 50GB additional data, valid 30 days.",
    "VI: Your family plan of Rs 699 includes 6 members. All benefits active.",
    "BSNL: Your prepaid SIM KYC is due. Update at nearest BSNL office before 31 Aug.",
    "Airtel: Your postpaid bill of Rs 1,245 for August generated. Auto-pay will debit on 5 Sep.",
    "Jio: 5G services now active in your area. Enjoy unlimited 5G data with your plan.",
    "VI: Your number has been temporarily suspended due to insufficient balance. Recharge now.",
    "Tata Play: Your DTH recharge of Rs 350 done. All channels active till 25 Sep.",
    "Dish TV: Your subscription of Rs 499 renewed. 300+ channels + 15 HD channels.",
    "Airtel DTH: Your annual pack of Rs 2,499 activated. Enjoy uninterrupted entertainment.",
    "JioAirFiber: Your installation scheduled for 12 Aug. Technician will call before visit.",
    "BSNL: Your complaint #1234567890 has been resolved. Thank you for your patience.",
    "Airtel: Your SIM has been successfully replaced. New SIM active from 2 PM today.",
    "VI: Your number is eligible for upgrade to 4G. Visit nearest store with Aadhaar.",
    "Jio: Data add-on of Rs 51 activated. 1GB/day for 3 days. Valid immediately.",
    "Airtel: Welcome to Airtel! Your number XXXXX67890 is active. Enjoy our services.",
    "BSNL: Your broadband usage is 80% of 3TB FUP limit. Speed will reduce after limit.",
]

LEGIT_COLLEGE_TEXTS = [
    "Delhi University: Semester 3 exam schedule published. Download at http://du.ac.in/exams.",
    "IIT Bombay: Placement drive registration open till 15 Aug. Register at http://placement.iitb.ac.in.",
    "VIT Vellore: Campus placements on 5 Aug. 50+ companies visiting. Register now.",
    "Anna University: End semester results published. Check at http://annauniv.edu/results.",
    "IIT Delhi: MTech admissions 2025 open. Apply by 31 Aug at http://jadav.iitd.ac.in.",
    "BITS Pilani: Your fee payment of Rs 2,50,000 for semester 1 due by 10 Aug.",
    "NIT Trichy: Hostel allotment for freshers published. Check at http://nitt.edu/hostel.",
    "JNU: PhD entrance exam results declared. Check your score at http://jnu.ac.in.",
    "IIM Ahmedabad: PGP batch 2025-27 applications open. CAT score required.",
    "IISc Bangalore: Research internship applications open for summer 2026. Apply now.",
    "DU: Your college orientation is on 2 Aug at 9 AM in the main auditorium.",
    "Mumbai University: Exam form submission for semester 3 deadline extended to 10 Aug.",
    "Calcutta University: Your admit card for semester exams available at http://caluniv.ac.in.",
    "NALSAR Hyderabad: CLAT counselling schedule published. Check at http://nalsar.ac.in.",
    "AIIMS Delhi: MBBS internship completion certificates available from academic section.",
    "DTU Delhi: Your semester fee of Rs 85,000 is due. Pay by 15 Aug to avoid late fee.",
    "SP Jain Mumbai: Guest lecture by industry leader on 8 Aug at 11 AM. Mandatory attendance.",
    "XLRI Jamshedpur: Summer placement results announced. Check placement portal.",
    "Christ University: Your provisional degree certificate ready for collection.",
    "SRM Chennai: Internal assessment marks published. Check your ERP portal.",
    "Manipal University: Your semester attendance below 75%. Please meet HOD immediately.",
    "Amity University: Convocation on 25 Aug. Register by 10 Aug at http://amity.edu.",
    "LPU: Your assignment submission deadline extended to 7 Aug. Submit via LMS.",
    "PES Bangalore: Project submission for final year due on 20 Aug. Submit to guide.",
    "Thapar University: Your hostel room allotment for 2025-26 published online.",
    "BIT Mesra: Your scholarship disbursement of Rs 50,000 credited to your account.",
    "COEP Pune: Techfest 2025 registrations open. Register your team at http://techfest.coep.ac.in.",
    "NIT Surathkal: Sports meet registration open till 20 Aug. Participate and win prizes.",
    "Jadavpur University: Your library fine of Rs 250 due. Clear before exam forms.",
    "BHU Varanasi: Your semester registration pending. Complete at http://bhu.ac.in.",
    "IGNOU: Your assignment grades published. Check at http://ignou.ac.in/student.",
    "Symbiosis Pune: SET 2025 results announced. Check your scorecard online.",
    "NID Ahmedabad: Your portfolio submission deadline extended to 15 Aug.",
    "NIFT Delhi: Your final year project exhibition on 10 Aug. Attendance compulsory.",
    "IIT Kharagpur: Your medical insurance claim of Rs 5,000 approved. Check student portal.",
    "IIT Roorkee: Winter internship applications open. Apply at http://internship.iitr.ac.in.",
    "ISI Kolkata: Your admission test results published. Check at http://isical.ac.in.",
    "TIFR Mumbai: Your PhD interview scheduled for 12 Aug at 10 AM. Be prepared.",
    "CMC Vellore: Your internship rotation schedule for August published in student portal.",
    "AFMC Pune: Your annual medical checkup on 8 Aug. Report to medical centre by 8 AM.",
]

LEGIT_UTILITY_TEXTS = [
    "Your electricity bill of Rs 1,250 for July is due by 15 Aug. Pay at http://tpsodl.com.",
    "Tata Power: Your bill of Rs 2,450 is generated. Due date: 20 Aug. Auto-pay enabled.",
    "BSES: Your electricity consumption 350 units for July. Bill Rs 2,100. Pay online.",
    "Adani Electricity: Your bill payment of Rs 1,890 received. Thank you for timely payment.",
    "Mahanagar Gas: Your gas bill of Rs 780 for August due. Pay at http://mahanagargas.com.",
    "IOCL: Your LPG cylinder delivery scheduled for 10 Aug. Track at http://iocl.com.",
    "HP Gas: Refill delivery in progress. SMS sent to registered mobile with delivery details.",
    "Bharat Gas: Your gas connection annual maintenance due. Pay Rs 150 at http://bharatgas.com.",
    "Water supply maintenance in your area on 15 Aug from 10 AM to 5 PM. Store water.",
    "Delhi Jal Board: Your water bill of Rs 450 for quarter 2 generated. Due: 31 Aug.",
    "Chennai Metro Water: Your water bill Rs 320 due. Pay at http://chennaimetrowater.com.",
    "Your property tax of Rs 12,500 for FY 2025-26 is due. Pay by 30 Sep to avoid penalty.",
    "Municipal Corporation: Your house tax bill generated. Pay online at municipal portal.",
    "Your society maintenance of Rs 3,500 for August is due. Pay to the society account.",
    "Broadband: Your ACT Fibernet bill of Rs 999 for August generated. Auto-pay on 10 Aug.",
    "Your water purifier AMC is due for renewal. Rs 1,999/year. Call 1800-123-4567.",
    "Electricity: Power maintenance in Sector 12 on 12 Aug from 9 AM to 2 PM.",
    "Your solar panel net metering bill of Rs 350 generated. Excess units: 120 units.",
    "Property tax payment receipt for FY 2025-26. Receipt #TX2025-1234567890.",
    "Society: Your parking allotment renewed for 2025-26. Pay Rs 2,400 annual fee.",
    "CNG: Your piped gas bill of Rs 650 for August due. Pay at http://iglonline.com.",
    "Your LPG subsidy of Rs 300 credited to your bank account for refill #12345.",
    "Electricity: Your new connection application #AP1234567890 approved. Meter installation in 7 days.",
    "Your water tanker booking for 15 Aug confirmed. Delivery between 8-10 AM.",
    "Gas pipeline maintenance: Supply will be off on 13 Aug from 9 AM to 2 PM.",
]

LEGIT_PERSONAL_MORE = [
    "Bhai, kal party mein kitne baje aana hai?",
    "Maa, main ghar aa raha hoon. Khana mat banana, bahar se le lunga.",
    "Yaar, kal ka assignment complete kiya? Mujhe samajh nahi aa raha.",
    "Aaj gharpe sab thik hai? Main office se late aaunga.",
    "Dost, tere paas Rs 500 hai? Kal wapas kar dunga.",
    "School se aate time bread aur butter le aana.",
    "Aaj bahut thand hai. Garam kapde pehen ke bahar jaana.",
    "Sunday ko family dinner hai. Sabko bula lo.",
    "Train 2 ghante late hai. Station pe 9 baje pahunchungi.",
    "Beta, exam mein achha score kiya. Very proud of you!",
    "Naa ungalukku innaikkum velai irukka? Saapidu porom.",
    "Appa, naan hostel safe ah vanthuten. Call pannuren.",
    "Akka, unga friend phone pannanga. Number koduthuten.",
    "Tamanna, naan ippo office ku poren. Dinner ku varuven.",
    "Machaa, naalai evening porul edukka poalam.",
    "Thambi, amma unga kitta pesanum. Intiki raa.",
    "Anna, nenu inka office lo unna. Dinner ki intiki vostanu.",
    "Amma, nenu safe ga hostel ki chesanu. Call chestanu.",
    "Akka, meeru konchem paalu theesukoni raavala?",
    "Babai, nenu repu ma intiki vastanu. Anni items konostanu.",
]

LEGIT_UPI_MORE = [
    "GPay: Rs 200 received from Rahul for movie tickets. Ref: 123456789012.",
    "PhonePe: Rs 1,500 sent to Kirana Store for monthly groceries. Successful.",
    "Paytm: Your wallet credited with Rs 500 from friend. Balance: Rs 2,350.",
    "Amazon Pay: Cashback of Rs 125 credited for utility bill payment.",
    "BHIM: Your monthly rent of Rs 15,000 paid to Landlord. Ref: 234567890123.",
    "CRED: Credit card bill of Rs 12,450 paid successfully. 5% cashback earned.",
    "GPay: Your electricity bill payment of Rs 1,890 successful. Receipt sent.",
    "PhonePe: Recharge of Rs 599 for Airtel mobile done. Valid 28 days.",
    "GPay: Rs 5,000 transferred to Savings account from UPI. Ref: 345678901234.",
    "Paytm: Your DTH recharge of Rs 350 for 3 months completed.",
    "BHIM: Loan EMI of Rs 8,500 paid to HDFC. Thank you for auto-pay.",
    "PhonePe: Insurance premium of Rs 2,300 paid. Policy active till Dec 2025.",
    "GPay: Rs 350 sent to Milkman for monthly dairy bill. Payment successful.",
    "Amazon Pay: Your credit card bill auto-paid. Receipt available in app.",
    "CRED: Rent payment of Rs 18,000 to owner successful. 750 CRED coins earned.",
    "PhonePe: Rs 2,000 requested from friend. Waiting for acceptance.",
    "GPay: Your QR payment of Rs 450 at Saravana Bhavan successful.",
    "Paytm: Your FASTag recharged with Rs 500. Balance: Rs 750.",
    "BHIM: Your municipal tax payment of Rs 3,200 successful. Receipt generated.",
    "GPay: Mutual fund SIP of Rs 5,000 invested successfully. Fund: Axis Bluechip.",
    "PhonePe: Gold purchase of Rs 1,000 at today's rate. 0.15g added to portfolio.",
    "GPay: Rs 250 refund from Zomato for cancelled order. Credited to account.",
    "Paytm: Your NPS contribution of Rs 3,000 invested. Tax benefit under 80C.",
    "PhonePe: Your mobile postpaid bill of Rs 1,200 paid via auto-pay.",
    "GPay: College fee of Rs 85,000 paid to SRM University. Receipt generated.",
    "BHIM: LPG cylinder payment of Rs 1,050 made. Refill on the way.",
    "CRED: Your platinum membership fee of Rs 999 paid. Enjoy premium benefits.",
    "Amazon Pay: Your insurance policy premium of Rs 15,000 paid. Policy active.",
]

LEGIT_BANKING_MORE = [
    "SBI: Your account XXXX4567 credited with Rs 25,000. Salary for July 2025.",
    "HDFC: Your home loan EMI of Rs 32,500 debited on 5 Aug. Outstanding: Rs 18,50,000.",
    "ICICI: Your credit card bill of Rs 14,200 paid. Available credit: Rs 1,85,800.",
    "Axis Bank: Fixed deposit of Rs 1,00,000 matured. Proceeds credited to savings.",
    "PNB: Your cheque #123456 of Rs 5,000 cleared. Issued to Rahul Sharma.",
    "Canara Bank: New debit card dispatched. Expected delivery: 7-10 working days.",
    "Union Bank: Your account statement for July generated. Available at net banking.",
    "Bank of Baroda: Your recurring deposit of Rs 2,000 debited. RD balance: Rs 1,20,000.",
    "Kotak Mahindra: Your credit card limit increased to Rs 5,00,000. Offer valid till 31 Aug.",
    "IndusInd: Your savings account interest of Rs 1,250 credited for Q2.",
    "SBI: Your PPF account credited with Rs 15,000. Current balance: Rs 3,50,000.",
    "HDFC: Demat account annual maintenance fee of Rs 750 debited.",
    "ICICI: Your NRI account statement for Q2 available. Download at http://icici.com.",
    "Axis Bank: Your loan against property sanctioned Rs 25,00,000. EMI: Rs 28,500.",
    "Yes Bank: Your salary account upgraded to Yes Priority. Concierge available.",
    "IDFC First Bank: Your savings account 7% interest credited. Amount: Rs 2,350.",
    "RBL Bank: Your credit card reward points expiring. Redeem by 31 Aug.",
    "Federal Bank: Your education loan disbursement of Rs 8,50,000 credited to college.",
    "Standard Chartered: Your investment portfolio review scheduled for 12 Aug.",
    "DBS Bank: Your DigiSavings account opened. Debit card dispatched. Activate at atm.",
    "SBI: Your ATM card blocked due to 3 wrong PIN attempts. New card being issued.",
    "HDFC: Your mutual fund SIP of Rs 5,000 in HDFC Top 100 debited successfully.",
    "ICICI: Your credit card statement for August generated. Minimum due: Rs 2,500.",
    "Axis Bank: You have 5,000 reward points. Redeem for flight tickets at http://axisrewards.com.",
    "PNB: Your gold loan of Rs 2,00,000 sanctioned. Disbursed to your account.",
]

LEGIT_COURIER_MORE = [
    "FedEx: Your shipment from New York has arrived at Mumbai customs. Clearance in progress.",
    "Your Delhivery parcel out for delivery today. Track at http://delhivery.com/track.",
    "Amazon Logistics: Your package will be delivered between 6-9 PM tonight.",
    "India Post: Your registered letter from IIT Bombay delivered to your address.",
    "Blue Dart: Your document shipment to Bangalore delivered successfully.",
    "DTDC: Your parcel from Dubai cleared customs. Out for delivery.",
    "Ecom Express: Your return pickup scheduled for 6 Aug between 10 AM - 1 PM.",
    "Your Professional Courier parcel from Delhi has reached the destination hub.",
    "Shiprocket: Your COD order of Rs 1,299 out for delivery. Keep exact change ready.",
    "DHL: Your international package from Singapore is in transit. Track online.",
    "Speed Post: Your Aadhaar letter dispatched from UIDAI. Track at indiapost.gov.in.",
    "XpressBees: Your order from Flipkart has reached your city hub. Delivering tomorrow.",
    "Shadowfax: Your food delivery order is being prepared. Will reach in 30 mins.",
    "Gati: Your cargo shipment of 25 kg from Chennai warehouse is in transit.",
    "Pickrr: Your return request approved. Pickup scheduled for 7 Aug.",
]

LEGIT_OTHER = [
    "Your driving licence renewal reminder: Expires on 31 Oct. Renew at http://parivahan.gov.in.",
    "Passport seva: Your application #AB1234567890 is under processing. Track online.",
    "Election Commission: Your voter ID issued. Download e-EPIC at http://nvsp.in.",
    "Income Tax: Your ITR for FY 2024-25 processed. Refund of Rs 12,500 credited.",
    "Aadhaar: Your address update request approved. Updated Aadhaar downloaded.",
    "Voter ID correction application status: Approved. New card dispatched.",
    "Parivahan: Your vehicle registration renewal reminder. Pay Rs 600 road tax.",
    "Your ration card updated. New members added. Check at http://epos.up.nic.in.",
    "Pension: Your monthly pension of Rs 25,000 credited. PPO number: 123456789.",
    "Ayushman Bharat: Your health card generated. Coverage: Rs 5,00,000 per family.",
]

BANKING_FRAUD_MORE = [
    "Axis Bank: Your account from Mumbai login. If not you, share OTP to 9988776655.",
    "PNB: Your net banking password expiring. Keep same password at http://pnb-update.xyz.",
    "HDFC: Your credit card has been used for Rs 1,25,000 in Dubai. Block at http://hdfc-block.tk.",
    "ICICI: SIM swap request detected. Your account may be compromised. Call immediately.",
    "SBI: Your account has been accessed from 3 different cities in 1 hour. Verify now.",
    "Kotak: Your salary account upgraded to premium. Pay Rs 3,500 annual fee to activate.",
    "Your ATM card cloned. Rs 75,000 withdrawn from Jaipur ATM. Call dispute centre.",
    "Bank of India: Your account selected for government subsidy. Pay Rs 2,500 processing fee.",
    "RBI: All banks required to update customer details. Update at http://rbi-update.in.",
    "Central Bank: Your locker rent overdue. Pay Rs 5,000 to avoid locker sealing.",
    "Dena Bank: Your account reviewed for PM Jan Dhan Yojana. Submit documents now.",
    "Corporation Bank: Your education loan sanctioned Rs 12,00,000. Pay Rs 25,000 processing.",
    "UCO Bank: Your pension account needs re-verification. Visit branch with Aadhaar.",
    "Vijaya Bank merged with Bank of Baroda. Update account details at http://bob-merge.xyz.",
    "Syndicate Bank: Your KYC expired. Account operations limited. Update at our portal.",
]

UPI_FRAUD_MORE = [
    "GPay: UPI collect request from merchant 'ElectroWorld' for Rs 45,000. Approve? Reply Y.",
    "PhonePe: Request from unknown. Rs 8,500 for insurance policy. Block at http://phonepe-block.xyz.",
    "Paytm: Your wallet auto-debit of Rs 1,999/month activated for VIP membership. Cancel? Reply OTP.",
    "BHIM: Your UPI PIN reset by someone from Pune. Not you? Share OTP to reverse.",
    "Amazon Pay: Your recurring payment of Rs 2,500 to unknown merchant. Dispute at http://amazon-dispute.tk.",
    "GPay: Rs 12,500 sent to unknown UPI ID from your account. Reverse? Share OTP now.",
    "PhonePe: Your gold investment of Rs 50,000 auto-purchased. Cancel within 30 mins.",
    "CRED: Your credit card payment of Rs 65,000 failed due to bank issue. Retry with new card.",
    "GPay: Your account shared with 3 family members via UPI Circle. Manage at http://gpay-circle.xyz.",
    "PhonePe: Rs 5,000 cashback credited. Withdraw at http://phonepe-cashback.tk.",
    "BHIM: Your account registered for UPI123Pay. Transaction limit increased to Rs 50,000.",
    "Paytm: Fastag auto-recharge of Rs 500 failed. Your tag may be deactivated.",
    "Amazon Pay: UPI mandate created for Rs 15,000/month. Not you? Cancel at http://amazon-mandate.xyz.",
    "GPay: Weekly transaction summary shows 5 unknown payments totalling Rs 23,000. Check now.",
    "PhonePe: Your UPI Lite balance of Rs 1,500 used for unknown merchant. Block now.",
    "BHIM: Scan and pay of Rs 8,900 from your account at 'QuickMart'. Not recognised? Dispute now.",
    "Google Pay: Rs 7,500 sent to Sunil@upi. If not authorised, call 1800-419-6789.",
    "PhonePe: Your auto-pay of Rs 2,500 to 'Grofers' activated. Not you? Cancel OTP sent.",
    "Amazon Pay: Rs 950 debited for Amazon Prime renewal. Not you? Cancel at http://amazon-cancel.xyz.",
    "CRED: Reward points worth Rs 2,500 redeemed. If not you, report immediately.",
]

TELECOM_SCAM_MORE = [
    "Your SIM has been used in illegal activities. Your number will be disconnected. Call 1800-123-4567.",
    "Airtel: Your SIM is being replaced by someone in Chennai. Not you? Share OTP to stop.",
    "TRAI: Your mobile number used for spam calls. Pay Rs 25,000 penalty or face disconnection.",
    "Jio: Your number selected for 5G upgrade. Submit documents at http://jio-upgrade.xyz.",
    "VI: Your SIM card expiring. Re-KYC at http://vi-kyc.in or line will be cut.",
    "BSNL: Your landline bill overdue Rs 4,500. Legal notice will be sent to your address.",
    "Your mobile number has won Rs 25,00,000 in TRAI lucky draw. Claim at http://trai-winner.tk.",
    "DoT: Your SIM linked to drug trafficking case. Contact cyber cell immediately.",
    "Airtel: Your international roaming activated for Rs 25,000 package. Reply YES to confirm.",
    "Jio: Free 5G upgrade for your number. Pay Rs 999 processing fee at http://jio-5g.top.",
    "TRAI: Your phone number used in fraud. File online complaint at http://trai-complaint.xyz.",
    "VI: You have 50,000 VI reward points expiring. Redeem at http://vi-rewards.tk.",
    "SIM swapping attempt detected. Your number will be blocked for 24 hours. Verify now.",
    "Your mobile number has been cloned. Another device using your number. Call immediately.",
    "Airtel: Rs 10,000 cashback on your next recharge. Click http://airtel-offer.xyz to claim.",
]

PERSONAL_SCAM = [
    "Beta, main hospital mein hoon. Emergency mein Rs 50,000 chahiye. Is account mein daalo - 1234567890.",
    "Rahul here. I'm stuck in a different city without money. Can you send Rs 20,000 urgently?",
    "Mummy ne bola aapko paise bhejne hain. Rs 25,000 emergency. Yahan bhejo: GPay 9876543210.",
    "Boss, I'm in trouble. Need Rs 15,000 immediately. Don't tell anyone. Will return tomorrow.",
    "Dost, meri tabiyat kharab hai. Hospital mein hoon. Rs 10,000 bhej de jaldi.",
    "Anna, naaku emergency lo Rs 30,000 kavali. GPay ki pampandi. Tharvaatha cheptha.",
    "Akka, naan hospital la irukken. Rs 20,000 urgent. PhonePe ku anupungal.",
    "Bhai emergency hai. Please call me on this number: 9876543210. Matter is sensitive.",
    "Hello, this is Rahul's friend. He met with an accident. Please send Rs 50,000 for treatment.",
    "Sir, main aapke bete ka dost hoon. Unhe accident hua hai. Rs 25,000 hospital ke liye chahiye.",
]

FAKE_CUSTOMER_CARE_MORE = [
    "Netflix: Your payment failed. Update card at http://netflix-update.xyz or account suspended.",
    "Amazon: Your account has been compromised. Call 1800-123-4567 to secure immediately.",
    "Google Pay: Suspicious transaction detected. Verify identity at http://gpay-verify.in.",
    "Swiggy: Your account credited with Rs 25,000 cashback. Withdraw at http://swiggy-cashback.tk.",
    "Zomato: Pro membership auto-renewed. Rs 2,500 charged. Dispute at http://zomato-dispute.xyz.",
    "Microsoft: Your OneDrive storage 99% full. Upgrade to 1TB at Rs 1,500/year.",
    "Uber: Your payment method failed. Update to continue using Uber services.",
    "OLX: Your item sold. Buyer paid Rs 35,000. Collect at http://olx-payment.xyz.",
    "LinkedIn: Premium membership trial ending. Auto-renewal of Rs 3,500/year. Cancel now.",
    "Amazon: Your gift card of Rs 10,000 activated. Use at http://amazon-gift-card.xyz.",
]

LOTTERY_SCAM_MORE = [
    "Congratulations! You have won Rs 50,00,000 in KBC Lucky Draw. Call 1800-123-4567 to claim.",
    "Tata Motors: You won a free Tiago car in our anniversary draw. Claim at http://tata-winner.xyz.",
    "Google: Your search history selected for Reward Program. Rs 2,00,000 prize. Call now.",
    "Amazon: You are our 1,000,000th customer! Win iPhone 15 Pro. Claim: http://amazon-million.tk.",
    "Coca-Cola: You won Rs 10,00,000 in our summer contest. Pay Rs 5,000 processing to release prize.",
    "Pepsi: You won a trip to Dubai worth Rs 5,00,000. Call 1800-425-6789 to confirm.",
    "Your phone number won Rs 25,00,000 in Mukesh Ambani birthday draw. Send Rs 2,500 for documents.",
    "Flipkart: You won Rs 75,000 shopping voucher. Redeem at http://flipkart-winner.xyz.",
    "WhatsApp: Message forwarded 100 times! You win Rs 50,000. Claim at http://whatsapp-lucky.tk.",
    "Your email ID won in Reliance Jio lucky draw. Rs 10,00,000 prize. Call now to claim.",
]

def generate_new_samples(all_texts, existing_ids):
    new_rows = []
    idx_counter = copy.deepcopy(existing_ids)

    def add_samples(category, is_scam, risk, texts, lang="en"):
        nonlocal idx_counter
        for t in texts:
            t_clean = t.strip().lower()
            if t_clean in all_texts:
                continue
            idx_counter[category] += 1
            row = make_sample(t, category, is_scam, risk, language=lang, index=idx_counter[category])
            new_rows.append(row)
            all_texts.add(t_clean)

    def add_multilingual(category, is_scam, risk, lang_texts):
        for lang, texts in lang_texts.items():
            for t in texts:
                t_clean = t.strip().lower()
                if t_clean in all_texts:
                    continue
                idx_counter[category] += 1
                row = make_sample(t, category, is_scam, risk, language=lang, index=idx_counter[category])
                new_rows.append(row)
                all_texts.add(t_clean)

    # --- CATEGORIES COMPLETELY MISSING FROM TRAINING ---
    # 1. OTP_SCAM (scam) - weakest scam category
    add_samples("OTP_SCAM", True, "HIGH", OTP_SCAM_TEXTS)
    # 2. LEGITIMATE_PERSONAL (legit) - most FPs
    add_samples("LEGITIMATE_PERSONAL", False, "LOW", LEGIT_PERSONAL_TEXTS)
    # 3. LEGITIMATE_SHOPPING (legit) - second most FNs
    add_samples("LEGITIMATE_SHOPPING", False, "LOW", LEGIT_SHOPPING_TEXTS)
    # 4. LEGITIMATE_TELECOM (legit) - FPs and FNs
    add_samples("LEGITIMATE_TELECOM", False, "LOW", LEGIT_TELECOM_TEXTS)
    # 5. LEGITIMATE_COLLEGE (legit) - FPs
    add_samples("LEGITIMATE_COLLEGE", False, "LOW", LEGIT_COLLEGE_TEXTS)
    # 6. LEGITIMATE_UTILITY (legit) - FPs
    add_samples("LEGITIMATE_UTILITY", False, "LOW", LEGIT_UTILITY_TEXTS)

    # --- MULTILINGUAL EXPANSION ---
    # Personal messages in Hindi, Tamil, Telugu
    add_samples("LEGITIMATE_PERSONAL", False, "LOW", LEGIT_PERSONAL_MORE, lang="hi-en")
    # Add hi-en te-en ta-en variants for key categories
    hi_otp = [
        "Aapka Amazon OTP 456789 hai. Kisi ko na bataye. Galat hai to forward karein 9988776655.",
        "SBI OTP 891234 se Rs 45,000 transfer ho gaya. Not you? Call 1800-425-3800.",
        "Google verification code 482916. Share mat karna. Galati se aaya to forward karo.",
        "Aapka WhatsApp OTP 673489. Do not share. Forward karo 9876543210 agar aapne nahi kiya.",
        "IRCTC OTP 945612. PNR cancellation ke liye. Agar aapne nahi kiya to call karein.",
        "PhonePe OTP 345678. Naya beneficiary add. Not you? Forward OTP to block.",
        "Paytm OTP 890123. Rs 25,000 wallet transfer. Send OTP to block transaction.",
        "Amazon OTP 563412. Login from Delhi. Not you? Call support immediately.",
    ]
    ta_otp = [
        "Unga Amazon OTP 456789. Yaarukkum share pannathinga. Thappu na 9988776655 ku forward pannunga.",
        "SBI OTP 891234. Rs 45,000 transfer aachu. Neenga illana 1800-425-3800 ku call pannunga.",
        "Google verification code 482916. Share pannathinga. Thappula vandha forward pannunga.",
        "WhatsApp OTP 673489. Share pannathinga. 9876543210 ku forward pannunga neenga illana.",
        "IRCTC OTP 945612. PNR cancellation ku. Neenga illana call pannunga.",
        "PhonePe OTP 345678. Puthu beneficiary add pannanga. Not you? OTP ah forward pannunga.",
    ]
    te_otp = [
        "Mee Amazon OTP 456789. Evvariki share cheyyakandi. Thappu ante 9988776655 ki forward cheyandi.",
        "SBI OTP 891234. Rs 45,000 transfer ayindi. Meeru kaka pote 1800-425-3800 ki call cheyandi.",
        "Google verification code 482916. Share cheyyakandi. Thappuga vaste forward cheyandi.",
        "WhatsApp OTP 673489. Share cheyyakandi. 9876543210 ki forward cheyandi.",
    ]
    add_samples("OTP_SCAM", True, "HIGH", hi_otp, lang="hi-en")
    add_samples("OTP_SCAM", True, "HIGH", ta_otp, lang="ta-en")
    add_samples("OTP_SCAM", True, "HIGH", te_otp, lang="te-en")

    # Telugu personal messages
    te_personal = [
        "Nenu safe ga hostel ki chesanu. Repu call chestanu.",
        "Amma, nenu konchem late ga vastanu. Dinner ki eduru choodakandi.",
        "Naa tho paalu theesukoni raava? Bread kuda konostanu.",
        "Neeku picnic ki vellali ante ela undi? Week-end lo planning cheddam.",
        "Annayya, nee friend phone chesaru. Number ichanu vadiki.",
        "Nenu ippo office ki velthunna. Dinner ki vastanu.",
        "Repu evening 7 ki movie ki plan cheddama?",
    ]
    ta_personal = [
        "Naan safe ah hostel vanthuten. Naalai call pannuren.",
        "Amma, naan konjam late aaguen. Dinner ku edhir paakka vendam.",
        "Unnodaa paal vaangi varaaya? Bread um vaanguren.",
        "Ungalukku picnic ku poga aasaiya? Weekend la plan pannalaam.",
        "Akka, unga friend phone pannanga. Number kuduthen.",
        "Naan ippo office ku poren. Dinner ku varuven.",
        "Naalaikku 7 PM ku movie ku plan pannalaama?",
    ]
    add_samples("LEGITIMATE_PERSONAL", False, "LOW", te_personal, lang="te-en")
    add_samples("LEGITIMATE_PERSONAL", False, "LOW", ta_personal, lang="ta-en")

    hi_shopping = [
        "Amazon: Aapka order OD1234567890 dispatched ho gaya hai. Delivery 5 Aug tak.",
        "Flipkart: Aapka Samsung phone dispatch. Track at http://flipkart.com/track.",
        "Meesho: Rs 349 ka order confirm. Delivery 8-10 din mein.",
        "Zepto: Aapka Rs 567 ka order aa raha hai! 10 minute mein delivery.",
        "Blinkit: Rs 892 ka grocery order picked. 12 minute mein pahunch jayega.",
        "Myntra: Size exchange approved. Pickup kal scheduled hai.",
    ]
    add_samples("LEGITIMATE_SHOPPING", False, "LOW", hi_shopping, lang="hi-en")

    hi_telecom = [
        "Airtel: Rs 599 ka recharge successful. 2GB/day, valid 28 din.",
        "Jio: 1.5GB/day data add. Balance: 18.5GB. 28 din validity.",
        "VI: Rs 299 ka plan renew. Unlimited calls + 1GB/day.",
        "BSNL: Rs 799 FTTH plan renew. 30 Mbps unlimited.",
        "JioFiber: Rs 999 ka bill generate. Due date: 10 Sep.",
        "TRAI: DND registration active. Promotional calls nahi aayenge.",
    ]
    add_samples("LEGITIMATE_TELECOM", False, "LOW", hi_telecom, lang="hi-en")

    # --- EXPAND UNDER-60 CATEGORIES ---
    add_samples("LEGITIMATE_BANKING", False, "LOW", LEGIT_BANKING_MORE)
    add_samples("LEGITIMATE_COURIER", False, "LOW", LEGIT_COURIER_MORE)
    add_samples("LEGITIMATE_UPI", False, "LOW", LEGIT_UPI_MORE)
    add_samples("LEGITIMATE_OTP", False, "LOW", ["Your OTP for transaction is 123456. Valid for 10 minutes.",
                                                  "GPay: OTP 789012 for adding new payee. Valid 5 mins.",
                                                  "PhonePe: Login OTP 345678. Do not share.",
                                                  "Amazon: One-time password 901234 for return pickup.",
                                                  "SBI: Transaction OTP 567890 for Rs 5,000. Valid 10 minutes.",
                                                  "IRCTC: OTP 123478 for login. Valid 5 minutes.",
                                                  "Aadhaar: OTP 234589 for authentication. Valid 10 minutes.",
                                                  "Netflix: OTP 345690 for account access. Valid 15 minutes.",
                                                  "Your Google verification code is 456701. Valid for 5 minutes.",
                                                  "Microsoft: OTP 567812 for account recovery. Do not share.",
                                                  "WhatsApp: Your code is 678923. Valid for 5 mins.",
                                                  "Twitter: OTP 789034 for login verification. Valid 15 mins.",
                                                  "Instagram: OTP 890145 for password reset. Valid 10 mins.",
                                                  "Facebook: OTP 901256 for login approval. Valid 5 mins.",
                                                  "LinkedIn: OTP 123467 for account recovery. Valid 10 mins.",
                                                  "UPI: OTP 234578 for transaction of Rs 1,500. Valid 5 mins.",
                                                  "Bank: OTP 345689 for adding beneficiary. Valid 10 mins.",
                                                  "Email: OTP 456790 for account verification. Valid 15 mins.",
                                                  "PayPal: OTP 567801 for payment confirmation. Valid 10 mins.",
                                                  "Razorpay: OTP 678912 for subscription. Valid 5 mins."])

    # --- EXPAND EXISTING WEAK SCAM CATEGORIES ---
    add_samples("BANKING_FRAUD", True, "HIGH", BANKING_FRAUD_MORE)
    add_samples("UPI_FRAUD", True, "HIGH", UPI_FRAUD_MORE)
    add_samples("TELECOM_SCAM", True, "HIGH", TELECOM_SCAM_MORE)
    add_samples("FAKE_CUSTOMER_CARE", True, "HIGH", FAKE_CUSTOMER_CARE_MORE)
    add_samples("LOTTERY_SCAM", True, "HIGH", LOTTERY_SCAM_MORE)
    add_samples("LEGITIMATE_SHOPPING", False, "LOW", ["Aapka Amazon order dispatch ho gaya hai. Track karo yahan.",
                                                      "Mee Amazon order dispatch ayindi. Track cheyandi.",
                                                      "Amazon order dispatch aagirukku. Track pannugal."], lang="hi-en")
    add_samples("LEGITIMATE_SHOPPING", False, "LOW", ["Mee Amazon order dispatch ayindi. Track cheyandi.",
                                                      "Amazon order dispatch aagirukku. Track pannugal."], lang="hi-en")

    # --- ADD REMAINING LEGIT CATEGORIES ---
    add_samples("LEGITIMATE_GOVERNMENT", False, "LOW", LEGIT_OTHER)

    # --- PERSONAL SCAM (scam) - family emergency scams ---
    add_samples("PERSONAL_SCAM", True, "HIGH", PERSONAL_SCAM)

    # --- EXPAND UNDER-60 SCAM CATEGORIES ---
    # FAKE_CUSTOMER_CARE: 61 → 70 (+9)
    # Add more FAKE_CUSTOMER_CARE samples
    fcc_extra = [
        "Amazon Prime: Your subscription auto-renewed Rs 1,499. Dispute? Call 1800-123-4567.",
        "Google One: Your storage plan expiring. Renew Rs 1,300/year at http://google-one.xyz.",
        "Swiggy: One order free on your birthday! Claim at http://swiggy-birthday.tk.",
        "Zomato: Gold membership expired. Renew Rs 2,999 at http://zomato-gold.xyz.",
        "Flipkart: Your account blocked due to policy violation. Verify at http://flipkart-verify.in.",
        "Myntra: Style session unlocked! Rs 15,000 shopping spree. Claim at http://myntra-style.xyz.",
        "Uber Eats: Your order of Rs 450 eligible for free delivery. Use code FREEDEL.",
        "Netflix: Your account will be deleted due to inactivity. Reactivate at http://netflix-react.tk.",
        "Amazon: Your registry enabled. Share wedding registry at http://amazon-registry.xyz.",
    ]

    # LOTTERY_SCAM: 63 → 70 (+7)
    lottery_extra = [
        "Your phone number won Rs 15,00,000 in Amazon Lucky Day. Claim at http://amazon-lucky.xyz.",
        "You won a luxury car in Times of India contest. Call 1800-123-456 to claim prize.",
        "Google Pay: You are our 5 crore user! Rs 5,00,000 prize. Claim at http://gpay-lucky.tk.",
        "Tesla: You won a Model 3 in our referral contest. Pay Rs 25,000 documentation fee.",
        "Air India: You won two business class tickets to London. Call to confirm.",
        "Samsung: You won Galaxy Z Fold 6 in launch event. Pay Rs 1,500 delivery charge.",
        "Boat: You won Rs 2,00,000 in our anniversary sale. Claim at http://boat-winner.xyz.",
    ]

    # PAN_SCAM: 63 → 70 (+7)
    pan_extra = [
        "Your PAN card deactivated due to non-usage. Reactivate at http://pan-reactivate.xyz.",
        "PAN-Aadhaar linking last date extended. Link now or PAN will be inoperative.",
        "Income Tax: Rs 75,000 refund for PAN ABCDE1234F pending. Submit bank details.",
        "Your PAN used to open 3 companies in Gujarat. File complaint at 1800-123-4567.",
        "PAN card update: Your photo required for e-PAN generation. Upload at http://pan-photo.tk.",
        "Tax notice: Your PAN has excess TDS of Rs 25,000. File return to claim refund.",
        "Your PAN card has been dispatched. Track at http://pan-track.in.",
    ]

    # QR_SCAM: 64 → 70 (+6)
    qr_extra = [
        "Scan QR to pay Rs 12,500 and claim your iPhone 15. Limited offer!",
        "Flipkart: Scan this QR code to win Rs 50,000 shopping voucher.",
        "GPay: Scan QR to pay Rs 5 and win upto Rs 1,00,000. Lucky draw!",
        "Amazon: Scan QR at store to get 90% off on your first purchase.",
        "Electricity bill discount! Scan QR to pay bill and get 20% cashback.",
        "PhonePe: Scan merchant QR to pay Rs 2,500 and get free insurance.",
    ]

    # DIGITAL_ARREST: 66 → 70 (+4)
    da_extra = [
        "Cyber crime: Your Aadhaar used in online fraud. Report to cyber cell immediately.",
        "Supreme Court notice: Your bank accounts frozen for money laundering. Call helpline.",
        "CBI investigation: Your IP address involved in hacking. Cooperate or arrest warrant issued.",
        "Your digital arrest warrant issued by Cyber Crime India. Pay Rs 50,000 bail to avoid arrest.",
    ]

    # INCOME_TAX_SCAM: 68 → 70 (+2)
    it_extra = [
        "Income Tax: Your ITR processing stopped due to income mismatch. Correct at http://itr-correction.xyz.",
        "CBDT: Your tax refund of Rs 1,25,000 is on hold. Update bank account at http://tax-refund.tk.",
    ]

    add_samples("FAKE_CUSTOMER_CARE", True, "HIGH", fcc_extra)
    add_samples("LOTTERY_SCAM", True, "HIGH", lottery_extra)
    add_samples("PAN_SCAM", True, "HIGH", pan_extra)
    add_samples("QR_SCAM", True, "HIGH", qr_extra)
    add_samples("DIGITAL_ARREST", True, "HIGH", da_extra)
    add_samples("INCOME_TAX_SCAM", True, "HIGH", it_extra)

    return new_rows


def main():
    logger.info("Loading existing gamma dataset...")
    existing_rows, existing_texts, existing_ids = load_existing(GAMMA_PATH)
    logger.info("Existing rows: %d", len(existing_rows))
    logger.info("Existing texts: %d unique", len(existing_texts))

    logger.info("Generating new samples for weak categories...")
    new_rows = generate_new_samples(existing_texts, existing_ids)
    logger.info("Generated %d new samples", len(new_rows))

    # Update max IDs to avoid collision
    all_rows = existing_rows + new_rows

    # Recalculate stats
    scam_count = sum(1 for r in all_rows if r["is_scam"].lower() in ("true", "1", "yes"))
    legit_count = len(all_rows) - scam_count
    cats = Counter(r["category"] for r in all_rows)
    langs = Counter(r["language"] for r in all_rows)

    logger.info("Total: %d samples (%d scam, %d legit)", len(all_rows), scam_count, legit_count)
    logger.info("Categories: %d", len(cats))
    logger.info("Languages: %s", dict(langs))
    logger.info("")
    logger.info("=== Category Distribution ===")
    for cat, n in sorted(cats.items()):
        logger.info("  %s: %d", cat, n)

    # Write output
    fieldnames = list(all_rows[0].keys())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    logger.info("Written to %s", OUTPUT_PATH)

    # Copy to backend
    BACKEND_COPY.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKEND_COPY, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    logger.info("Copied to %s", BACKEND_COPY)

    logger.info("Done! Total samples: %d", len(all_rows))

if __name__ == "__main__":
    main()
