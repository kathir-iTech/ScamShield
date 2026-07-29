import json
import time
import urllib.request
import urllib.error
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

API_URL = "http://localhost:8001/analyze/text"

SCAM_SAMPLES = {
    "banking_scam": [
        "Your HDFC account has been blocked. Call 1800-123-4567 immediately to restore access.",
        "SBI Alert: Your debit card has been deactivated. Update KYC at https://sbi-kyc-update.xyz or your account will be frozen.",
        "ICICI Bank: Your account is temporarily suspended. Click here to restore access: http://bit.ly/icici-restore",
        "Axis Bank Warning: Unauthorized login detected from New Delhi. Confirm your identity or your account will be blocked.",
        "PNB Alert: Rs 49,500 debited from your account. Not you? Call 1800-XXX-XXX immediately to reverse.",
    ],
    "upi_scam": [
        "Your Google Pay UPI PIN has been reset. Click http://malicious.com to set new pin immediately.",
        "PhonePe: Rs 12,500 sent to Ramesh Kumar. UPI ref UPIRef1234. Not you? Block here: http://bit.ly/phonepe-block",
        "Paytm UPI: Your account is limited. Complete KYC to restore unlimited payments. https://paytm-kyc.tk",
        "BHIM UPI: You received Rs 2,000. Claim by entering your UPI PIN at https://bhim-reward.com/claim",
        "GPay: Your UPI ID has been compromised. Verify immediately: https://gpay-verify.xyz",
    ],
    "fake_job": [
        "Work from home job! Earn Rs50000/month. Pay Rs1999 registration fee.",
        "Urgent hiring for Amazon data entry. Salary Rs 35,000-60,000. No experience needed. Register: https://amazon-jobs.xyz",
        "Flipkart is hiring part-time workers. Earn Rs 500-2000 per day. Join today: Pay Rs 499 for registration kit.",
        "Google is offering Work From Home jobs. Type names and earn Rs 40,000/month. Processing fee Rs 1,500 required.",
        "Railway recruitment 2026. 50,000 vacancies. Apply now with registration fee Rs 1,200. Guaranteed job placement.",
    ],
    "courier_scam": [
        "Your FedEx package held at customs. Pay Rs999 clearance fee.",
        "DHL: Your international shipment is stuck at Mumbai customs. Pay Rs 3,200 for customs clearance. http://bit.ly/dhl-clear",
        "Blue Dart: Package delivery failed. Your parcel contains undeclared items. Pay Rs 5,000 penalty to avoid legal action.",
        "UPS: Your package from USA requires insurance clearance. Pay Rs 4,500 insurance fee for delivery.",
        "India Post: Your international parcel is detained. Customs clearance fee Rs 2,000 required. Contact immediately.",
    ],
    "otp_scam": [
        "Your Aadhaar OTP is 384729. KYC update required at http://evil.com.",
        "SBI: Your OTP for transaction is 729384. Forward this OTP to 9222222222 for verification.",
        "Aadhaar OTP: 516273. Share this OTP with our executive to complete KYC or your Aadhaar will be deactivated.",
        "Netflix: Your OTP is 638192. Share with our support agent for account recovery. Do not ignore.",
        "Facebook: Your login code is 482716. Forward this code to our verification bot on WhatsApp.",
    ],
    "investment_scam": [
        "Get 100% guaranteed returns in 7 days! Bitcoin investment. Minimum Rs1000.",
        "Stock market tips from experts. 100% guaranteed profit. Earn Rs 1 lakh in one week. Investment Rs 5,000 only.",
        "Cryptocurrency investment opportunity. Minimum investment Rs 10,000. Daily returns of 10% for lifetime.",
        "SEBI registered investment advisor. Get 10x returns in 30 days. Join our elite group. Fee Rs 15,000.",
        "Forex trading made easy. Earn $500 daily. Automated trading bot. One-time setup fee Rs 8,500.",
    ],
    "romance_scam": [
        "Hello dear, I'm US Army captain in Syria. I need your help to transfer $50000.",
        "I am a British oil engineer on offshore rig. I have fallen in love with you. Send me money for my visa to meet you.",
        "Hello dear. I am Maria from Russia. I want to marry you. Please send Rs 50,000 for my flight ticket to India.",
        "I am a UN doctor working in Congo. I received a gold shipment worth $5 million. Help me transfer it for 30% share.",
        "Sweetheart, I am a US soldier in Afghanistan. My leave has been denied. Pay $2,500 for my emergency leave approval.",
    ],
    "government_scam": [
        "Your PAN card used in illegal activities. Call Income Tax Dept immediately or face arrest.",
        "Income Tax Department: Tax evasion case registered against you. Pay Rs 50,000 penalty immediately to avoid arrest warrant.",
        "Your Aadhaar card will be deactivated. Update your Aadhaar now at https://uidai-update.xyz or face legal consequences.",
        "PM Kisan Yojana: You are eligible for Rs 6,000 installment. Click to claim: https://pmkisan-gov.xyz/claim",
        "Central Government: Rs 1,50,000 subsidy approved for your bank account. Pay Rs 2,500 processing fee to release funds.",
    ],
    "lottery_scam": [
        "Congratulations! You won Rs50,00,000 in Mega Millions lottery! Call 1800-123-4567 to claim your prize.",
        "You won an iPhone 16 Pro! Claim your prize at https://apple-lucky-winner.xyz. Pay Rs 999 for shipping.",
        "Google Lucky Draw: You won Rs 15,00,000. Contact Mr Sharma at 9876543210 with registration fee Rs 8,000.",
        "Amazon Great Indian Sale winner! You won Rs 5,00,000 shopping voucher. Tax processing fee Rs 3,500 required.",
        "KBC winner 2025! Your cheque of Rs 15,00,000 is ready. Processing fee Rs 2500 required. Call now!",
    ],
    "phishing_scam": [
        "Netflix: Your subscription suspended. Update payment at http://phishing.com.",
        "Your email account password will expire today. Keep same password: https://email-verify-now.xyz",
        "Instagram: Your account has been hacked. Recover now: https://instagram-recovery.xyz/login",
        "LinkedIn: Someone tried to access your account from Russia. Secure here: http://bit.ly/linkedin-secure",
        "Microsoft: Unusual sign-in detected. Verify your identity at https://microsoft-account-verify.com",
    ],
    "electricity_scam": [
        "Your electricity connection will be DISCONNECTED due to non-payment. Pay Rs 4500 immediately.",
        "TNEB: Your electricity connection will be disconnected tonight! Pay pending bill Rs 4500: http://tneb-bill.tk",
        "Electricity board: Your meter has been tampered. Pay penalty Rs 25000 to avoid FIR. http://elect-penalty.xyz",
        "BSES: Your electricity bill payment failed. Immediate disconnection. Pay now: http://bses-pay.top",
        "Current bill pay pannathinga! Disconnect panniduvinga. Link: http://tneb-alert.ga",
    ],
    "loan_scam": [
        "Personal loan approved! Rs5,00,000 instantly. Processing fee Rs2499.",
        "Instant personal loan up to Rs 25 lakhs. No paperwork. 0% interest for 6 months. Processing fee Rs 2,500.",
        "Bajaj Finserv: Your pre-approved loan of Rs 5,00,000 is ready. Pay Rs 3,000 documentation fee to disburse.",
        "Home loan at 2% interest rate! Government subsidy available. Register with Rs 5,000 processing fee.",
        "Student loan for abroad studies. 100% approval. No collateral. Pay Rs 2,000 application fee to proceed.",
    ],
    "qr_scam": [
        "Scan QR code to receive Rs5000 cashback! Limited offer.",
        "QR code scan panni Rs 10,000 gift voucher vangikunga! http://gift-qr.xyz",
        "Free recharging! Scan QR and get Rs 200 free mobile recharge. Limited offer: http://free-recharge.tk",
        "Google Pay QR code scanner! Scan any QR and earn rewards. Download: http://gpay-qr.ml",
        "Your parcel delivery needs QR payment of Rs 500 for customs. Scan: http://delivery-qr.tk",
    ],
}

LEGITIMATE_SAMPLES = [
    "Your Flipkart order #OD12345678 has been shipped. Track here: https://flipkart.com/track",
    "Your monthly Netflix subscription of Rs 199 will be charged on 15th. Manage your account settings.",
    "Your Amazon order #AMZ876543 is out for delivery. Expected by 8 PM. Track at https://amazon.in/track",
    "ICICI Bank: Your credit card bill of Rs 12,500 is due on 05-Apr-2026. Auto-debit will be processed.",
    "Swiggy: Your order from Dominos is being prepared. Estimated delivery by 7:30 PM. Track live on the app.",
    "Zomato: Table for 2 at Pizza Express confirmed for 28 Mar 8 PM. Order #ZB89765.",
    "HDFC Bank: Rs 5,000 credited to your account from NEFT. Ref: NEFT123456789.",
    "Your Uber ride is arriving. Driver: Rajesh, Car: MH12AB1234 White Swift. ETA 3 mins.",
    "Airtel: Your monthly plan of Rs 499 will expire on 31 Mar. Recharge now to continue uninterrupted service.",
    "IRCTC: Your train ticket for 12951 Mumbai-Delhi on 15 Apr is confirmed. PNR: 4123567890.",
    "Google: Your account verification code is 839201. This code expires in 10 minutes.",
    "LinkedIn: John Doe sent you a connection request. View profile: https://linkedin.com/in/johndoe",
    "WhatsApp: Your verification code is 482-931. Do not share this code with anyone.",
    "Paytm: Rs 250 received from Ravi Kumar. UPI Ref: 987654321098. Wallet balance: Rs 1,250.",
    "Your appointment with Dr Sharma at Apollo Hospital is confirmed for 10:30 AM on 20 Mar.",
    "SBI: Your FD of Rs 2,00,000 has matured. Maturity amount Rs 2,45,678 credited to savings account.",
    "Myntra: 50% off on your favorite brands! Use code MYNTRA50. Shop now: https://myntra.com/sale",
    "Vistara: Check-in for flight UK915 DEL-BOM on 22 Mar is now open. Web check-in: https://vistara.com/webcheckin",
    "PhonePe: Rs 1,200 bill paid for electricity. Receipt: PP-RCPT-928374. Auto-pay scheduled for next month.",
    "Zerodha: Your trade of 100 shares of TCS at Rs 3,450 executed successfully. Ledger updated.",
    "Google Pay: Rs1,200 sent to Priya Singh. UPI Ref: 987654321098.",
    "Your Netflix plan has been upgraded to Premium. Enjoy 4K streaming.",
    "Makemytrip: Your flight booking #MMT123456 from Mumbai to Delhi is confirmed.",
    "Your account password was changed successfully. If not you, reset immediately.",
    "Razorpay: Payment of Rs1,500 received from Acme Corp.",
]

EDGE_CASES = [
    {"text": "Your account blocked aagidhe, call 1800-123-4567 immediately to restore pannikonga", "expected_prediction": "scam", "expected_category": "banking_scam", "note": "Tanglish mixed language"},
    {"text": "Ungal SBI account KYC update pannitt illaina block aagum. https://sbi-update.tk", "expected_prediction": "scam", "expected_category": "banking_scam", "note": "Pure Tamil"},
    {"text": "Neraya cashback! Rs 5000 credit pannirukkom. Claim panniko: http://tiny.cc/cashback", "expected_prediction": "scam", "expected_category": "upi_scam", "note": "Pure Tamil UPI"},
    {"text": "&#128680; Alert! Your account will be blocked! &#128680; Call NOW 1800-123-4567", "expected_prediction": "scam", "expected_category": "banking_scam", "note": "Emoji in message"},
    {"text": "OTP: 384729", "expected_prediction": "safe", "expected_category": "legitimate", "note": "Very short OTP message"},
    {"text": "384729", "expected_prediction": "safe", "expected_category": "legitimate", "note": "Numbers only"},
    {"text": "URGENT: Your a/c blocked! Call 1800-123-4567", "expected_prediction": "scam", "expected_category": "banking_scam", "note": "Very short scam"},
    {"text": "Vela venuma? Data entry, part time. Monthly Rs 30,000. Registration fee Rs 999. http://tamil-jobs.tk", "expected_prediction": "scam", "expected_category": "fake_job", "note": "Tamil job scam"},
    {"text": "Courier company: Unga parcel la illegal items irukku! Fine pay pannanum. http://customs-alert.ga", "expected_prediction": "scam", "expected_category": "courier_scam", "note": "Tamil courier scam"},
    {"text": "Aadhaar card update pannikunga! Payment Rs 500. http://aadhaar-update.ml", "expected_prediction": "scam", "expected_category": "government_scam", "note": "Tamil government scam"},
]


def call_api(text: str) -> dict:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps({"text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"error": str(e)}


def flatten_samples() -> List[dict]:
    samples = []
    for cat, texts in SCAM_SAMPLES.items():
        for text in texts:
            samples.append({"text": text, "expected_prediction": "scam", "expected_category": cat})
    for text in LEGITIMATE_SAMPLES:
        samples.append({"text": text, "expected_prediction": "safe", "expected_category": "legitimate"})
    for edge in EDGE_CASES:
        samples.append({"text": edge["text"], "expected_prediction": edge["expected_prediction"],
                        "expected_category": edge["expected_category"], "note": edge.get("note", "")})
    return samples


def evaluate():
    samples = flatten_samples()
    results = []
    errors = []
    category_results = defaultdict(list)

    total_scam = sum(1 for s in samples if s["expected_prediction"] == "scam")
    total_safe = sum(1 for s in samples if s["expected_prediction"] == "safe")

    print("=" * 110)
    print("  SCAMSHIELD COMPREHENSIVE AI BENCHMARK")
    print(f"  API Endpoint: {API_URL}")
    print(f"  Total Samples: {len(samples)} (Scam: {total_scam}, Legitimate: {total_safe}, Edge: {len(EDGE_CASES)})")
    print(f"  Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 110)

    for i, sample in enumerate(samples, 1):
        text = sample["text"]
        expected_pred = sample["expected_prediction"]
        expected_cat = sample["expected_category"]
        note = sample.get("note", "")

        response = call_api(text)

        if "error" in response:
            errors.append((i, text[:80], response["error"]))
            print(f"  [{i:03d}] ERROR: {response['error']}")
            continue

        prediction = response.get("prediction", "unknown")
        confidence = response.get("confidence", 0)
        assessment_score = response.get("assessment_score", 0)
        refined_score = response.get("refined_assessment_score", 0)
        scam_category = response.get("scam_category", "")
        detected_indicators = response.get("detected_indicators", [])
        risk_level = response.get("risk_level", "")

        result = {
            "index": i,
            "text": text,
            "note": note,
            "expected_prediction": expected_pred,
            "expected_category": expected_cat,
            "prediction": prediction,
            "confidence": confidence,
            "assessment_score": assessment_score,
            "refined_assessment_score": refined_score,
            "scam_category": scam_category,
            "detected_indicators": detected_indicators,
            "risk_level": risk_level,
        }
        results.append(result)
        category_results[expected_cat].append(result)

        correct = prediction == expected_pred
        marker = "+" if correct else "!"
        cat_name = expected_cat[:22]
        note_str = f" [{note}]" if note else ""
        print(f"  [{i:03d}] {marker} pred={prediction:<5} conf={confidence:.3f} score={assessment_score:<4} "
              f"cat={cat_name:<22} [{correct}]{note_str}")

    print()
    print("=" * 110)
    print("  RESULTS SUMMARY")
    print("=" * 110)

    total = len(results)
    correct_total = sum(1 for r in results if r["prediction"] == r["expected_prediction"])
    misclassified = [r for r in results if r["prediction"] != r["expected_prediction"]]
    total_errors = len(errors)

    print(f"  Total Samples Tested:      {total}")
    print(f"  Correct Predictions:       {correct_total}")
    print(f"  Misclassified:             {len(misclassified)}")
    print(f"  API Errors:                {total_errors}")
    if total > 0:
        print(f"  Overall Accuracy:          {correct_total / total * 100:.2f}%")

    print()
    print("=" * 110)
    print("  PER-CATEGORY ACCURACY BREAKDOWN")
    print("=" * 110)
    print(f"  {'Category':<25} {'Total':>6} {'Correct':>8} {'Accuracy':>9}")
    print(f"  {'-'*25} {'-'*6} {'-'*8} {'-'*9}")

    category_metrics = {}
    for cat in sorted(category_results.keys()):
        cat_res = category_results[cat]
        total_cat = len(cat_res)
        correct_cat = sum(1 for r in cat_res if r["prediction"] == r["expected_prediction"])
        accuracy_cat = correct_cat / total_cat * 100 if total_cat > 0 else 0
        category_metrics[cat] = {"total": total_cat, "correct": correct_cat}
        print(f"  {cat:<25} {total_cat:>6} {correct_cat:>8} {accuracy_cat:>8.1f}%")

    print()
    print("=" * 110)
    print("  CONFUSION MATRIX")
    print("=" * 110)

    grand_tp = sum(1 for r in results if r["expected_prediction"] == "scam" and r["prediction"] == "scam")
    grand_fn = sum(1 for r in results if r["expected_prediction"] == "scam" and r["prediction"] == "safe")
    grand_fp = sum(1 for r in results if r["expected_prediction"] == "safe" and r["prediction"] == "scam")
    grand_tn = sum(1 for r in results if r["expected_prediction"] == "safe" and r["prediction"] == "safe")

    print(f"  {'':<20} {'Predicted Scam':>16} {'Predicted Safe':>16}")
    print(f"  {'-'*20} {'-'*16} {'-'*16}")
    print(f"  {'Actual Scam':<20} {grand_tp:>16} {grand_fn:>16}")
    print(f"  {'Actual Safe':<20} {grand_fp:>16} {grand_tn:>16}")

    precision = grand_tp / (grand_tp + grand_fp) if (grand_tp + grand_fp) > 0 else 0
    recall = grand_tp / (grand_tp + grand_fn) if (grand_tp + grand_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    specificity = grand_tn / (grand_tn + grand_fp) if (grand_tn + grand_fp) > 0 else 0
    fpr = grand_fp / (grand_fp + grand_tn) if (grand_fp + grand_tn) > 0 else 0

    print()
    print("=" * 110)
    print("  OVERALL METRICS")
    print("=" * 110)
    print(f"  Accuracy:           {correct_total / total * 100:.2f}%" if total > 0 else "  N/A")
    print(f"  Precision:          {precision:.4f}  ({precision * 100:.2f}%)")
    print(f"  Recall:             {recall:.4f}  ({recall * 100:.2f}%)")
    print(f"  F1 Score:           {f1:.4f}  ({f1 * 100:.2f}%)")
    print(f"  Specificity:        {specificity:.4f}  ({specificity * 100:.2f}%)")
    print(f"  False Positive Rate: {fpr:.4f}  ({fpr * 100:.2f}%)")

    print()
    print("=" * 110)
    print("  FALSE POSITIVES DETAILS")
    print("=" * 110)
    fps = [r for r in results if r["expected_prediction"] == "safe" and r["prediction"] == "scam"]
    if fps:
        for fp in fps:
            print(f"\n  --- False Positive ---")
            print(f"  Text:       {fp['text'][:90]}")
            print(f"  Confidence: {fp['confidence']:.4f}")
            print(f"  Category:   {fp['scam_category']}")
            print(f"  Score:      {fp['assessment_score']}")
            print(f"  Indicators: {fp['detected_indicators']}")
    else:
        print("  No false positives!")

    print()
    print("=" * 110)
    print("  FALSE NEGATIVES DETAILS")
    print("=" * 110)
    fns = [r for r in results if r["expected_prediction"] == "scam" and r["prediction"] == "safe"]
    if fns:
        for fn in fns:
            print(f"\n  --- False Negative ---")
            print(f"  Text:        {fn['text'][:90]}")
            print(f"  Expected:    {fn['expected_category']}")
            print(f"  Confidence:  {fn['confidence']:.4f}")
            print(f"  Refined:     {fn['refined_assessment_score']}")
            print(f"  Indicators:  {fn['detected_indicators']}")
    else:
        print("  No false negatives!")

    if errors:
        print()
        print("=" * 110)
        print(f"  API ERRORS ({len(errors)})")
        print("=" * 110)
        for idx, text, err in errors:
            print(f"  [{idx}] {text[:60]} -> {err}")

    print()
    print("=" * 110)
    print("  END OF BENCHMARK REPORT")
    print("=" * 110)

    print(json.dumps({
        "summary": {
            "total_tested": total,
            "correct": correct_total,
            "misclassified": len(misclassified),
            "errors": total_errors,
            "accuracy_pct": round(correct_total / total * 100, 2) if total > 0 else 0,
        },
        "metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "specificity": round(specificity, 4),
            "false_positive_rate": round(fpr, 4),
        },
        "confusion_matrix": {
            "true_positives": grand_tp,
            "false_negatives": grand_fn,
            "false_positives": grand_fp,
            "true_negatives": grand_tn,
        },
        "per_category": {cat: {"total": m["total"], "correct": m["correct"],
                                "accuracy_pct": round(m["correct"] / m["total"] * 100, 1)}
                         for cat, m in sorted(category_metrics.items())},
    }, indent=2))


if __name__ == "__main__":
    evaluate()
