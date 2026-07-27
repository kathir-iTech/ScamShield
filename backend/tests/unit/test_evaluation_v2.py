from core.evaluation_v2 import (
    EvaluationMetrics,
    evaluate_classification,
    regression_check,
    save_evaluation_result,
    format_report,
)
import json
import os
import tempfile


def test_evaluation_metrics_perfect():
    m = EvaluationMetrics([1, 1, 0, 0], [1, 1, 0, 0])
    d = m.to_dict()
    assert d["accuracy"] == 1.0
    assert d["precision"] == 1.0
    assert d["recall"] == 1.0
    assert d["f1"] == 1.0
    assert d["fpr"] == 0.0
    assert d["fnr"] == 0.0
    assert d["tp"] == 2
    assert d["tn"] == 2


def test_evaluation_metrics_all_wrong():
    m = EvaluationMetrics([1, 1, 0, 0], [0, 0, 1, 1])
    d = m.to_dict()
    assert d["accuracy"] == 0.0
    assert d["precision"] == 0.0
    assert d["recall"] == 0.0
    assert d["f1"] == 0.0
    assert d["tp"] == 0
    assert d["tn"] == 0


def test_evaluation_metrics_mixed():
    m = EvaluationMetrics([1, 1, 0, 0, 1], [1, 0, 0, 1, 1])
    d = m.to_dict()
    assert d["tp"] == 2
    assert d["fp"] == 1
    assert d["fn"] == 1
    assert d["tn"] == 1


def test_evaluation_metrics_edge_no_positives():
    m = EvaluationMetrics([0, 0, 0], [0, 0, 0])
    d = m.to_dict()
    assert d["precision"] == 0.0
    assert d["recall"] == 0.0
    assert d["f1"] == 0.0


def test_evaluation_metrics_single():
    m = EvaluationMetrics([1], [1])
    assert m.to_dict()["accuracy"] == 1.0
    m2 = EvaluationMetrics([1], [0])
    assert m2.to_dict()["accuracy"] == 0.0


def test_evaluation_metrics_summary():
    m = EvaluationMetrics([1, 1, 0, 0], [1, 1, 0, 0])
    s = m.summary()
    assert "acc=100.0%" in s
    assert "f1=100.0%" in s


def test_regression_check_passes():
    baseline = {"accuracy": 0.9, "precision": 0.9, "recall": 0.9, "f1": 0.9, "fpr": 0.1, "fnr": 0.1}
    current = {"accuracy": 0.91, "precision": 0.91, "recall": 0.91, "f1": 0.91, "fpr": 0.09, "fnr": 0.09}
    result = regression_check(baseline, current)
    assert result["passed"] is True
    assert len(result["issues"]) == 0


def test_regression_check_fails_accuracy():
    baseline = {"accuracy": 0.9, "precision": 0.9, "recall": 0.9, "f1": 0.9, "fpr": 0.1, "fnr": 0.1}
    current = {"accuracy": 0.85, "precision": 0.9, "recall": 0.9, "f1": 0.9, "fpr": 0.1, "fnr": 0.1}
    result = regression_check(baseline, current)
    assert result["passed"] is False
    assert len(result["issues"]) > 0


def test_regression_check_fails_fpr():
    baseline = {"accuracy": 0.9, "precision": 0.9, "recall": 0.9, "f1": 0.9, "fpr": 0.1, "fnr": 0.1}
    current = {"accuracy": 0.9, "precision": 0.9, "recall": 0.9, "f1": 0.9, "fpr": 0.2, "fnr": 0.1}
    result = regression_check(baseline, current)
    assert result["passed"] is False


def test_regression_check_custom_thresholds():
    baseline = {"accuracy": 0.9, "precision": 0.9, "recall": 0.9, "f1": 0.9, "fpr": 0.1, "fnr": 0.1}
    current = {"accuracy": 0.88, "precision": 0.9, "recall": 0.9, "f1": 0.9, "fpr": 0.1, "fnr": 0.1}
    result = regression_check(baseline, current, {"accuracy_drop": 0.05})
    assert result["passed"] is True


def test_save_evaluation_result():
    tmp_dir = tempfile.mkdtemp()
    result = {
        "metrics": {"accuracy": 0.9, "precision": 0.9, "recall": 0.9, "f1": 0.9, "fpr": 0.1, "fnr": 0.1, "tp": 5, "fp": 1, "fn": 1, "tn": 5, "mcc": 0.7, "balanced_accuracy": 0.9, "n": 12},
        "samples": {"total": 12, "scam": 6, "safe": 6},
        "latency": {"average_ms": 10.0, "p95_ms": 15.0, "count": 12},
        "predictions": [],
        "errors": [],
        "category_breakdown": [],
        "language_breakdown": [],
        "summary": "test",
        "timestamp": "2024-01-01T00:00:00Z",
    }
    path = save_evaluation_result(result, tmp_dir)
    assert os.path.isfile(path)
    with open(path) as f:
        loaded = json.load(f)
    assert loaded["metrics"]["accuracy"] == 0.9


def test_format_report():
    result = {
        "metrics": {"accuracy": 0.9, "precision": 0.9, "recall": 0.9, "f1": 0.9, "fpr": 0.1, "fnr": 0.1, "tp": 5, "fp": 1, "fn": 1, "tn": 5, "mcc": 0.7, "balanced_accuracy": 0.9, "n": 12},
        "samples": {"total": 12, "scam": 6, "safe": 6},
        "latency": {"average_ms": 10.0, "p95_ms": 15.0, "count": 12},
        "predictions": [],
        "errors": [],
        "category_breakdown": [{"category": "Phishing", "total": 5, "accuracy": 0.9, "risk_accuracy": 0.8, "assessment_accuracy": 0.7}],
        "language_breakdown": [{"language": "en", "total": 10, "accuracy": 0.9}],
        "summary": "test",
        "timestamp": "2024-01-01T00:00:00Z",
    }
    report = format_report(result)
    assert "90.0%" in report
    assert "EVALUATION REPORT" in report
    assert "Phishing" in report
