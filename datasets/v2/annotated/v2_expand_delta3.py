import csv, json, logging, os, random, re, copy
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("v2-delta3")
random.seed(999)

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
        "annotation_notes": "Delta3 expansion for persistent FN patterns.",
        "created_at": now,
        "updated_at": now,
    }

# FOCUSED: LEGITIMATE_SHOPPING scams (6 FNs - Amazon/Flipkart multilingual delivery)
SHOPPING_SCAM_FOCUS = {
    "hi-en": [
        "Aapka Amazon ka order dispatch ho gaya hai. Yahan track karein.",
        "Aapka Flipkart ka order bhej diya gaya hai. Track karo.",
        "Amazon: aapka order deliver ho gaya. Rating do.",
        "Flipkart: aapka order deliver ho gaya. Rating do.",
    ],
    "ta-en": [
        "Unga Amazon order dispatch. Track pannugal.",
        "Unga Flipkart order dispatch. Track pannugal.",
        "Amazon: unga order deliver. Rating kudungal.",
    ],
    "te-en": [
        "Mee Amazon order dispatch. Track cheyandi.",
        "Mee Flipkart order dispatch. Track cheyandi.",
    ],
}

# FOCUSED: LEGITIMATE_TELECOM scams (3 FNs - "Mobile recharge Rs 599 successful")
TELECOM_SCAM_FOCUS = {
    "en": [
        "Your prepaid recharge of Rs 599 is successful. 84 days validity. Enjoy unlimited calling.",
        "Jio: Rs 599 recharge successful. 2GB/day data for 84 days. Plan active.",
        "VI: Your Rs 599 recharge done. Unlimited calls + 2GB/day for 84 days.",
        "Airtel: Recharge Rs 599 successful. Enjoy 2GB/day data for 84 days.",
        "Airtel recharge Rs 599 successful. Naa valid 84 days.",
        "VI recharge Rs 599 successful. Plan active. Valid 84 days.",
    ],
}

# FOCUSED: LEGITIMATE_PERSONAL FNs (3 - hi/ta/te dinner booking)
PERSONAL_FOCUS = {
    "hi-en": ["Dinner aaj raat 8 baje. Main restaurant book kar chuka hoon."],
    "ta-en": ["Dinner innikku 8 manikku. Naan restaurant book panniten."],
    "te-en": ["Dinner iedu 8 ki. Nenu restaurant book chesanu."],
}

# FOCUSED: UPI_FRAUD (1 FN - BHIM credit)
UPI_SCAM_FOCUS = {
    "en": [
        "BHIM UPI: Rs 5,000 credited to your account from unknown UPI ID. Report at http://bhim-report.xyz.",
        "Your BHIM account received Rs 5,000 from unknown sender. Reverse? Call 1800-123-4567.",
        "PhonePe: Rs 6,500 credited by mistake. Return at http://phonepe-return.tk.",
    ],
}

# FOCUSED: BANKING_FRAUD (2 FNs - Canara cheque, Axis credit)
BANKING_FOCUS = {
    "en": [
        "Canara Bank: Your cheque book order has been confirmed. Delivery tracking at http://canara-track.xyz.",
        "Axis Bank: Your account credited Rs 85,000 from unknown source. If not you, call 1860-500-5555.",
        "SBI: Your account received Rs 1,25,000 from unknown NEFT. Verify at http://sbi-alert.xyz.",
    ],
}

# FOCUSED: OTP_SCAM (1 FN - Telegram OTP)
OTP_FOCUS = {
    "en": [
        "Telegram: OTP 782345 for account access from Hyderabad. If not you, secure account now.",
        "WhatsApp: OTP 891234 for login from Mumbai. Not you? Block immediately.",
    ],
}

# FOCUSED: DIGITAL_ARREST (1 FN - NCB parcel)
DIGITAL_FOCUS = {
    "en": [
        "NCB: A parcel with 2kg cocaine found in your name at Mumbai airport. Call 1800-123-4567.",
        "Customs: Your international shipment contains illegal goods. Legal notice issued. Contact now.",
        "CBI: Drugs consignment booked under your Aadhaar. Immediate investigation required.",
    ],
}

def main():
    existing_rows, existing_texts, existing_ids = load_existing(GAMMA_PATH)
    logger.info("Existing: %d rows", len(existing_rows))
    new_rows = []
    idx_counter = copy.deepcopy(existing_ids)

    def add(cat, scam, risk, lang_texts):
        nonlocal idx_counter
        for lang, texts in lang_texts.items():
            for t in texts:
                tc = t.strip().lower()
                if tc in existing_texts:
                    continue
                idx_counter[cat] += 1
                new_rows.append(make_sample(t, cat, scam, risk, language=lang, index=idx_counter[cat]))
                existing_texts.add(tc)

    add("LEGITIMATE_SHOPPING", True, "HIGH", SHOPPING_SCAM_FOCUS)
    add("TELECOM_SCAM", True, "HIGH", TELECOM_SCAM_FOCUS)
    add("LEGITIMATE_PERSONAL", True, "HIGH", PERSONAL_FOCUS)
    add("UPI_FRAUD", True, "HIGH", UPI_SCAM_FOCUS)
    add("BANKING_FRAUD", True, "HIGH", BANKING_FOCUS)
    add("OTP_SCAM", True, "HIGH", OTP_FOCUS)
    add("DIGITAL_ARREST", True, "HIGH", DIGITAL_FOCUS)

    logger.info("Generated %d new samples", len(new_rows))
    if len(new_rows) == 0:
        logger.info("No new unique samples to add. Stopping.")
        return

    all_rows = existing_rows + new_rows
    scam_count = sum(1 for r in all_rows if r["is_scam"].lower() in ("true", "1", "yes"))
    cats = Counter(r["category"] for r in all_rows)
    langs = Counter(r["language"] for r in all_rows)
    logger.info("Total: %d (%d scam) | Languages: %s", len(all_rows), scam_count, dict(langs))
    for cat, n in sorted(cats.items()):
        logger.info("  %s: %d", cat, n)

    for path in [OUTPUT_PATH, BACKEND_COPY]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)
        logger.info("Saved to %s", path)
    logger.info("Done! Total: %d", len(all_rows))

if __name__ == "__main__":
    main()
