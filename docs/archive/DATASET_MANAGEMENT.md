# Dataset Management

## Overview

The dataset management system provides versioning, integrity verification, and
statistical analysis for training and evaluation datasets.

## Components

- `core/dataset_manager.py` — Load, split, verify, and version datasets

## Features

### Loading

```python
from core.dataset_manager import load_dataset

texts, labels, categories, stats = load_dataset("data/scam_dataset.csv")
print(f"Scam: {stats['scam']}, Safe: {stats['safe']}")
```

### Train/Test Splitting

```python
from core.dataset_manager import train_test_split

split = train_test_split(texts, labels, categories, test_ratio=0.2)
print(f"Train: {split['train']['count']}, Test: {split['test']['count']}")
```

### Cross-Validation

```python
from core.dataset_manager import cross_validation_splits

splits = cross_validation_splits(texts, labels, n_splits=5)
for s in splits:
    print(f"Fold {s['fold']}: train={s['train_count']} test={s['test_count']}")
```

### Dataset Balance

```python
from core.dataset_manager import evaluate_dataset_balance

balance = evaluate_dataset_balance(labels)
print(f"Balance: {balance['balance']}")
for w in balance['warnings']:
    print(f"Warning: {w}")
```

### Versioning

```python
from core.dataset_manager import save_manifest, load_manifest, verify_dataset_integrity

stats = {"total": 5715, "scam": 888, "safe": 4827}
manifest_path = save_manifest("data/scam_dataset.csv", "1.0", stats)

manifest = load_manifest(manifest_path)
assert verify_dataset_integrity("data/scam_dataset.csv", manifest)
```
