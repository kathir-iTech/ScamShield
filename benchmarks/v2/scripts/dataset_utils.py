from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timezone

import numpy as np

from ..config.dataset_schema import validate_sample, generate_sample_id


def load_dataset_json(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("samples", data.get("data", []))
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of samples, got {type(data).__name__}")
    return data


def load_dataset_csv(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    samples: List[Dict[str, Any]] = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}
            if "is_scam" in row:
                row["is_scam"] = row["is_scam"].lower() in ("true", "1", "yes")
            if "extracted_entities" in row and row["extracted_entities"]:
                try:
                    row["extracted_entities"] = json.loads(row["extracted_entities"])
                except (json.JSONDecodeError, TypeError):
                    row["extracted_entities"] = {}
            samples.append(row)
    return samples


def save_dataset_json(samples: List[Dict[str, Any]], path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)


def save_dataset_csv(samples: List[Dict[str, Any]], path: str) -> None:
    if not samples:
        raise ValueError("No samples to save")

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(samples[0].keys())
    with open(p, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sample in samples:
            row = dict(sample)
            if isinstance(row.get("extracted_entities"), dict):
                row["extracted_entities"] = json.dumps(row["extracted_entities"], ensure_ascii=False)
            if isinstance(row.get("is_scam"), bool):
                row["is_scam"] = str(row["is_scam"])
            writer.writerow(row)


def merge_datasets(datasets: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    for ds in datasets:
        for sample in ds:
            sid = sample.get("id", "")
            if sid and sid in seen_ids:
                continue
            if sid:
                seen_ids.add(sid)
            merged.append(sample)

    return merged


def deduplicate_by_text(samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen_texts: Set[str] = set()
    deduped: List[Dict[str, Any]] = []

    for sample in samples:
        text = sample.get("text_clean", sample.get("text", "")).strip().lower()
        if not text or text in seen_texts:
            continue
        seen_texts.add(text)
        deduped.append(sample)

    return deduped


def split_train_test(
    samples: List[Dict[str, Any]],
    test_size: float = 0.2,
    stratify_by: str = "is_scam",
    random_seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    random.seed(random_seed)
    if not samples:
        return [], []

    if stratify_by:
        groups: Dict[Any, List[Dict[str, Any]]] = {}
        for s in samples:
            key = s.get(stratify_by)
            if key not in groups:
                groups[key] = []
            groups[key].append(s)

        train: List[Dict[str, Any]] = []
        test: List[Dict[str, Any]] = []
        for key, group in groups.items():
            random.shuffle(group)
            n_test = max(1, int(len(group) * test_size))
            test.extend(group[:n_test])
            train.extend(group[n_test:])
    else:
        shuffled = list(samples)
        random.shuffle(shuffled)
        n_test = max(1, int(len(shuffled) * test_size))
        test = shuffled[:n_test]
        train = shuffled[n_test:]

    return train, test


def get_category_stats(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    scam_count = 0
    legit_count = 0

    for s in samples:
        cat = s.get("category", "UNKNOWN")
        counts[cat] = counts.get(cat, 0) + 1
        if s.get("is_scam", False):
            scam_count += 1
        else:
            legit_count += 1

    total = len(samples)
    return {
        "total_samples": total,
        "num_categories": len(counts),
        "per_category": dict(sorted(counts.items())),
        "scam_count": scam_count,
        "legitimate_count": legit_count,
        "scam_ratio": round(scam_count / total, 4) if total > 0 else 0.0,
        "legitimate_ratio": round(legit_count / total, 4) if total > 0 else 0.0,
    }


def get_language_stats(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for s in samples:
        lang = s.get("language", "unknown")
        counts[lang] = counts.get(lang, 0) + 1
    total = len(samples)
    return {
        "total_samples": total,
        "num_languages": len(counts),
        "per_language": dict(sorted(counts.items())),
        "language_ratios": {
            lang: round(cnt / total, 4) for lang, cnt in sorted(counts.items())
        } if total > 0 else {},
    }


def balance_dataset(
    samples: List[Dict[str, Any]],
    target_per_category: int = 100,
    random_seed: int = 42,
) -> List[Dict[str, Any]]:
    random.seed(random_seed)
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for s in samples:
        cat = s.get("category", "UNKNOWN")
        if cat not in groups:
            groups[cat] = []
        groups[cat].append(s)

    balanced: List[Dict[str, Any]] = []
    for cat, group in groups.items():
        if len(group) >= target_per_category:
            selected = random.sample(group, target_per_category)
        else:
            selected = random.choices(group, k=target_per_category)
        balanced.extend(selected)

    random.shuffle(balanced)
    return balanced


def export_for_training(
    samples: List[Dict[str, Any]]
) -> Tuple[List[str], List[int], List[str]]:
    texts: List[str] = []
    labels: List[int] = []
    categories: List[str] = []

    for s in samples:
        text = s.get("text_clean") or s.get("text", "")
        if not text:
            continue
        texts.append(text)
        labels.append(1 if s.get("is_scam", False) else 0)
        categories.append(s.get("category", "UNKNOWN"))

    return texts, labels, categories
