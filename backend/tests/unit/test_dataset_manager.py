import os
import json
import tempfile
import csv

from core.dataset_manager import (
    compute_hash,
    load_dataset,
    train_test_split,
    evaluate_dataset_balance,
    save_manifest,
    load_manifest,
    verify_dataset_integrity,
)


def _create_temp_csv(rows):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
    writer = csv.DictWriter(tmp, fieldnames=["text", "label", "category"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    tmp.close()
    return tmp.name


def test_compute_hash():
    tmp = _create_temp_csv([{"text": "test", "label": "scam", "category": "phishing"}])
    h = compute_hash(tmp)
    assert len(h) == 64
    os.unlink(tmp)


def test_load_dataset():
    tmp = _create_temp_csv([
        {"text": "Free lottery win", "label": "scam", "category": "lottery"},
        {"text": "Meeting at 3pm", "label": "safe", "category": "general"},
        {"text": "KYC update required", "label": "scam", "category": "banking"},
    ])
    texts, labels, categories, stats = load_dataset(tmp)
    assert len(texts) == 3
    assert labels == [1, 0, 1]
    assert categories == ["lottery", "general", "banking"]
    assert stats["scam"] == 2
    assert stats["safe"] == 1
    assert stats["total"] == 3
    os.unlink(tmp)


def test_load_dataset_labels():
    tmp = _create_temp_csv([
        {"text": "test1", "label": "scam", "category": "a"},
        {"text": "test2", "label": "safe", "category": "b"},
    ])
    texts, labels, _, _ = load_dataset(tmp)
    assert labels == [1, 0]
    os.unlink(tmp)


def test_load_dataset_stats():
    tmp = _create_temp_csv([
        {"text": "a", "label": "scam", "category": "x"},
        {"text": "b", "label": "safe", "category": "y"},
    ])
    _, _, _, stats = load_dataset(tmp)
    assert stats["file_hash"] == compute_hash(tmp)
    os.unlink(tmp)


def test_train_test_split():
    tmp = _create_temp_csv([
        {"text": f"msg{i}", "label": "scam" if i % 2 == 0 else "safe", "category": "gen"}
        for i in range(100)
    ])
    texts, labels, categories, _ = load_dataset(tmp)
    split = train_test_split(texts, labels, categories, test_ratio=0.2, random_seed=42)
    assert split["train"]["count"] == 80
    assert split["test"]["count"] == 20
    assert len(split["train"]["indices"]) == 80
    assert len(split["test"]["indices"]) == 20
    os.unlink(tmp)


def test_train_test_split_stratified():
    texts = ["a"] * 80 + ["b"] * 20
    labels = [1] * 40 + [0] * 40 + [1] * 10 + [0] * 10
    split = train_test_split(texts, labels, test_ratio=0.2, stratify=True)
    assert split["train"]["count"] == 80
    assert split["test"]["count"] == 20
    train_scam_ratio = split["train"]["scam"] / split["train"]["count"]
    test_scam_ratio = split["test"]["scam"] / split["test"]["count"]
    assert abs(train_scam_ratio - 0.5) < 0.15
    assert abs(test_scam_ratio - 0.5) < 0.15


def test_evaluate_dataset_balance_balanced():
    result = evaluate_dataset_balance([1] * 50 + [0] * 50)
    assert result["balance"] == "balanced"


def test_evaluate_dataset_balance_skewed():
    result = evaluate_dataset_balance([1] * 90 + [0] * 10)
    assert result["balance"] == "skewed"


def test_evaluate_dataset_balance_warnings():
    result = evaluate_dataset_balance([1] * 5 + [0] * 95)
    assert len(result["warnings"]) > 0


def test_save_and_load_manifest():
    import time
    tmp_dir = tempfile.mkdtemp()
    data_path = os.path.join(tmp_dir, "data.csv")
    with open(data_path, "w") as f:
        f.write("text,label\nhello,scam\n")
    stats = {"total": 1, "scam": 1, "safe": 0, "file_hash": compute_hash(data_path)}
    manifest_path = save_manifest(data_path, "1.0", stats, output_dir=tmp_dir)
    assert os.path.isfile(manifest_path)
    manifest = load_manifest(manifest_path)
    assert manifest is not None
    assert manifest["version"] == "1.0"
    assert manifest["stats"]["scam"] == 1
    assert manifest["stats"]["total"] == 1


def test_verify_dataset_integrity():
    tmp_dir = tempfile.mkdtemp()
    data_path = os.path.join(tmp_dir, "data.csv")
    with open(data_path, "w") as f:
        f.write("text,label\nhello,scam\n")
    stats = {"total": 1, "scam": 1, "safe": 0, "file_hash": compute_hash(data_path)}
    manifest_path = save_manifest(data_path, "1.0", stats, output_dir=tmp_dir)
    manifest = load_manifest(manifest_path)
    assert verify_dataset_integrity(data_path, manifest) is True
    with open(data_path, "a") as f:
        f.write("modified,scam\n")
    assert verify_dataset_integrity(data_path, manifest) is False


def test_load_manifest_nonexistent():
    assert load_manifest("/nonexistent/path.json") is None
