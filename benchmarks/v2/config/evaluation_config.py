from typing import List, Dict, Any
from dataclasses import dataclass, field

DEFAULT_METRICS: List[str] = [
    "accuracy", "precision", "recall", "f1",
    "fpr", "fnr", "auc", "mcc", "balanced_accuracy"
]

SCAM_CATEGORIES: List[str] = [
    "UPI_FRAUD", "BANKING_FRAUD", "KYC_SCAM", "AADHAAR_SCAM", "PAN_SCAM",
    "FAKE_CUSTOMER_CARE", "COURIER_SCAM", "ELECTRICITY_BILL_SCAM", "QR_SCAM",
    "LOTTERY_SCAM", "INVESTMENT_SCAM", "CRYPTO_SCAM", "LOAN_SCAM", "JOB_SCAM",
    "ROMANCE_SCAM", "GOVERNMENT_IMPERSONATION", "DIGITAL_ARREST",
    "INCOME_TAX_SCAM", "TELECOM_SCAM"
]

LEGIT_CATEGORIES: List[str] = [
    "LEGITIMATE_BANKING", "LEGITIMATE_UPI", "LEGITIMATE_OTP",
    "LEGITIMATE_COURIER", "LEGITIMATE_GOVERNMENT", "LEGITIMATE_OTHER"
]

ALL_CATEGORIES: List[str] = SCAM_CATEGORIES + LEGIT_CATEGORIES

SEVERITY_WEIGHTS: Dict[str, int] = {
    "CRITICAL": 5,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1
}

MIN_SAMPLES_PER_CATEGORY: int = 100
DEFAULT_THRESHOLD: float = 0.5

MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "transformer": {
        "model_type": "transformer",
        "batch_size": 32,
        "max_length": 512,
        "threshold": 0.5,
        "device": "cuda"
    },
    "ensemble": {
        "model_type": "ensemble",
        "models": ["transformer", "fasttext", "lr"],
        "voting": "soft",
        "threshold": 0.5
    },
    "fasttext": {
        "model_type": "fasttext",
        "threshold": 0.5,
        "epochs": 50,
        "lr": 0.1
    },
    "lr": {
        "model_type": "logistic_regression",
        "threshold": 0.5,
        "max_iter": 1000,
        "C": 1.0
    }
}

DATA_PATHS: Dict[str, str] = {
    "raw": "data/raw",
    "processed": "data/processed",
    "synthetic": "data/synthetic",
    "cert_in": "data/sources/cert-in",
    "rbi": "data/sources/rbi",
    "ncpc": "data/sources/ncpc"
}

MODEL_PATHS: Dict[str, str] = {
    "transformer": "models/transformer",
    "fasttext": "models/fasttext",
    "ensemble": "models/ensemble",
    "lr": "models/logistic_regression"
}

REPORT_PATHS: Dict[str, str] = {
    "metrics": "reports/metrics",
    "curves": "reports/curves",
    "html": "reports/html",
    "json": "reports/json",
    "error_analysis": "reports/error_analysis",
    "comparison": "reports/comparison",
    "data_drift": "reports/data_drift"
}

@dataclass
class EvaluationConfig:
    metrics: List[str] = field(default_factory=lambda: DEFAULT_METRICS)
    threshold: float = DEFAULT_THRESHOLD
    min_samples_per_category: int = MIN_SAMPLES_PER_CATEGORY
    model_configs: Dict[str, Any] = field(default_factory=lambda: MODEL_CONFIGS)
    severity_weights: Dict[str, int] = field(default_factory=lambda: SEVERITY_WEIGHTS)
    categories: List[str] = field(default_factory=lambda: ALL_CATEGORIES)
    scam_categories: List[str] = field(default_factory=lambda: SCAM_CATEGORIES)
    legit_categories: List[str] = field(default_factory=lambda: LEGIT_CATEGORIES)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metrics": self.metrics,
            "threshold": self.threshold,
            "min_samples_per_category": self.min_samples_per_category,
            "categories": self.categories,
            "scam_categories": self.scam_categories,
            "legit_categories": self.legit_categories,
            "severity_weights": self.severity_weights,
            "model_configs": self.model_configs
        }
