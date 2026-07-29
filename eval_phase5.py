import urllib.request, json, time, random

API = 'http://localhost:8001/analyze/text'

CATEGORIES = {
    'banking_scam': [
        'Your {bank} account has been {action}. Call {phone} immediately to {reason}.',
        'ALERT: {bank} detected {issue} on your account. Click {url} to verify within 24 hours or account will be suspended.',
        'Dear customer, your {bank} debit card has been {status} due to suspicious activity. Call {phone} to reactivate.',
        'SBI Alert: Your account has been credited with {amount} from unknown source. Call {phone} for refund process.',
        'Your ICICI netbanking password will expire in 24 hours. Update at {url} to continue using services.',
    ],
    'upi_scam': [
        'Your Google Pay UPI PIN has been reset. Click {url} to set new pin immediately.',
        'UPI Payment of {amount} initiated to unknown beneficiary. Click {url} to BLOCK or call {phone}.',
        'PhonePe: Your UPI ID has been linked to a new device. Verify at {url} if not you.',
        'Your UPI transaction of {amount} failed. Refund available at {url}.',
        'UPI address expired. Update your UPI ID at {url} to continue receiving payments.',
    ],
    'fake_job': [
        'Congratulations! You are selected for {company} work-from-home job. Earn \u20b9{salary}/month. Pay \u20b9{fee} registration fee.',
        'Urgent hiring at {company}! No interview required. Submit \u20b9{fee} for joining kit. Limited positions.',
        'Part-time job: Data entry from home. Earn \u20b9{salary}/day. Call {phone} for registration.',
        '{company} is hiring freelancers! Earn \u20b9{salary}/project. Registration fee \u20b9{fee} refundable after first project.',
        'Work from home job with {company}. Daily payout \u20b9{salary}. Processing fee \u20b9{fee}. Limited slots!',
    ],
    'courier_scam': [
        'Your {courier} package #{tracking} is held at customs. Pay \u20b9{fee} clearance fee to release.',
        '{courier} delivery failed for order #{tracking}. Reschedule delivery at {url} or pay \u20b9{fee} redelivery charge.',
        'Your international shipment #{tracking} from {country} requires customs clearance. Call {phone} immediately.',
        '{courier}: Your package contains prohibited items. Call {phone} to avoid legal action.',
        'DHL tracking update: Package #{tracking} on hold. Confirm address at {url} within 24 hours.',
    ],
    'otp_scam': [
        'Your Aadhaar OTP is {otp}. Never share this OTP. KYC update required at {url}.',
        'SIM card blocked due to KYC not updated. Click {url} to update KYC and restore service.',
        'Your ATM card has been blocked. Call {phone} to unblock immediately.',
        '{bank} KYC update mandatory. Click {url} to update or account will be frozen.',
        'Your mobile number will be disconnected within 24 hours. Update KYC at {url}.',
    ],
    'investment_scam': [
        'Get {returns}% guaranteed returns in {days} days! Bitcoin investment. Minimum \u20b9{min_invest}. Join now!',
        'Stock market tips by experts. Earn \u20b9{profit} per month. Join our {group} group. Limited seats.',
        'Mutual fund bonus scheme! Invest \u20b9{invest} get \u20b9{return_amt} after 1 year. Government approved.',
        'Crypto trading signals. {accuracy}% accuracy. Last 10 trades all profitable. Join now!',
        'Forex trading made easy. Earn {returns}% monthly. Automated trading. No experience needed.',
    ],
    'romance_scam': [
        'Hello dear, I am {name}, US Army captain serving in {location}. I need your help to transfer ${amount}.',
        "Hi beautiful, I saw your profile. I'm a oil rig engineer from {country}. Let's chat on WhatsApp.",
        'I am {name} from {country}. I inherited ${amount} but need your help to claim it. Reward 30% for you.',
        'Hello my love, I will visit you soon but my luggage is stuck at customs. Can you send \u20b9{fee} to release it?',
        'Dear, I am sick and need ${amount} for surgery. You are my only hope. Please help.',
    ],
    'government_scam': [
        'Your PAN card has been used in illegal {activity}. Call Income Tax Dept at {phone} immediately to avoid arrest.',
        'Income Tax refund of \u20b9{amount} is pending. Click {url} to claim your refund.',
        'Your Aadhaar-Electricity bill linking incomplete. Disconnection in 24 hours. Click {url} to link now.',
        'Electricity board: Your connection will be DISCONNECTED due to non-payment. Pay \u20b9{amount} at {url}.',
        'Ration card update required. Click {url} to update or your benefits will be stopped.',
    ],
    'lottery_scam': [
        'Congratulations! You won \u20b9{amount} in {lottery} lottery! Call {phone} to claim your prize.',
        'You have been selected as the {prize} winner in our mega draw. Transfer \u20b9{fee} processing fee to release prize.',
        'Merry Christmas! You won a {prize} worth \u20b9{amount}. Claim at {url}.',
        'Google Lucky Draw: You won {prize}! Claim your prize by paying \u20b9{fee} handling charges.',
        'Amazon Bumper Draw: You won {prize} worth \u20b9{amount}! Call {phone} immediately to claim.',
    ],
    'phishing_scam': [
        'Your Apple ID has been locked. Unlock at {url} to continue using your account.',
        'Netflix: Your subscription has been suspended. Update payment at {url} within 24 hours.',
        'Google Alert: Unusual sign-in detected from {location}. Verify account at {url}.',
        'Your Facebook account will be permanently deleted. Appeal at {url}.',
        'Microsoft: Your email storage is full. Upgrade at {url} to continue receiving emails.',
    ],
}

def expand_template(template):
    subs = {
        'bank': random.choice(['HDFC Bank', 'ICICI Bank', 'SBI', 'Axis Bank', 'Kotak Mahindra', 'Yes Bank', 'PNB', 'Canara Bank']),
        'action': random.choice(['blocked', 'locked', 'compromised', 'suspended', 'hacked', 'restricted']),
        'phone': random.choice(['1800-123-4567', '022-6789-1234', '011-2345-6789']),
        'reason': random.choice(['restore access', 'secure your account', 'verify your identity', 'prevent fraud']),
        'issue': random.choice(['unusual login activity', 'multiple failed attempts', 'a new device login', 'suspicious transaction']),
        'url': random.choice(['http://bank-secure-update.com', 'http://verify-account-now.com', 'http://secure-banking-verify.com', 'http://account-alert-247.com']),
        'amount': random.choice(['50,000', '1,00,000', '25,000', '10,000', '5,00,000']),
        'status': random.choice(['blocked', 'suspended', 'temporarily locked']),
        'fee': random.choice(['999', '1999', '499', '2499', '500']),
        'courier': random.choice(['FedEx', 'DHL', 'UPS', 'Blue Dart', 'DTDC']),
        'tracking': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=12)),
        'country': random.choice(['USA', 'UK', 'Canada', 'Australia', 'Germany', 'Dubai']),
        'salary': random.choice(['25000', '50000', '100000', '15000', '35000']),
        'company': random.choice(['Amazon', 'Google', 'Microsoft', 'Flipkart', 'Swiggy', 'Zomato', 'Myntra']),
        'otp': ''.join(random.choices('0123456789', k=6)),
        'returns': str(random.choice([10, 20, 50, 100, 500, 1000])),
        'days': str(random.choice([1, 3, 7, 15, 30])),
        'min_invest': random.choice(['1000', '5000', '10000', '25000']),
        'profit': random.choice(['25000', '50000', '100000']),
        'group': random.choice(['WhatsApp', 'Telegram', 'VIP', 'Premium']),
        'invest': random.choice(['10000', '25000', '50000', '100000']),
        'return_amt': random.choice(['100000', '250000', '500000']),
        'accuracy': str(random.choice([90, 95, 97, 99])),
        'name': random.choice(['John Smith', 'David Wilson', 'James Anderson', 'Robert Taylor', 'Michael Brown']),
        'location': random.choice(['Syria', 'Afghanistan', 'Iraq', 'Yemen', 'Kuwait']),
        'activity': random.choice(['transactions', 'money laundering', 'tax evasion', 'suspicious activities']),
        'lottery': random.choice(['Mega Millions', 'Power Ball', 'Lucky Draw', 'Christmas Special']),
        'prize': random.choice(['iPhone 15 Pro Max', 'Brand New Car', '\u20b950 Lakh Cash', 'Dubai Trip', 'Gold Bar']),
    }
    result = template
    for k, v in subs.items():
        result = result.replace('{' + k + '}', str(v))
    return result

# Generate samples
samples = []
for cat, templates in CATEGORIES.items():
    for _ in range(50):
        tmpl = random.choice(templates)
        text = expand_template(tmpl)
        samples.append({'text': text, 'expected': cat})

# Add legitimate samples
legitimate = [
    ('legitimate', 'Your Flipkart order #OD123456789 has been shipped and will be delivered by Jan 20. Track your order on our app.'),
    ('legitimate', 'Netflix: Your monthly subscription of \u20b9199 will be charged on 15th February. Manage your account settings at netflix.com.'),
    ('legitimate', 'Dear customer, your HDFC Bank statement for December 2025 is ready. Download from our netbanking portal.'),
    ('legitimate', 'Zomato: Your order from Dominos is being prepared and will be delivered in 30 minutes.'),
    ('legitimate', 'ICICI Bank: Your credit card bill of \u20b912,500 is due on 31st Jan. Pay on time to avoid late fees.'),
    ('legitimate', 'Swiggy: Order delivered! Rate your experience and earn Swiggy coins.'),
    ('legitimate', 'Your appointment with Dr. Sharma at Apollo Clinic is confirmed for 15th Jan at 10:00 AM.'),
    ('legitimate', 'Airtel: Your plan of \u20b9249 will expire on 20th Jan. Recharge now to continue uninterrupted service.'),
    ('legitimate', 'Google: Your verification code is 839201. This code expires in 10 minutes.'),
    ('legitimate', 'WhatsApp: Your verification code for WhatsApp is 452891. Do not share this code.'),
    ('legitimate', 'Paytm: \u20b9250 received from Rahul Sharma. UPI Ref: 123456789012.'),
    ('legitimate', 'Your IRCTC ticket #1234567890 for New Delhi Rajdhani is confirmed. Boarding at platform 3.'),
    ('legitimate', 'Amazon: Your return for product #XYZ123 has been accepted. Refund will be processed in 5-7 days.'),
    ('legitimate', 'Uber: Your trip to Indira Gandhi Airport is complete. Total fare: \u20b9450. Payment via Uber wallet.'),
    ('legitimate', 'SBI: Your account XX1234 has been credited with \u20b915,000 via NEFT from HDFC Bank.'),
    ('legitimate', 'PhonePe: Monthly mobile recharge of \u20b9249 successful for 9876543210.'),
    ('legitimate', 'LinkedIn: John Doe viewed your profile. See who viewed your profile on LinkedIn.'),
    ('legitimate', 'Your COVID-19 vaccination appointment is scheduled at Apollo Hospital on 20th Jan at 2:00 PM.'),
    ('legitimate', 'Razorpay: Payment of \u20b91,500 received from Acme Corp. Invoice #INV-2024-001.'),
    ('legitimate', 'Zerodha: Your order to buy 10 shares of RELIANCE at \u20b92,500 has been executed.'),
    ('legitimate', 'Your Aadhaar OTP for eKYC is 384729. Valid for 10 minutes.'),
    ('legitimate', 'Makemytrip: Your flight booking #MMT123456 from Mumbai to Delhi is confirmed. Departure: 6:00 AM.'),
    ('legitimate', 'Your account password was changed successfully. If not you, reset immediately.'),
    ('legitimate', 'Google Pay: \u20b91,200 sent to Priya Singh. UPI Ref: 987654321098.'),
    ('legitimate', 'Your Netflix plan has been upgraded to Premium. Enjoy 4K streaming on 4 devices.'),
]
for cat, text in legitimate:
    samples.append({'text': text, 'expected': cat})

while len(samples) < 510:
    s = random.choice(legitimate)
    samples.append({'text': s[1], 'expected': s[0]})

random.shuffle(samples)
print(f'Generated {len(samples)} test samples')

# Test each sample
results = []
for i, sample in enumerate(samples):
    data = json.dumps({'text': sample['text']}).encode()
    req = urllib.request.Request(API, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        r = urllib.request.urlopen(req, timeout=10)
        resp = json.loads(r.read())
        prediction = resp.get('prediction', 'unknown')
        confidence = resp.get('confidence', 0)
        cat_pred = resp.get('scam_category', 'unknown')
        risk = resp.get('risk_level', 'unknown')
        score = resp.get('assessment_score', 0)
        expected_is_scam = sample['expected'] != 'legitimate'
        predicted_is_scam = prediction == 'scam'
        correct = expected_is_scam == predicted_is_scam
        results.append({'index': i+1, 'expected': sample['expected'], 'prediction': prediction, 'confidence': confidence, 'category': cat_pred, 'risk': risk, 'score': score, 'correct': correct})
    except Exception as e:
        results.append({'index': i+1, 'expected': sample['expected'], 'error': str(e)[:120], 'correct': False})

    if (i+1) % 50 == 0:
        print(f'Progress: {i+1}/{len(samples)} tested')

# Calculate metrics
total = len(results)
correct = sum(1 for r in results if r.get('correct'))
errors = sum(1 for r in results if 'error' in r)
scam_correct = sum(1 for r in results if r.get('correct') and r['expected'] != 'legitimate' and r.get('prediction') == 'scam')
scam_total = sum(1 for r in results if r['expected'] != 'legitimate')
safe_correct = sum(1 for r in results if r.get('correct') and r['expected'] == 'legitimate' and r.get('prediction') == 'safe')
safe_total = sum(1 for r in results if r['expected'] == 'legitimate')
fp = sum(1 for r in results if r['expected'] == 'legitimate' and r.get('prediction') == 'scam')
fn = sum(1 for r in results if r['expected'] != 'legitimate' and r.get('prediction') == 'safe')

tp = scam_correct
tn = safe_correct
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
accuracy = correct / total if total > 0 else 0
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

print()
print('=' * 60)
print(f'BENCHMARK RESULTS: {total} samples')
print('=' * 60)
print(f'CORRECT: {correct}/{total} ({accuracy*100:.2f}%)')
print(f'ERRORS: {errors}')
print()
print('CONFUSION MATRIX:')
print('                  Predicted Scam    Predicted Safe')
print(f'Actual Scam       TP={tp:<5}        FN={fn:<5}')
print(f'Actual Safe       FP={fp:<5}        TN={tn:<5}')
print()
print('METRICS:')
print(f'  Accuracy:  {accuracy*100:.2f}%')
print(f'  Precision: {precision*100:.2f}%')
print(f'  Recall:    {recall*100:.2f}%')
print(f'  F1 Score:  {f1*100:.2f}%')
print(f'  Specificity: {specificity*100:.2f}%')
print(f'  FPR: {fpr*100:.2f}%')
print(f'  FNR: {fnr*100:.2f}%')

# Per-category breakdown
print()
print('PER-CATEGORY BREAKDOWN:')
cat_stats = {}
for r in results:
    cat = r['expected']
    if cat not in cat_stats:
        cat_stats[cat] = {'total': 0, 'correct': 0}
    cat_stats[cat]['total'] += 1
    if r.get('correct'):
        cat_stats[cat]['correct'] += 1

for cat, data in sorted(cat_stats.items()):
    acc = data['correct'] / data['total'] * 100 if data['total'] > 0 else 0
    print(f'  {cat:25s}: {data["correct"]}/{data["total"]:3d} ({acc:5.1f}%)')

# Wrong predictions detail
print()
print('MISCLASSIFICATION DETAILS (first 30):')
wrong = [r for r in results if not r.get('correct') and 'error' not in r]
for w in wrong[:30]:
    print(f'  #{w["index"]}: expected={w["expected"]}, predicted={w["prediction"]}, confidence={w.get("confidence",0):.4f}, score={w.get("score",0)}')

print()
print(f'Total misclassifications: {len(wrong)}')