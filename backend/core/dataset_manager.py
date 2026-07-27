import csv
import hashlib
import json
import os
import random
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

DATASET_REGISTRY: Dict[str, str] = {}


def compute_hash(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_dataset(
    filepath: str,
    label_col: str = "label",
    text_col: str = "text",
    category_col: Optional[str] = "category",
) -> Tuple[List[str], List[int], List[Optional[str]], Dict[str, Any]]:
    texts: List[str] = []
    labels: List[int] = []
    categories: List[Optional[str]] = []
    stats: Dict[str, Any] = {}

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        texts.append(row[text_col])
        labels.append(1 if row[label_col].strip().lower() == "scam" else 0)
        categories.append(row.get(category_col) if category_col else None)

    label_counts = Counter(labels)
    stats = {
        "total": len(texts),
        "scam": label_counts.get(1, 0),
        "safe": label_counts.get(0, 0),
        "scam_ratio": round(label_counts.get(1, 0) / max(len(texts), 1), 4),
        "filepath": filepath,
        "file_hash": compute_hash(filepath),
    }

    if any(categories):
        cat_counts = Counter(c for c in categories if c)
        stats["categories"] = dict(cat_counts.most_common())

    return texts, labels, categories, stats


def train_test_split(
    texts: List[str],
    labels: List[int],
    categories: Optional[List[Optional[str]]] = None,
    test_ratio: float = 0.2,
    stratify: bool = True,
    random_seed: int = 42,
) -> Dict[str, Any]:
    from sklearn.model_selection import train_test_split as sk_split

    if stratify:
        stratify_labels = labels
    else:
        stratify_labels = None

    train_idx, test_idx = sk_split(
        list(range(len(texts))),
        test_size=test_ratio,
        random_state=random_seed,
        stratify=stratify_labels,
    )

    result = {
        "train": {
            "indices": train_idx.tolist() if hasattr(train_idx, "tolist") else list(train_idx),
            "texts": [texts[i] for i in train_idx],
            "labels": [labels[i] for i in train_idx],
            "count": len(train_idx),
            "scam": sum(1 for i in train_idx if labels[i] == 1),
            "safe": sum(1 for i in train_idx if labels[i] == 0),
        },
        "test": {
            "indices": test_idx.tolist() if hasattr(test_idx, "tolist") else list(test_idx),
            "texts": [texts[i] for i in test_idx],
            "labels": [labels[i] for i in test_idx],
            "count": len(test_idx),
            "scam": sum(1 for i in test_idx if labels[i] == 1),
            "safe": sum(1 for i in test_idx if labels[i] == 0),
        },
        "test_ratio": test_ratio,
        "random_seed": random_seed,
    }

    if categories:
        result["train"]["categories"] = [categories[i] for i in train_idx]
        result["test"]["categories"] = [categories[i] for i in test_idx]

    return result


def cross_validation_splits(
    texts: List[str],
    labels: List[int],
    n_splits: int = 5,
    random_seed: int = 42,
) -> List[Dict[str, Any]]:
    from sklearn.model_selection import StratifiedKFold

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_seed)
    splits = []

    for fold, (train_idx, test_idx) in enumerate(skf.split(texts, labels)):
        splits.append({
            "fold": fold + 1,
            "train_indices": train_idx.tolist(),
            "test_indices": test_idx.tolist(),
            "train_count": len(train_idx),
            "test_count": len(test_idx),
            "train_scam": sum(1 for i in train_idx if labels[i] == 1),
            "train_safe": sum(1 for i in train_idx if labels[i] == 0),
            "test_scam": sum(1 for i in test_idx if labels[i] == 1),
            "test_safe": sum(1 for i in test_idx if labels[i] == 0),
        })

    return splits


def evaluate_dataset_balance(labels: List[int]) -> Dict[str, Any]:
    total = len(labels)
    scam = sum(labels)
    safe = total - scam
    scam_ratio = scam / max(total, 1)

    warnings = []
    if scam_ratio < 0.15:
        warnings.append("Low scam ratio may cause model to predict safe too often")
    elif scam_ratio > 0.85:
        warnings.append("High scam ratio may cause model to predict scam too often")
    if safe < 50:
        warnings.append("Very few safe samples — FPR estimates will be unreliable")
    if scam < 50:
        warnings.append("Very few scam samples — recall estimates will be unreliable")

    return {
        "total": total,
        "scam": scam,
        "safe": safe,
        "scam_ratio": round(scam_ratio, 4),
        "safe_ratio": round(1.0 - scam_ratio, 4),
        "balance": "skewed" if scam_ratio < 0.2 or scam_ratio > 0.8 else "balanced",
        "warnings": warnings,
    }


def save_manifest(
    dataset_path: str,
    version: str,
    stats: Dict[str, Any],
    output_dir: str = "data",
) -> str:
    manifest = {
        "version": version,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_path": dataset_path,
        "file_hash": stats.get("file_hash", compute_hash(dataset_path)),
        "stats": {k: v for k, v in stats.items() if k != "filepath"},
    }
    os.makedirs(output_dir, exist_ok=True)
    manifest_path = os.path.join(output_dir, f"dataset_v{version}_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return manifest_path


def load_manifest(manifest_path: str) -> Optional[Dict[str, Any]]:
    if not os.path.isfile(manifest_path):
        return None
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_dataset_integrity(dataset_path: str, manifest: Dict[str, Any]) -> bool:
    if not os.path.isfile(dataset_path):
        return False
    current_hash = compute_hash(dataset_path)
    stored_hash = manifest.get("file_hash", "")
    return current_hash == stored_hash
