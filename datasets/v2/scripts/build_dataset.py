"""
ScamShield v2 Dataset Builder

Assembles raw data from multiple sources into the annotated dataset format.
Usage: python datasets/v2/scripts/build_dataset.py
"""
import csv
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

# Add backend to path for text utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from utils.text import clean_text, extract_entities

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw")
ANNOTATED_DIR = os.path.join(BASE_DIR, "annotated")
BENCHMARK_DIR = os.path.join(BASE_DIR, "benchmark")

VALID_CATEGORIES = {
    "UPI_FRAUD", "BANKING_FRAUD", "KYC_SCAM", "AADHAAR_SCAM", "PAN_SCAM",
    "FAKE_CUSTOMER_CARE", "COURIER_SCAM", "ELECTRICITY_BILL_SCAM", "QR_SCAM",
    "LOTTERY_SCAM", "INVESTMENT_SCAM", "CRYPTO_SCAM", "LOAN_SCAM", "JOB_SCAM",
    "ROMANCE_SCAM", "GOVERNMENT_IMPERSONATION", "DIGITAL_ARREST",
    "INCOME_TAX_SCAM", "TELECOM_SCAM",
    "LEGITIMATE_BANKING", "LEGITIMATE_UPI", "LEGITIMATE_OTP",
    "LEGITIMATE_COURIER", "LEGITIMATE_GOVERNMENT", "LEGITIMATE_OTHER",
}

CATEGORY_IS_SCAM = {
    "UPI_FRAUD": True, "BANKING_FRAUD": True, "KYC_SCAM": True,
    "AADHAAR_SCAM": True, "PAN_SCAM": True, "FAKE_CUSTOMER_CARE": True,
    "COURIER_SCAM": True, "ELECTRICITY_BILL_SCAM": True, "QR_SCAM": True,
    "LOTTERY_SCAM": True, "INVESTMENT_SCAM": True, "CRYPTO_SCAM": True,
    "LOAN_SCAM": True, "JOB_SCAM": True, "ROMANCE_SCAM": True,
    "GOVERNMENT_IMPERSONATION": True, "DIGITAL_ARREST": True,
    "INCOME_TAX_SCAM": True, "TELECOM_SCAM": True,
    "LEGITIMATE_BANKING": False, "LEGITIMATE_UPI": False,
    "LEGITIMATE_OTP": False, "LEGITIMATE_COURIER": False,
    "LEGITIMATE_GOVERNMENT": False, "LEGITIMATE_OTHER": False,
}

CATEGORY_RISK_MAP = {
    "UPI_FRAUD": "CRITICAL", "BANKING_FRAUD": "CRITICAL", "KYC_SCAM": "HIGH",
    "AADHAAR_SCAM": "HIGH", "PAN_SCAM": "HIGH", "FAKE_CUSTOMER_CARE": "MEDIUM",
    "COURIER_SCAM": "HIGH", "ELECTRICITY_BILL_SCAM": "HIGH", "QR_SCAM": "HIGH",
    "LOTTERY_SCAM": "MEDIUM", "INVESTMENT_SCAM": "HIGH", "CRYPTO_SCAM": "HIGH",
    "LOAN_SCAM": "MEDIUM", "JOB_SCAM": "MEDIUM", "ROMANCE_SCAM": "HIGH",
    "GOVERNMENT_IMPERSONATION": "HIGH", "DIGITAL_ARREST": "CRITICAL",
    "INCOME_TAX_SCAM": "CRITICAL", "TELECOM_SCAM": "HIGH",
    "LEGITIMATE_BANKING": "NONE", "LEGITIMATE_UPI": "NONE",
    "LEGITIMATE_OTP": "NONE", "LEGITIMATE_COURIER": "NONE",
    "LEGITIMATE_GOVERNMENT": "NONE", "LEGITIMATE_OTHER": "NONE",
}

CATEGORY_GROUND_TRUTH = {
    cat: "scam" if is_scam else "legitimate"
    for cat, is_scam in CATEGORY_IS_SCAM.items()
}

VERSION = "2.0.0-alpha"

_BANK_NAMES = [
    "sbi", "state bank", "hdfc", "icici", "axis", "pnb", "kotak",
    "yes bank", "indusind", "idbi", "canara", "union bank", "bank of baroda",
    "bob", "sbi", "rbi", "reserve bank", "sebi",
]

_AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
_PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
_PHONE_RE = re.compile(r"(?:\+?91[\s-]?)?\d{10}\b")
_URL_RE = re.compile(r"https?://(?:[-\w.]|%[\da-fA-F]{2})+(?:/[^\s]*)?", re.IGNORECASE)
_UPI_RE = re.compile(r"[\w.-]+@[\w.-]+", re.IGNORECASE)


def _detect_banks(text_lower: str) -> List[str]:
    return [b for b in _BANK_NAMES if b in text_lower]


def _extract_entities_text(text: str) -> Dict[str, List[str]]:
    text_lower = text.lower()
    return {
        "urls": [m.group(0) for m in _URL_RE.finditer(text)],
        "phones": [m.group(0) for m in _PHONE_RE.finditer(text)],
        "upi_ids": [m.group(0) for m in _UPI_RE.finditer(text) if m.group(0).split("@")[-1].isalpha()],
        "banks": _detect_banks(text_lower),
        "emails": [],
        "aadhaar": [m.group(0) for m in _AADHAAR_RE.finditer(text)],
        "pan": [m.group(0) for m in _PAN_RE.finditer(text)],
    }


def create_sample(
    text: str,
    category: str,
    source: str = "synthetic",
    annotation_notes: str = "",
    language: str = "en",
) -> Dict:
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category: {category}")

    cat_samples = {"UPI_FRAUD": 0, "BANKING_FRAUD": 0, "KYC_SCAM": 0}
    counter = _get_category_counter(category)

    entities = _extract_entities_text(text)
    text_clean = clean_text(text)

    return {
        "id": f"{category}_{counter:04d}",
        "text": text,
        "text_clean": text_clean,
        "language": language,
        "category": category,
        "is_scam": CATEGORY_IS_SCAM[category],
        "risk_level": CATEGORY_RISK_MAP[category],
        "extracted_entities": entities,
        "ground_truth_label": CATEGORY_GROUND_TRUTH[category],
        "source": source,
        "annotation_notes": annotation_notes,
        "annotator_id": "",
        "version": VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


_category_counters: Dict[str, int] = {}


def _get_category_counter(category: str) -> int:
    _category_counters[category] = _category_counters.get(category, 0) + 1
    return _category_counters[category]


def save_dataset(samples: List[Dict], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(samples)} samples to {output_path}")
    return output_path


def export_csv(samples: List[Dict], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not samples:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("id,text,category,is_scam,risk_level,ground_truth_label,language,source\n")
        return output_path

    fields = ["id", "text", "category", "is_scam", "risk_level",
              "ground_truth_label", "language", "source"]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for s in samples:
            writer.writerow({k: s.get(k, "") for k in fields})
    print(f"Exported {len(samples)} samples to CSV: {output_path}")
    return output_path


def get_dataset_stats(samples: List[Dict]) -> Dict:
    total = len(samples)
    if total == 0:
        return {"total": 0, "categories": {}}

    cats = Counter(s["category"] for s in samples)
    langs = Counter(s.get("language", "en") for s in samples)
    sources = Counter(s.get("source", "unknown") for s in samples)
    scam_count = sum(1 for s in samples if s["is_scam"])
    legit_count = total - scam_count

    return {
        "total": total,
        "scam": scam_count,
        "legitimate": legit_count,
        "scam_pct": round(scam_count / total * 100, 1) if total else 0,
        "categories": dict(cats.most_common()),
        "languages": dict(langs.most_common()),
        "sources": dict(sources.most_common()),
        "categories_with_shortfall": [
            {"category": cat, "count": count}
            for cat, count in cats.most_common()
            if count < 100
        ],
    }


def build_benchmark_from_dataset(
    samples: List[Dict],
    samples_per_category: int = 20,
    random_seed: int = 42,
) -> List[Dict]:
    import random
    random.seed(random_seed)

    by_category: Dict[str, List[Dict]] = defaultdict(list)
    for s in samples:
        by_category[s["category"]].append(s)

    benchmark = []
    for cat, cat_samples in by_category.items():
        selected = random.sample(cat_samples, min(samples_per_category, len(cat_samples)))
        for s in selected:
            benchmark.append({
                "id": s["id"],
                "text": s["text"],
                "expected_prediction": "scam" if s["is_scam"] else "safe",
                "expected_category": s["category"],
                "expected_risk_level": s["risk_level"],
                "difficulty": "medium",
                "language": s.get("language", "en"),
                "source_type": "sms",
                "ground_truth_reason": s.get("annotation_notes", ""),
            })

    return benchmark


def split_dataset(
    samples: List[Dict],
    train_ratio: float = 0.7,
    test_ratio: float = 0.15,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Stratified split preserving category distribution."""
    import random
    random.seed(seed)

    assert abs(train_ratio + test_ratio + val_ratio - 1.0) < 0.001

    by_category: Dict[str, List[Dict]] = defaultdict(list)
    for s in samples:
        by_category[s["category"]].append(s)

    train, test, val = [], [], []
    for cat, cat_samples in by_category.items():
        random.shuffle(cat_samples)
        n = len(cat_samples)
        n_train = int(n * train_ratio)
        n_test = int(n * test_ratio)
        train.extend(cat_samples[:n_train])
        test.extend(cat_samples[n_train:n_train + n_test])
        val.extend(cat_samples[n_train + n_test:])

    return train, test, val


if __name__ == "__main__":
    print("ScamShield v2 Dataset Builder")
    print("=" * 50)
    print("Usage:")
    print("  from build_dataset import create_sample, save_dataset, get_dataset_stats")
    print()
    print("Example:")
    print("  samples = []")
    print("  samples.append(create_sample(")
    print("      text='Your SBI account blocked. Update KYC: [URL]',")
    print("      category='KYC_SCAM',")
    print("      source='synthetic'")
    print("  ))")
    print("  save_dataset(samples, 'datasets/v2/annotated/v2.0.0-alpha/dataset.json')")