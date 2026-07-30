from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pytest

import core.model_registry as mr_mod
from core.drift_detector import DriftDetector, DriftResult, detect_drift
from core.eval_scheduler import (
    EvaluationResult,
    compare_with_baseline,
    get_evaluation_history,
    get_latest_evaluation,
)
from core.model_registry import ModelMetadata, ModelRegistry, get_registry
from core.prediction_logger import (
    PredictionLogger,
    PredictionRecord,
    get_prediction_logger,
    log_prediction,
)


@pytest.fixture
def registry(tmp_path: Path) -> ModelRegistry:
    original_training_log = mr_mod.TRAINING_LOG_PATH
    mr_mod.TRAINING_LOG_PATH = str(tmp_path / "no_training_log.json")
    try:
        reg = ModelRegistry(registry_path=str(tmp_path / "registry.json"))
        reg._load()
        return reg
    finally:
        mr_mod.TRAINING_LOG_PATH = original_training_log


# ---------------------------------------------------------------------------
# ModelRegistry tests
# ---------------------------------------------------------------------------

class TestModelRegistry:

    def test_register_and_get_active(self, registry: ModelRegistry) -> None:
        meta = ModelMetadata(
            version="v20260730_120000",
            model_type="LogisticRegression",
            trained_at="2026-07-30T12:00:00Z",
            dataset_path="/fake/path.csv",
            dataset_samples=100,
            params={"C": 1.0},
            cv_metrics={"f1": 0.95},
            test_metrics={"accuracy": 0.96, "f1": 0.95},
            file_path="/fake/model.joblib",
            vectorizer_path="/fake/vectorizer.joblib",
            status="staging",
        )
        v = registry.register_model(meta)
        assert v == "v20260730_120000"
        assert registry.model_count() == 1

        registry.set_active_model("v20260730_120000")
        active = registry.get_active_model()
        assert active is not None
        assert active.version == "v20260730_120000"
        assert active.status == "active"

    def test_set_active_model(self, registry: ModelRegistry) -> None:
        m1 = ModelMetadata(version="v1", file_path="/a", vectorizer_path="/b")
        m2 = ModelMetadata(version="v2", file_path="/c", vectorizer_path="/d")
        registry.register_model(m1)
        registry.register_model(m2)

        registry.set_active_model("v1")
        registry.set_active_model("v2")
        active = registry.get_active_model()
        assert active is not None
        assert active.version == "v2"
        assert active.status == "active"

        archived = registry.get_model("v1")
        assert archived is not None
        assert archived.status == "archived"

    def test_list_models(self, registry: ModelRegistry) -> None:
        for i in range(3):
            m = ModelMetadata(version=f"v{i}", file_path="/a", vectorizer_path="/b")
            registry.register_model(m)
        models = registry.list_models()
        assert len(models) == 3
        versions = [m.version for m in models]
        assert "v0" in versions
        assert "v1" in versions
        assert "v2" in versions

    def test_get_model(self, registry: ModelRegistry) -> None:
        m = ModelMetadata(version="v_test", file_path="/a", vectorizer_path="/b")
        registry.register_model(m)
        retrieved = registry.get_model("v_test")
        assert retrieved is not None
        assert retrieved.version == "v_test"
        assert registry.get_model("nonexistent") is None

    def test_archive_model(self, registry: ModelRegistry) -> None:
        m = ModelMetadata(version="v_arch", file_path="/a", vectorizer_path="/b")
        registry.register_model(m)
        registry.archive_model("v_arch")
        archived = registry.get_model("v_arch")
        assert archived is not None
        assert archived.status == "archived"

    def test_archive_nonexistent_raises(self, registry: ModelRegistry) -> None:
        with pytest.raises(KeyError):
            registry.archive_model("nonexistent")

    def test_rollback_to_previous(self, registry: ModelRegistry) -> None:
        m1 = ModelMetadata(version="v1", file_path="/a", vectorizer_path="/b")
        m2 = ModelMetadata(version="v2", file_path="/c", vectorizer_path="/d")
        registry.register_model(m1)
        registry.register_model(m2)
        registry.set_active_model("v2")

        rolled = registry.rollback()
        assert rolled == "v1"
        active = registry.get_active_model()
        assert active is not None
        assert active.version == "v1"

    def test_rollback_specific(self, registry: ModelRegistry) -> None:
        m1 = ModelMetadata(version="v1", file_path="/a", vectorizer_path="/b")
        m2 = ModelMetadata(version="v2", file_path="/c", vectorizer_path="/d")
        registry.register_model(m1)
        registry.register_model(m2)
        registry.set_active_model("v2")
        registry.rollback("v1")
        active = registry.get_active_model()
        assert active is not None
        assert active.version == "v1"

    def test_rollback_no_previous_raises(self, registry: ModelRegistry) -> None:
        m = ModelMetadata(version="v1", file_path="/a", vectorizer_path="/b")
        registry.register_model(m)
        registry.set_active_model("v1")
        with pytest.raises(RuntimeError, match="No previous version"):
            registry.rollback()

    def test_rollback_nonexistent_raises(self, registry: ModelRegistry) -> None:
        with pytest.raises(KeyError):
            registry.rollback("nonexistent")

    def test_model_count(self, registry: ModelRegistry) -> None:
        assert registry.model_count() == 0
        registry.register_model(ModelMetadata(version="v1", file_path="/a", vectorizer_path="/b"))
        assert registry.model_count() == 1
        registry.register_model(ModelMetadata(version="v2", file_path="/a", vectorizer_path="/b"))
        assert registry.model_count() == 2

    def test_thread_safety(self, registry: ModelRegistry) -> None:
        errors: List[Exception] = []

        def register_many(start: int, count: int) -> None:
            for i in range(start, start + count):
                try:
                    m = ModelMetadata(
                        version=f"v{i}",
                        file_path="/a",
                        vectorizer_path="/b",
                    )
                    registry.register_model(m)
                except Exception as e:
                    errors.append(e)

        threads = [
            threading.Thread(target=register_many, args=(0, 50)),
            threading.Thread(target=register_many, args=(50, 50)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert registry.model_count() == 100

    def test_get_registry_singleton(self) -> None:
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_rollback_changes_active(self, registry: ModelRegistry) -> None:
        m1 = ModelMetadata(version="v_old", file_path="/a", vectorizer_path="/b")
        m2 = ModelMetadata(version="v_new", file_path="/c", vectorizer_path="/d")
        registry.register_model(m1)
        registry.register_model(m2)
        registry.set_active_model("v_new")
        registry.rollback("v_old")
        active = registry.get_active_model()
        assert active is not None
        assert active.version == "v_old"

    def test_rollback_archives_current(self, registry: ModelRegistry) -> None:
        m1 = ModelMetadata(version="v1", file_path="/a", vectorizer_path="/b")
        m2 = ModelMetadata(version="v2", file_path="/c", vectorizer_path="/d")
        registry.register_model(m1)
        registry.register_model(m2)
        registry.set_active_model("v2")
        registry.rollback("v1")
        archived = registry.get_model("v2")
        assert archived is not None
        assert archived.status == "archived"

    def test_rollback_then_list(self, registry: ModelRegistry) -> None:
        m1 = ModelMetadata(version="v1", file_path="/a", vectorizer_path="/b")
        m2 = ModelMetadata(version="v2", file_path="/c", vectorizer_path="/d")
        registry.register_model(m1)
        registry.register_model(m2)
        registry.set_active_model("v2")
        registry.rollback("v1")
        models = registry.list_models()
        versions = {m.version: m.status for m in models}
        assert versions["v1"] == "active"
        assert versions["v2"] == "archived"


# ---------------------------------------------------------------------------
# PredictionLogger tests
# ---------------------------------------------------------------------------

class TestPredictionLogger:

    @pytest.fixture
    def logger(self, tmp_path: Path) -> PredictionLogger:
        return PredictionLogger(log_dir=str(tmp_path / "predictions"))

    def test_log_and_retrieve(self, logger: PredictionLogger) -> None:
        record = PredictionRecord(
            request_id="req-001",
            timestamp="2026-07-30T12:00:00Z",
            text_hash="abc123",
            text_preview="test message",
            prediction="scam",
            confidence=0.95,
            model_version="v20260730_120000",
            pipeline_steps=["preprocess", "classify"],
            latency_ms=12.5,
            category="PHISHING",
        )
        logger.log_prediction(record)
        recent = logger.get_recent_predictions(10)
        assert len(recent) == 1
        assert recent[0].request_id == "req-001"
        assert recent[0].prediction == "scam"
        assert recent[0].confidence == 0.95

    def test_recent_limit(self, logger: PredictionLogger) -> None:
        for i in range(100):
            r = PredictionRecord(
                request_id=f"req-{i:03d}",
                timestamp="2026-07-30T12:00:00Z",
                text_hash=f"hash{i}",
                text_preview=f"msg {i}",
                prediction="scam" if i % 2 == 0 else "safe",
                confidence=0.5 + i / 200,
                model_version="v1",
            )
            logger.log_prediction(r)
        recent = logger.get_recent_predictions(10)
        assert len(recent) == 10
        assert recent[0].request_id == "req-090"

    def test_get_stats(self, logger: PredictionLogger) -> None:
        for i in range(10):
            r = PredictionRecord(
                request_id=f"req-{i}",
                timestamp="2026-07-30T12:00:00Z",
                text_hash=f"hash{i}",
                text_preview=f"msg {i}",
                prediction="scam",
                confidence=0.9,
                model_version="v1",
            )
            logger.log_prediction(r)
        stats = logger.get_stats()
        assert stats["total"] == 10
        assert stats["scam"] == 10
        assert stats["safe"] == 0
        assert stats["avg_confidence"] == 0.9

    def test_get_stats_mixed(self, logger: PredictionLogger) -> None:
        for i in range(5):
            logger.log_prediction(PredictionRecord(
                request_id=f"req-{i}",
                timestamp="2026-07-30T12:00:00Z",
                text_hash=f"hash{i}",
                text_preview=f"msg {i}",
                prediction="scam" if i < 3 else "safe",
                confidence=0.8,
                model_version="v1",
            ))
        stats = logger.get_stats()
        assert stats["total"] == 5
        assert stats["scam"] == 3
        assert stats["safe"] == 2
        assert stats["scam_ratio"] == 0.6

    def test_get_daily_stats(self, logger: PredictionLogger) -> None:
        for i in range(5):
            logger.log_prediction(PredictionRecord(
                request_id=f"req-{i}",
                timestamp="2026-07-30T12:00:00Z",
                text_hash=f"hash{i}",
                text_preview=f"msg {i}",
                prediction="scam",
                confidence=0.8,
                model_version="v1",
            ))
        daily = logger.get_daily_stats()
        assert "2026-07-30" in daily
        assert daily["2026-07-30"]["total"] == 5
        assert daily["2026-07-30"]["scam"] == 5

    def test_recent_method(self, logger: PredictionLogger) -> None:
        for i in range(5):
            logger.log_prediction(PredictionRecord(
                request_id=f"req-{i}",
                timestamp="2026-07-30T12:00:00Z",
                text_hash=f"hash{i}",
                text_preview=f"msg {i}",
                prediction="scam",
                confidence=0.8,
                model_version="v1",
            ))
        rec = logger.recent(3)
        assert len(rec) == 3

    def test_empty_stats(self, logger: PredictionLogger) -> None:
        stats = logger.get_stats()
        assert stats["total"] == 0

    def test_file_persistence(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "preds"
        lg = PredictionLogger(log_dir=str(log_dir))
        lg.log_prediction(PredictionRecord(
            request_id="req-persist",
            timestamp="2026-07-30T12:00:00Z",
            text_hash="hash",
            text_preview="persist",
            prediction="safe",
            confidence=0.99,
            model_version="v1",
        ))
        date_str = "2026-07-30"
        log_file = log_dir / f"{date_str}.jsonl"
        assert log_file.exists()
        content = log_file.read_text()
        assert "req-persist" in content
        assert "safe" in content

    def test_get_prediction_logger_singleton(self) -> None:
        p1 = get_prediction_logger()
        p2 = get_prediction_logger()
        assert p1 is p2

    def test_log_prediction_convenience(self, tmp_path: Path) -> None:
        from core.prediction_logger import _logger_instance
        saved = _logger_instance
        import core.prediction_logger as pl_mod
        pl_mod._logger_instance = None
        try:
            pl = PredictionLogger(log_dir=str(tmp_path / "preds"))
            pl_mod._logger_instance = pl

            log_prediction(
                request_id="conv-001",
                text="hello world",
                prediction="safe",
                confidence=0.5,
                model_version="v1",
                latency_ms=5.0,
                category="LEGIT",
            )
            recent = pl.get_recent_predictions(10)
            assert len(recent) == 1
            assert recent[0].request_id == "conv-001"
            assert recent[0].category == "LEGIT"
            expected_hash = hashlib.md5(b"hello world").hexdigest()
            assert recent[0].text_hash == expected_hash
            assert recent[0].text_preview == "hello world"
        finally:
            pl_mod._logger_instance = saved


# ---------------------------------------------------------------------------
# DriftDetector tests
# ---------------------------------------------------------------------------

class TestDriftDetector:

    def test_accuracy_drift_no_drift(self) -> None:
        r = DriftDetector.check_accuracy_drift(0.95, 0.95, threshold=0.05)
        assert not r.has_drift
        assert r.severity == "none"
        assert r.metric_name == "accuracy"

    def test_accuracy_drift_detected(self) -> None:
        r = DriftDetector.check_accuracy_drift(0.85, 0.95, threshold=0.05)
        assert r.has_drift
        assert r.severity == "warning"

    def test_accuracy_drift_critical(self) -> None:
        r = DriftDetector.check_accuracy_drift(0.70, 0.95, threshold=0.05)
        assert r.has_drift
        assert r.severity == "critical"

    def test_accuracy_drift_below_threshold(self) -> None:
        r = DriftDetector.check_accuracy_drift(0.93, 0.95, threshold=0.05)
        assert not r.has_drift

    def test_confidence_drift_no_drift(self) -> None:
        curr = {"0.7_0.9": 0.3, "0.9_1.0": 0.7}
        base = {"0.7_0.9": 0.3, "0.9_1.0": 0.7}
        r = DriftDetector.check_confidence_drift(curr, base, threshold=0.1)
        assert not r.has_drift

    def test_confidence_drift_detected(self) -> None:
        curr = {"0.0_0.5": 1.0}
        base = {"0.9_1.0": 1.0}
        r = DriftDetector.check_confidence_drift(curr, base, threshold=0.1)
        assert r.has_drift

    def test_data_drift_no_drift(self) -> None:
        r = DriftDetector.check_data_drift(0.7, 0.7, threshold=0.1)
        assert not r.has_drift

    def test_data_drift_detected(self) -> None:
        r = DriftDetector.check_data_drift(0.3, 0.7, threshold=0.1)
        assert r.has_drift
        assert r.severity == "critical"

    def test_data_drift_warning(self) -> None:
        r = DriftDetector.check_data_drift(0.55, 0.7, threshold=0.1)
        assert r.has_drift
        assert r.severity == "warning"

    def test_data_drift_critical(self) -> None:
        r = DriftDetector.check_data_drift(0.1, 0.7, threshold=0.1)
        assert r.has_drift
        assert r.severity == "critical"

    def test_latency_drift_no_baseline(self) -> None:
        r = DriftDetector.check_latency_drift(100.0, 0.0, threshold=0.2)
        assert not r.has_drift
        assert "No baseline" in r.details

    def test_latency_drift_no_drift(self) -> None:
        r = DriftDetector.check_latency_drift(105.0, 100.0, threshold=0.2)
        assert not r.has_drift

    def test_latency_drift_detected(self) -> None:
        r = DriftDetector.check_latency_drift(150.0, 100.0, threshold=0.2)
        assert r.has_drift
        assert r.severity == "critical"

    def test_latency_drift_warning(self) -> None:
        r = DriftDetector.check_latency_drift(125.0, 100.0, threshold=0.2)
        assert r.has_drift
        assert r.severity == "warning"

    def test_latency_drift_critical(self) -> None:
        r = DriftDetector.check_latency_drift(200.0, 100.0, threshold=0.2)
        assert r.has_drift
        assert r.severity == "critical"

    def test_generate_report_no_results(self) -> None:
        report = DriftDetector.generate_report([])
        assert "No drift checks performed" in report

    def test_generate_report_with_results(self) -> None:
        results = [
            DriftDetector.check_accuracy_drift(0.85, 0.95),
            DriftDetector.check_data_drift(0.5, 0.7),
        ]
        report = DriftDetector.generate_report(results)
        assert "DRIFT DETECTION REPORT" in report
        assert "accuracy" in report
        assert "class_ratio" in report

    def test_run_all_checks_empty_logger(self) -> None:
        class EmptyLogger:
            @staticmethod
            def get_stats() -> Dict:
                return {"total": 0}
        results = DriftDetector.run_all_checks(EmptyLogger())
        assert results == []

    def test_run_all_checks_with_data(self) -> None:
        class DummyLogger:
            @staticmethod
            def get_stats() -> Dict:
                return {
                    "total": 100,
                    "scam": 60,
                    "safe": 40,
                    "scam_ratio": 0.6,
                    "avg_confidence": 0.85,
                    "confidence_distribution": {
                        "0_0.5": 5,
                        "0.5_0.7": 10,
                        "0.7_0.9": 30,
                        "0.9_1.0": 55,
                    },
                }
        results = DriftDetector.run_all_checks(DummyLogger())
        assert len(results) == 3

    def test_detect_drift_convenience(self) -> None:
        results = detect_drift()
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# EvalScheduler tests
# ---------------------------------------------------------------------------

class TestEvalScheduler:

    def test_compare_with_baseline_none(self) -> None:
        result = compare_with_baseline({"metrics": {"f1": 0.95}}, None)
        assert result["regressions"] == []
        assert result["improvements"] == []

    def test_compare_with_baseline_no_metrics(self) -> None:
        result = compare_with_baseline(
            {"metrics": {"f1": 0.96}},
            {"metrics": {"f1": 0.95}},
        )
        assert isinstance(result, dict)
        assert "regressions" in result

    def test_get_latest_evaluation_no_dir(self, tmp_path: Path) -> None:
        import core.eval_scheduler as es
        original = es.EVALS_DIR
        es.EVALS_DIR = str(tmp_path / "nonexistent")
        try:
            result = get_latest_evaluation()
            assert result is None
        finally:
            es.EVALS_DIR = original

    def test_get_evaluation_history_no_dir(self, tmp_path: Path) -> None:
        import core.eval_scheduler as es
        original = es.EVALS_DIR
        es.EVALS_DIR = str(tmp_path / "nonexistent")
        try:
            results = get_evaluation_history(5)
            assert results == []
        finally:
            es.EVALS_DIR = original

    def test_evaluation_result_dataclass(self) -> None:
        r = EvaluationResult(
            timestamp="2026-07-30T12:00:00Z",
            metrics={"accuracy": 0.95},
            dataset="/fake.csv",
            model_version="v1",
            duration=1.5,
        )
        assert r.timestamp == "2026-07-30T12:00:00Z"
        assert r.metrics["accuracy"] == 0.95
        assert r.duration == 1.5
        assert r.regressions == []
        assert r.improvements == []
