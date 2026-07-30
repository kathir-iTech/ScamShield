import csv, json, logging, os, random, re, copy
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("v2-delta2")
random.seed(123)

GAMMA_PATH = Path(r"D:\Developer\Desktop\ScamShield\datasets\v2\annotated\dataset_v2_gamma.csv")
OUTPUT_PATH = GAMMA_PATH
BACKEND_COPY = Path(r"D:\Developer\Desktop\ScamShield\backend\data\dataset_v2_gamma.csv")

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
        "id": f"{category}_{index:04d}",
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
        "annotation_notes": "Delta2 expansion for weak category.",
        "created_at": now,
        "updated_at": now,
    }

# ---- TELECOM scams (6 FNs on gold: 3 English + hi/ta/te Airtel scams) ----
HI_TELECOM_SCAM = [
    "Airtel: Aapka recharge plan expire hone wala hai. Renew karo app se warna service band.",
    "Jio: Aapka plan kal expire ho raha hai. Rs 599 ka recharge karo warna service band.",
    "VI: Unlimited plan band hone wala hai. Abhi recharge karo warna number block.",
    "BSNL: Aapka SIM expiry date nikal gayi. Re-KYC karo nearest office mein.",
    "Airtel: Aapke account mein Rs 25,000 ka cashback. Claim at http://airtel-offer.tk.",
    "TRAI: Aapka number spam complaints ki vajah se band kiya jayega. Pay Rs 5,000 penalty.",
    "Jio: Free 5G upgrade. Rs 999 processing fee bhejein. http://jio-upgrade.top.",
    "Aapka SIM doosre city mein activate hua hai. Not you? Call 1800-123-4567 immediately.",
    "DoT: Aapka SIM mobile fraud mein use hua. Abhi 1800-425-6789 pe contact karein.",
    "VI: Aapke 50,000 reward points expire. Redeem at http://vi-rewards.xyz.",
]

TA_TELECOM_SCAM = [
    "Airtel: Ungal recharge plan expire aaga irukku. Renew pannugal app la.",
    "Jio: Ungal plan naalai mudiyapoguthu. Rs 599 recharge pannunga.",
    "VI: Ungal unlimited plan mudiyapoguthu. Ippave recharge pannuga.",
    "BSNL: Ungal SIM expiry date kadandhuduchi. Re-KYC nearest office la pannuga.",
    "Airtel: Ungal account ku Rs 25,000 cashback. Claim at http://airtel-offer.tk.",
    "TRAI: Ungal number spam complaint kaarana block aagum. Rs 5,000 fine kattuga.",
    "Jio: Free 5G upgrade. Rs 999 processing fee. http://jio-upgrade.top.",
    "Ungal SIM vere city la activate aachu. Neengal illana 1800-123-4567 ku call pannuga.",
    "DoT: Ungal SIM mobile fraud la use pannanga. Ippave 1800-425-6789 ku call pannuga.",
    "VI: Ungal 50,000 reward points expire aaguthu. Redeem at http://vi-rewards.xyz.",
]

TE_TELECOM_SCAM = [
    "Airtel: Mee recharge plan expire avutundi. Renew chesukondi app lo.",
    "Jio: Mee plan repu expire avutundi. Rs 599 recharge chesukondi.",
    "VI: Mee unlimited plan expire avutundi. Ippude recharge chesukondi.",
    "BSNL: Mee SIM expiry date aipoyindi. Re-KYC nearest office lo chesukondi.",
    "Airtel: Mee account lo Rs 25,000 cashback. Claim at http://airtel-offer.tk.",
    "TRAI: Mee number spam complaints valana block avutundi. Rs 5,000 fine kattandi.",
    "Jio: Free 5G upgrade. Rs 999 processing fee. http://jio-upgrade.top.",
    "Mee SIM vere city lo activate ayyindi. Meeru kaka pote 1800-123-4567 ki call cheyandi.",
    "DoT: Mee SIM mobile fraud lo use chesaru. Ippude 1800-425-6789 ki call cheyandi.",
    "VI: Mee 50,000 reward points expire avutunnayi. Redeem at http://vi-rewards.xyz.",
]

EN_TELECOM_SCAM = [
    "Airtel: Your recharge plan is expiring soon. Renew now to avoid interruption.",
    "Jio: Your plan expires tomorrow. Recharge Rs 599 to continue unlimited benefits.",
    "VI: Your unlimited plan is about to expire. Recharge now to keep your number active.",
    "TRAI: Your SIM will be disconnected for policy violation. Pay Rs 10,000 penalty.",
    "DoT: Your mobile number used in illegal activities. Contact cyber cell immediately.",
    "Airtel: Your reward points worth Rs 5,000 expiring. Redeem at http://airtel-rewards.tk.",
    "Jio: You have won 50GB free data. Claim at http://jio-free-data.xyz.",
    "VI: Your number selected for premium upgrade. Pay Rs 2,500 activation fee.",
    "BSNL: Your landline bill overdue Rs 6,500. Legal notice dispatched to your address.",
    "Your SIM card has been deactivated due to KYC expiry. Re-verify online now.",
]

# ---- SHOPPING scams (6 FNs on gold: Amazon/Flipkart dispatch/delivery) ----
HI_SHOPPING_SCAM = [
    "Aapka Amazon order dispatch ho gaya hai. Track karo yahan: http://amazon-track.tk.",
    "Flipkart: Aapka order bhej diya gaya hai. Yahan track karein: http://flipkart-track.xyz.",
    "Amazon: Aapke order mein problem hai. Is link se update karo: http://amazon-update.in.",
    "Meesho: Aapka parcel dispatch. Delivery date confirm karo: http://meesho-dispatch.tk.",
    "Amazon: Aapka return pickup confirm hai. Kal 10-1 baje aayega delivery boy.",
    "Flipkart: Exchange ke liye pickup scheduled. Product ready rakhein.",
    "Amazon: Aapki delivery aaj 6-9 PM ke beech hogi. Ghar pe rahein.",
    "Yourntra: Aapka order dispatch. 5-7 din mein delivery. Track karo app se.",
    "Snapdeal: Aapka order shipped. Delivery address confirm karo: http://snapdeal-verify.xyz.",
    "Amazon: COD order Rs 2,499 out for delivery. Exact cash rakhein.",
]

TA_SHOPPING_SCAM = [
    "Amazon order dispatch aagirukku. Track pannugal: http://amazon-track.tk.",
    "Flipkart: Ungal order anupapadugirathu. Track pannugal: http://flipkart-track.xyz.",
    "Amazon: Ungal order delivery ku varudhu. Konjam update pannuga: http://amazon-update.in.",
    "Meesho: Ungal parcel dispatch aachu. Delivery date confirm pannuga.",
    "Amazon: Ungal return pickup confirm aachu. Naalaikku 10-1 varuvaanga.",
    "Flipkart: Exchange pickup scheduled aachu. Product ready vaithundu.",
    "Amazon: Ungal delivery innikku 6-9 PM. Veetla irundhuga.",
    "Myntra: Ungal order dispatch. 5-7 days la delivery varum. App la track pannuga.",
    "Snapdeal: Ungal order shipped. Delivery address confirm pannuga: http://snapdeal-verify.xyz.",
    "Amazon: COD order Rs 2,499 out for delivery. Exact cash vaithundu.",
]

TE_SHOPPING_SCAM = [
    "Amazon order dispatch ayindi. Track cheyandi: http://amazon-track.tk.",
    "Flipkart: Mee order pampabadindi. Track cheyandi: http://flipkart-track.xyz.",
    "Amazon: Mee order lo problem undi. Update cheyandi: http://amazon-update.in.",
    "Meesho: Mee parcel dispatch ayyindi. Delivery date confirm cheyandi.",
    "Amazon: Mee return pickup confirm ayyindi. Repu 10-1 varuvalu.",
    "Flipkart: Exchange pickup scheduled. Product ready ga unchandi.",
    "Amazon: Mee delivery iedu 6-9 PM madhya. Intlo undandi.",
    "Myntra: Mee order dispatch. 5-7 days lo delivery. App lo track cheyandi.",
    "Snapdeal: Mee order shipped. Delivery address confirm cheyandi.",
    "Amazon: COD order Rs 2,499 out for delivery. Exact cash unchandi.",
]

# ---- FAKE_CUSTOMER_CARE (3 FNs: Amazon return, LinkedIn, multilingual) ----
HI_CUSTOMER_CARE = [
    "Amazon: Aapka order return ho gaya hai. Refund ke liye bank details update karo.",
    "LinkedIn: Aapka account restriction ke liye pending hai. Verify at http://linkedin-verify.tk.",
    "Amazon Pay: Aapke wallet se Rs 5,000 debit hua hai. Dispute? Call 1800-123-4567.",
    "Google: Aapka account suspicious activity ki vajah se block ho gaya. http://google-recover.tk.",
    "Netflix: Aapka payment fail ho gaya. Card update karo warna account band.",
    "Facebook: Aapka page delete kar diya gaya hai. Appeal at http://fb-appeal.xyz.",
    "Swiggy: Aapka account mein Rs 15,000 cashback. Claim karo: http://swiggy-gold.xyz.",
    "Zomato: Pro membership Rs 2,999 auto-renew. Cancel nahi kiya to charge hoga.",
    "Amazon Prime: Rs 1,499 auto-renewal successful. Cancel at http://amazon-cancel.tk.",
    "Google One: 100GB storage upgrade Rs 1,300/year. Pay now to avoid data loss.",
]

TA_CUSTOMER_CARE = [
    "Amazon: Ungal order return aagirukku. Refund ku bank details update pannuga.",
    "LinkedIn: Ungal account restriction pending. Verify at http://linkedin-verify.tk.",
    "Amazon Pay: Ungal wallet la Rs 5,000 debit aachu. Dispute na 1800-123-4567 ku call.",
    "Google: Ungal account suspicious activity la block aachu. http://google-recover.tk.",
    "Netflix: Ungal payment fail aachu. Card update pannuga illana account block.",
    "Facebook: Ungal page delete pannitanga. Appeal at http://fb-appeal.xyz.",
    "Swiggy: Ungal account ku Rs 15,000 cashback. Claim pannuga: http://swiggy-gold.xyz.",
    "Zomato: Pro membership Rs 2,999 auto-renew. Cancel pannalum charge aagum.",
    "Amazon Prime: Rs 1,499 auto-renewal aachu. Cancel at http://amazon-cancel.tk.",
]

TE_CUSTOMER_CARE = [
    "Amazon: Mee order return ayyindi. Refund ki bank details update cheyandi.",
    "LinkedIn: Mee account restriction pending. Verify at http://linkedin-verify.tk.",
    "Amazon Pay: Mee wallet nundi Rs 5,000 debit ayyindi. Dispute ante 1800-123-4567 ki call.",
    "Google: Mee account suspicious activity valla block ayyindi. http://google-recover.tk.",
    "Netflix: Mee payment fail ayyindi. Card update cheyandi leka account block.",
    "Facebook: Mee page delete chesaru. Appeal at http://fb-appeal.xyz.",
    "Swiggy: Mee account lo Rs 15,000 cashback. Claim cheyandi: http://swiggy-gold.xyz.",
    "Zomato: Pro membership Rs 2,999 auto-renew. Cancel chesina charge avutundi.",
    "Amazon Prime: Rs 1,499 auto-renewal ayyindi. Cancel at http://amazon-cancel.tk.",
]

# ---- MULTILINGUAL OTP scam expansion ----
HI_OTP2 = [
    "Aapka Google verification code 482916. 5 minute mein expire. Kisi ko na bataye.",
    "Amazon OTP 563412 login ke liye. Not you? Call 1800-3000-1234.",
    "PhonePe OTP 345678. Naya beneficiary. Not you? Forward OTP to 9988776655.",
    "SBI OTP 891234. Rs 45,000 transfer. Not you? Call 1800-425-3800.",
    "WhatsApp OTP 673489. Share na karein. Forward 9876543210 agar aapne nahi kiya.",
    "IRCTC OTP 945612. PNR cancellation. Not you? Call immediately.",
    "GPay OTP 623489. Rs 12,500 payment. Not you? Share OTP to reverse.",
    "Paytm OTP 890123. Rs 25,000 wallet transfer. Send OTP to block.",
    "Facebook OTP 784512 password reset. Not you? Reply OTP to secure.",
    "Netflix OTP 234567 account recovery. Share OTP to lock if not you.",
]

TA_OTP2 = [
    "Google verification code 482916. 5 minutes la expire aagum. Yaarukkum share pannathinga.",
    "Amazon OTP 563412 login ku. Neenga illana 1800-3000-1234 ku call.",
    "PhonePe OTP 345678. Puthu beneficiary. Not you? OTP ah forward pannuga.",
    "SBI OTP 891234. Rs 45,000 transfer. Neenga illana 1800-425-3800.",
    "WhatsApp OTP 673489. Share pannathinga. Forward 9876543210.",
    "IRCTC OTP 945612. PNR cancellation. Neenga illana call pannuga.",
    "GPay OTP 623489. Rs 12,500 payment. Not you? OTP share pannuga reverse ku.",
    "Paytm OTP 890123. Rs 25,000 transfer. OTP anupuga block panna.",
    "Facebook OTP 784512 password reset. Not you? OTP reply pannuga secure panna.",
]

TE_OTP2 = [
    "Google verification code 482916. 5 minutes lo expire. Evvariki share cheyyakandi.",
    "Amazon OTP 563412 login ki. Meeru kaka pote 1800-3000-1234 ki call.",
    "PhonePe OTP 345678. Kotha beneficiary. Not you? OTP forward cheyandi.",
    "SBI OTP 891234. Rs 45,000 transfer. Meeru kaka pote 1800-425-3800.",
    "WhatsApp OTP 673489. Share cheyyakandi. Send to 9876543210.",
    "IRCTC OTP 945612. PNR cancellation. Meeru kaka pote call cheyandi.",
    "GPay OTP 623489. Rs 12,500 payment. Not you? OTP share cheyandi reverse ki.",
]

# ---- MULTILINGUAL UPI_FRAUD expansion ----
HI_UPI = [
    "GPay se Rs 5,000 Rahul ko bheje gaye. Ref: 7890123456. Kya aapne kiya?",
    "PhonePe: Rs 12,500 ka collect request aaya hai 'QuickMart' se. Approve karein?",
    "Paytm: Aapka wallet se Rs 2,000 debit. Not you? Call 1800-123-4567.",
    "Amazon Pay: Rs 8,500 ka UPI payment unknown merchant ko. Dispute karein.",
    "BHIM: Rs 15,000 aapke account se nikal gaye. Block karein? OTP bhejein.",
    "GPay: Aapka UPI PIN reset hua. Not you? Share OTP to block.",
    "PhonePe: Rs 50,000 ka loan approved. EMI Rs 2,500/month. Reject? Reply NO.",
    "CRED: Credit card bill Rs 45,000 auto-pay scheduled. Cancel at http://cred-cancel.xyz.",
    "Paytm: Fastag Rs 500 recharge failed. Your tag may be deactivated.",
    "GPay: UPI Circle mein 2 log add hue. Not you? Call 1800-180-1234.",
]

TA_UPI = [
    "GPay le Rs 5,000 Rahul ku anupirukkom. Ref: 7890123456. Neenga panniningala?",
    "PhonePe: Rs 12,500 collect request 'QuickMart' la irundhu. Approve pannuringala?",
    "Paytm: Ungal wallet la Rs 2,000 debit aachu. Not you? 1800-123-4567 ku call.",
    "Amazon Pay: Rs 8,500 unknown merchant ku UPI payment. Dispute pannuga.",
    "BHIM: Rs 15,000 ungal account la send aachu. Block pannattuma? OTP anupuga.",
    "GPay: Ungal UPI PIN reset aachu. Not you? OTP share pannuga block panna.",
    "PhonePe: Rs 50,000 loan approved. EMI Rs 2,500/month. Reject pannattuma?",
    "CRED: Credit card bill Rs 45,000 auto-pay scheduled. Cancel at http://cred-cancel.xyz.",
    "Paytm: Fastag Rs 500 recharge fail aachu. Tag deactivate aagum.",
    "GPay: UPI Circle ku 2 per add aachu. Not you? 1800-180-1234 ku call.",
]

TE_UPI = [
    "GPay lo Rs 5,000 Rahul ki pampiyaru. Ref: 7890123456. Meeru chesara?",
    "PhonePe: Rs 12,500 collect request 'QuickMart' nundi. Approve chestara?",
    "Paytm: Mee wallet nundi Rs 2,000 debit ayyindi. Not you? 1800-123-4567 ki call.",
    "Amazon Pay: Rs 8,500 unknown merchant ki UPI payment. Dispute cheyandi.",
    "BHIM: Rs 15,000 mee account nundi velipoyayi. Block cheyala? OTP pampandi.",
    "GPay: Mee UPI PIN reset ayyindi. Not you? OTP share cheyandi block ki.",
    "PhonePe: Rs 50,000 loan approved. EMI Rs 2,500/month. Reject chestara?",
    "CRED: Credit card bill Rs 45,000 auto-pay scheduled. Cancel at http://cred-cancel.xyz.",
    "Paytm: Fastag Rs 500 recharge fail ayyindi. Tag deactivate avutundi.",
    "GPay: UPI Circle lo 2 peru add ayyaru. Not you? 1800-180-1234 ki call.",
]

# ---- MULTILINGUAL PERSONAL scam (family emergency) ----
HI_PERSONAL_SCAM2 = [
    "Papa, main hospital mein hoon. Accident ho gaya. Rs 30,000 bhejo jaldi.",
    "Mummy, mera phone kho gaya hai. Is number se likh raha hoon. Rs 15,000 bhejo.",
    "Beta, main police station mein hoon. Galti se case mein fas gaya. Rs 50,000 bhejo.",
    "Bhai, meri tabiyat kharab hai. Operation ke liye Rs 25,000 chahiye. Jaldi bhejo.",
    "Sir, main aapke bete ka classmate hoon. Unhe accident hua hai. Rs 20,000 chahiye.",
    "Rahul bhai, main foreign mein phas gaya hoon. Ticket ke liye Rs 40,000 bhejo.",
    "Maa, mujhe kidnap kar liya gaya hai. Police ko mat batana. Rs 2,00,000 chahiye.",
    "Didi, main ghar se bhag gaya hoon. Wapas aane ke liye Rs 10,000 bhejo.",
    "Chachu, main hospital mein hoon. Emergency operation. Rs 60,000 jaldi bhejo.",
    "Bhabhi, bhai ko accident hua hai. Hospital admit hai. Rs 35,000 bhejo.",
]

TA_PERSONAL_SCAM2 = [
    "Appa, naan hospital la irukken. Accident aachu. Rs 30,000 anupunga.",
    "Amma, en phone poyiduchu. Indha number la pesuren. Rs 15,000 anupunga.",
    "Anna, naan police station la irukken. Case la sikkiten. Rs 50,000 anupunga.",
    "Akka, enaku operation ku Rs 25,000 venum. Jaldi anupunga.",
    "Sir, naan unga ponnoda classmate. Avangalku accident aachu. Rs 20,000 venum.",
    "Thambi, naan foreign la sikkiten. Ticket ku Rs 40,000 anupunga.",
    "Amma, enna kidnap pannitanga. Police ku sollathinga. Rs 2,00,000 venum.",
]

TE_PERSONAL_SCAM2 = [
    "Nanna, nenu hospital lo unna. Accident ayyindi. Rs 30,000 pampandi.",
    "Amma, naa phone poyindi. Ee number nundi matladutunna. Rs 15,000 pampandi.",
    "Anna, nenu police station lo unna. Case lo chikkina. Rs 50,000 pampandi.",
    "Akka, naku operation ki Rs 25,000 kavali. Tondaraga pampandi.",
    "Sir, nenu mee koduku classmate. Ayanaku accident ayyindi. Rs 20,000 kavali.",
    "Thammudu, nenu foreign lo chikkina. Ticket ki Rs 40,000 pampandi.",
    "Amma, nannu kidnap chesaru. Police ki cheppakandi. Rs 2,00,000 kavali.",
]

# ---- MULTILINGUAL BANKING_FRAUD expansion ----
HI_BANKING = [
    "SBI: Aapka account 3 alag cities se access hua. Verify at http://sbi-verify.tk.",
    "HDFC: Rs 1,25,000 credit card Dubai mein use hua. Block at http://hdfc-block.xyz.",
    "ICICI: SIM swap request aaya hai. Aapka account compromised ho sakta hai.",
    "Axis Bank: Aapke account mein Rs 50,00,000 ka loan approve. Rs 5,000 processing fee.",
    "PNB: Aapka net banking password expired. Update at http://pnb-update.in.",
    "Canara Bank: Aapka locker rent overdue. Rs 6,500 pay karo warna locker seal.",
    "Bank of Baroda: Aapka account money laundering mein involve. Call compliance officer.",
    "Kotak: Aapki credit card limit badh gayi Rs 8,00,000. Accept at http://kotak-offer.xyz.",
    "Yes Bank: Aapka savings account upgraded. Rs 3,500 annual fee pay karo.",
    "RBI: All banks need customer re-verification. Update at http://rbi-verify.tk.",
]

TA_BANKING = [
    "SBI: Ungal account 3 cities la access pannanga. Verify at http://sbi-verify.tk.",
    "HDFC: Rs 1,25,000 credit card Dubai la use pannanga. Block at http://hdfc-block.xyz.",
    "ICICI: SIM swap request. Ungal account compromised aagalaam.",
    "Axis Bank: Rs 50,00,000 loan approved. Rs 5,000 processing fee.",
    "PNB: Net banking password expired. Update at http://pnb-update.in.",
]

TE_BANKING = [
    "SBI: Mee account 3 cities nundi access chesaru. Verify at http://sbi-verify.tk.",
    "HDFC: Rs 1,25,000 credit card Dubai lo use chesaru. Block at http://hdfc-block.xyz.",
    "ICICI: SIM swap request. Mee account compromised avocchu.",
    "Axis Bank: Rs 50,00,000 loan approved. Rs 5,000 processing fee.",
    "PNB: Net banking password expired. Update at http://pnb-update.in.",
]

# ---- MULTILINGUAL LOTTERY scam ----
HI_LOTTERY = [
    "Mubarak ho! Aapne KBC mein Rs 75,00,000 jeete. Call 1800-123-4567 claim ke liye.",
    "Amazon: Aap 1,000,000th customer. iPhone 16 jeete! Claim: http://amazon-winner.tk.",
    "Google: Aapki search history ne Rs 3,00,000 jeete. Call now to claim.",
    "Flipkart: Aapne Big Billion Day mein Rs 1,00,000 shopping voucher jeeta.",
    "Reliance: Aapne Mukesh Ambani birthday draw mein Rs 25,00,000 jeete.",
    "Tata Motors: Aapne Tata Nexon car jeeti. Rs 25,000 delivery charges pay karo.",
    "WhatsApp: Aapka forwarded message 1,00,000 times share hua. Rs 50,000 prize.",
    "Pepsi: Aapne Dubai trip jeeti. Rs 15,000 processing fee bhejein.",
    "Coca-Cola: Aapne Rs 10,00,000 summer contest mein jeete. Call now.",
    "Samsung: Aapne Galaxy S25 Ultra launch event mein jeeta. Rs 2,500 shipping.",
]

TA_LOTTERY = [
    "Vaazhthukkal! KBC la Rs 75,00,000 jechinga. 1800-123-4567 ku call pannuga.",
    "Amazon: Neenga 1,000,000th customer. iPhone 16 jechinga! Claim: http://amazon-winner.tk.",
    "Google: Ungal search history Rs 3,00,000 jechiduchu. Ippave call pannuga.",
    "Flipkart: Big Billion Day la Rs 1,00,000 shopping voucher jechinga.",
    "Reliance: Mukesh Ambani birthday draw la Rs 25,00,000 jechinga.",
]

TE_LOTTERY = [
    "Abhinaandanalu! KBC lo Rs 75,00,000 gachincharu. 1800-123-4567 ki call cheyandi.",
    "Amazon: Meeru 1,000,000th customer. iPhone 16 gachincharu! Claim: http://amazon-winner.tk.",
    "Google: Mee search history Rs 3,00,000 gachinchindi. Ippude call cheyandi.",
    "Flipkart: Big Billion Day lo Rs 1,00,000 shopping voucher gachincharu.",
    "Reliance: Mukesh Ambani birthday draw lo Rs 25,00,000 gachincharu.",
]

# ---- LEGITIMATE_PERSONAL more non-English ----
HI_PERSONAL_MORE2 = [
    "Chalo aaj party karte hain. Sabko bulao. Raat 8 baje.",
    "Aaj bahut garmi hai. AC chala do please.",
    "Bachche school se aa gaye. Unko khana khila diya.",
    "Office se late aaunga. Meeting chal rahi hai.",
    "Kal Sunday hai. Gharpe sab log milenge.",
    "Train 9:15 PM ki hai. Platform 3. Saman sambhal ke.",
    "Doctor ne kaha hai aaram karne ko. Chutti le lo.",
    "Aaj mere saath shopping chaloge? Bahut saari cheezein leni hain.",
    "Ghar ke liye naya sofa lena hai. Kal dekhte hain.",
    "Beta, padhai kar lo. Exam aane wale hain.",
]

TA_PERSONAL_MORE2 = [
    "Inniku party pannalaam. Ellaaraiyum koottunga. Raathiri 8 maniku.",
    "Inniku romba veyyil. AC podunga please.",
    "Pillai school irundhu vanthutanga. Unavu kuduthen.",
    "Office la late aaguen. Meeting nadakuthu.",
    "Naalaiku Sunday. Veetla ellarum sernel.",
    "Train 9:15 PM platform 3. Parthu ponga.",
    "Doctor rest eduka sonnar. Leave pottudunga.",
    "Inniku en kooda shopping varathingala? Niraiya items vanganum.",
]

TE_PERSONAL_MORE2 = [
    "Iedu party cheddam. Andarini piluvandi. Ratri 8 ki.",
    "Iedu chaala veyil. AC veyyandi please.",
    "Pillalu school nundi vacharu. Vaallaki annam pettanu.",
    "Office nundi late ga vastanu. Meeting jarugutundi.",
    "Repu Sunday. Intlo andaram kalustam.",
    "Train 9:15 PM ki platform 3. Jaagratha.",
    "Doctor rest teesukomannaru. Leave veyyandi.",
    "Iedu natho shopping ki vastara? Chaala items konali.",
]

# ---- LEGITIMATE_SHOPPING more non-English ----
HI_SHOPPING2 = [
    "Amazon: Aapka order kal deliver hoga. 6-9 PM ke beech.",
    "Flipkart: Aapka order out for delivery. Track app se karein.",
    "Myntra: 50-80% off end of season sale! Shop now at http://myntra.com.",
    "Meesho: Diwali sale live! 90% off on home decor. Order now.",
    "Ajio: New collection arrived. Extra 20% off on prepaid orders.",
    "Tata CLiQ: Electronics sale. Up to 60% off on smartphones.",
    "Nykaa: Beauty products par 30% off. Use code NYKAA30.",
    "Zepto: Aapka order aa raha hai. 10 minute mein delivery.",
    "Blinkit: Grocery order pick ho gaya. 15 minute mein.",
    "BigBasket: Kal ki delivery confirm. Slot 7-9 AM.",
]

TA_SHOPPING2 = [
    "Amazon: Ungal order naalai deliver aagum. 6-9 PM.",
    "Flipkart: Ungal order out for delivery. App la track pannuga.",
    "Myntra: 50-80% off end of season sale! Shop now.",
    "Meesho: Diwali sale live! 90% off home decor.",
    "Ajio: New collection. Extra 20% off prepaid orders.",
]

TE_SHOPPING2 = [
    "Amazon: Mee order repu deliver avutundi. 6-9 PM.",
    "Flipkart: Mee order out for delivery. App lo track cheyandi.",
    "Myntra: 50-80% off end of season sale! Shop now.",
    "Meesho: Diwali sale live! 90% off home decor.",
    "Ajio: New collection. Extra 20% off prepaid orders.",
]

# ---- LEGITIMATE_TELECOM more non-English ----
HI_TELECOM2 = [
    "Airtel: Aapka Rs 299 plan renew ho gaya. Valid 28 din.",
    "Jio: 2GB/day data add. Balance 22GB. Recharge at http://jio.com.",
    "VI: Aapka Rs 599 unlimited plan active hai. Valid 84 din.",
    "BSNL: Aapka broadband bill Rs 799 generate. Due date 15 Aug.",
    "Airtel Black: Combined plan Rs 1,299/month. All services active.",
    "JioFiber: 100 Mbps plan active. Next billing 5 Sep.",
    "VI: Family plan Rs 699 mein 6 members. All benefits active.",
    "BSNL: FTTH plan 30 Mbps unlimited. Rs 799/month.",
    "Airtel: Postpaid bill Rs 1,245 generated. Auto-pay on 5 Sep.",
    "Jio: Rs 51 data add-on active. 1GB/day for 3 days.",
]

TA_TELECOM2 = [
    "Airtel: Ungal Rs 299 plan renew aachu. Valid 28 days.",
    "Jio: 2GB/day data add. Balance 22GB. Recharge at http://jio.com.",
    "VI: Ungal Rs 599 unlimited plan active. Valid 84 days.",
    "BSNL: Broadband bill Rs 799 generate. Due date 15 Aug.",
]

TE_TELECOM2 = [
    "Airtel: Mee Rs 299 plan renew ayyindi. Valid 28 days.",
    "Jio: 2GB/day data add. Balance 22GB. Recharge at http://jio.com.",
    "VI: Mee Rs 599 unlimited plan active. Valid 84 days.",
    "BSNL: Broadband bill Rs 799 generate. Due date 15 Aug.",
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
            add_samples(category, is_scam, risk, texts, lang=lang)

    # 1. TELECOM_SCAM - multilingual Airtel recharge scams (6 FNs)
    add_multilingual("TELECOM_SCAM", True, "HIGH", {
        "en": EN_TELECOM_SCAM, "hi-en": HI_TELECOM_SCAM,
        "ta-en": TA_TELECOM_SCAM, "te-en": TE_TELECOM_SCAM
    })

    # 2. LEGITIMATE_SHOPPING scams - multilingual delivery/order (6 FNs)
    add_multilingual("LEGITIMATE_SHOPPING", True, "HIGH", {
        "hi-en": HI_SHOPPING_SCAM, "ta-en": TA_SHOPPING_SCAM, "te-en": TE_SHOPPING_SCAM
    })

    # 3. FAKE_CUSTOMER_CARE - multilingual (3 FNs)
    add_multilingual("FAKE_CUSTOMER_CARE", True, "HIGH", {
        "hi-en": HI_CUSTOMER_CARE, "ta-en": TA_CUSTOMER_CARE, "te-en": TE_CUSTOMER_CARE
    })

    # 4. OTP_SCAM multilingual
    add_multilingual("OTP_SCAM", True, "HIGH", {
        "hi-en": HI_OTP2, "ta-en": TA_OTP2, "te-en": TE_OTP2
    })

    # 5. UPI_FRAUD multilingual
    add_multilingual("UPI_FRAUD", True, "HIGH", {
        "hi-en": HI_UPI, "ta-en": TA_UPI, "te-en": TE_UPI
    })

    # 6. LEGITIMATE_UPI multilingual
    add_samples("LEGITIMATE_UPI", False, "LOW", [
        "GPay: Rs 500 received from friend for dinner split. Ref: 456789012345.",
        "PhonePe: Your recharge of Rs 299 for Jio successful. Valid 28 days.",
        "Paytm: FASTag recharge Rs 500 successful. Balance: Rs 1,250.",
        "BHIM: Your LPG payment of Rs 1,050 made to HP Gas. Ref: 567890123456.",
        "CRED: Rent payment of Rs 22,000 to Landlord successful. 900 CRED coins.",
        "GPay: Your weekly transaction summary: 8 payments totalling Rs 6,250.",
        "PhonePe: Gold purchase of Rs 1,500 successful. 0.22g added.",
        "Amazon Pay: Your NPS contribution of Rs 3,000 invested. Tax benefit under 80C.",
        "GPay: College fee of Rs 95,000 paid to IIT Bombay. Receipt generated.",
        "BHIM: Your mutual fund SIP of Rs 5,000 in HDFC Top 100 invested.",
    ])

    # 7. LEGITIMATE_PERSONAL multilingual
    add_multilingual("LEGITIMATE_PERSONAL", False, "LOW", {
        "hi-en": HI_PERSONAL_MORE2, "ta-en": TA_PERSONAL_MORE2, "te-en": TE_PERSONAL_MORE2
    })

    # 8. LEGITIMATE_SHOPPING legit multilingual
    add_multilingual("LEGITIMATE_SHOPPING", False, "LOW", {
        "hi-en": HI_SHOPPING2, "ta-en": TA_SHOPPING2, "te-en": TE_SHOPPING2
    })

    # 9. LEGITIMATE_TELECOM legit multilingual
    add_multilingual("LEGITIMATE_TELECOM", False, "LOW", {
        "hi-en": HI_TELECOM2, "ta-en": TA_TELECOM2, "te-en": TE_TELECOM2
    })

    # 10. PERSONAL_SCAM multilingual
    add_multilingual("PERSONAL_SCAM", True, "HIGH", {
        "hi-en": HI_PERSONAL_SCAM2, "ta-en": TA_PERSONAL_SCAM2, "te-en": TE_PERSONAL_SCAM2
    })

    # 11. BANKING_FRAUD multilingual
    add_multilingual("BANKING_FRAUD", True, "HIGH", {
        "hi-en": HI_BANKING, "ta-en": TA_BANKING, "te-en": TE_BANKING
    })

    # 12. LOTTERY_SCAM multilingual
    add_multilingual("LOTTERY_SCAM", True, "HIGH", {
        "hi-en": HI_LOTTERY, "ta-en": TA_LOTTERY, "te-en": TE_LOTTERY
    })

    # 13. Top up weak legit categories
    add_samples("LEGITIMATE_TELECOM", False, "LOW", [
        "Jio: Your 5G service activated in your area. Enjoy unlimited 5G data.",
        "Airtel: Welcome Rs 100 cashback on next recharge above Rs 299.",
        "VI: Your number eligible for free upgrade to 4G. Visit store with Aadhaar.",
        "BSNL: Your complaint #1234567890 resolved. Thank you for your patience.",
        "TRAI: DND check: Your number is registered. No promotional SMS till 30 Sep.",
        "Airtel: SIM replacement request completed. New SIM active from tomorrow.",
        "JioFiber: Your installation technician will visit tomorrow 9-11 AM.",
        "VI: Your family add-on plan of Rs 99/month for extra 50GB activated.",
        "BSNL: Your FTTH broadband usage: 1.5TB of 3TB FUP limit.",
        "Airtel Xstream: Netflix + Prime + Hotstar included in your plan.",
    ])
    add_samples("LEGITIMATE_SHOPPING", False, "LOW", [
        "Amazon: Your order of books has been delivered. Rate your experience.",
        "Flipkart: Your exchange of old phone completed. Rs 8,000 credit applied.",
        "Myntra: Your size exchange approved. New item will be shipped after pickup.",
        "Meesho: Your order has reached your city hub. Out for delivery tomorrow.",
        "Nykaa: Your order is being packed. You will receive tracking shortly.",
        "Snapdeal: Your product has been dispatched from seller's warehouse.",
        "Tata CLiQ: Your order of smartwatch has been shipped. Track now.",
        "Ajio: Extra Rs 500 off on prepaid orders above Rs 2,000. Code AJIO500.",
        "Lenskart: Your new glasses are ready. Track at http://lenskart.com/track.",
        "Cult.fit: Your activewear order dispatched. Get fit with Cult!",
    ])
    add_samples("LEGITIMATE_COLLEGE", False, "LOW", [
        "IIT Madras: BS Degree program applications open for 2025 session.",
        "BITS Pilani: Your semester fee payment confirmed. Receipt available.",
        "NIT Warangal: Hostel reopening on 10 Aug. Report by 5 PM.",
        "Jadavpur University: Your admission confirmation fee Rs 5,000 paid.",
        "Manipal: Your semester registration pending. Complete within 7 days.",
        "Amrita University: Placement training sessions start from 12 Aug.",
        "VIT: Your internal assessment marks for July published in VTOP.",
        "SRM: Your project review scheduled for 15 Aug with guide.",
        "Christ University: Your library membership card ready for collection.",
        "LPU: Your scholarship amount of Rs 40,000 credited to your account.",
    ])
    add_samples("LEGITIMATE_UTILITY", False, "LOW", [
        "Tata Power: Your bill payment of Rs 2,100 received. Thank you.",
        "BSES: Power maintenance in your area on 20 Aug 10 AM-2 PM.",
        "Adani Electricity: Your consumption 280 units this month. Bill Rs 1,680.",
        "Mahanagar Gas: Your gas bill of Rs 820 paid. Receipt: 123456789.",
        "HP Gas: Your LPG refill delivered. Please collect cylinder.",
        "Bharat Gas: Your subsidy of Rs 300 credited for refill #12345.",
        "IOCL: Your new gas connection application approved. Installation in 7 days.",
        "Chennai Metro Water: Your water connection bill Rs 380 generated.",
        "Delhi Jal Board: Water supply disruption on 22 Aug for maintenance.",
        "Society maintenance: Your parking renewal fee Rs 2,400 for 2025-26 due.",
    ])

    return new_rows

def main():
    logger.info("Loading existing gamma dataset...")
    existing_rows, existing_texts, existing_ids = load_existing(GAMMA_PATH)
    logger.info("Existing rows: %d, unique texts: %d", len(existing_rows), len(existing_texts))
    logger.info("Existing languages: %s", dict(Counter(r["language"] for r in existing_rows)))

    new_rows = generate_new_samples(existing_texts, existing_ids)
    logger.info("Generated %d new samples", len(new_rows))

    all_rows = existing_rows + new_rows
    scam_count = sum(1 for r in all_rows if r["is_scam"].lower() in ("true", "1", "yes"))
    legit_count = len(all_rows) - scam_count
    cats = Counter(r["category"] for r in all_rows)
    langs = Counter(r["language"] for r in all_rows)

    logger.info("Total: %d samples (%d scam, %d legit)", len(all_rows), scam_count, legit_count)
    logger.info("Categories: %d", len(cats))
    logger.info("Languages: %s", dict(langs))
    for cat, n in sorted(cats.items()):
        logger.info("  %s: %d", cat, n)

    for path in [OUTPUT_PATH, BACKEND_COPY]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)
        logger.info("Written to %s", path)

    logger.info("Done! Total samples: %d", len(all_rows))

if __name__ == "__main__":
    main()
