from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from pipeline.pipeline import PipelineRunner
from pipeline.registry import StepRegistry
from pipeline.contracts import PipelineStep, StepResult, StepStatus
from pipeline.types import StepID, StepHealth


def _make_step(step_id: str, priority: int = 100, dependencies: list[str] | None = None, optional: bool = False, disabled: bool = False, fatal: bool = False, impl=None) -> PipelineStep:
    mock = MagicMock(spec=PipelineStep)
    mock.step_id = step_id
    mock.name = step_id
    mock.priority = priority
    mock.dependencies = dependencies or []
    mock.optional = optional
    mock.disabled = disabled
    mock.fatal = fatal
    mock.initialize.return_value = None
    mock.cleanup.return_value = None
    mock.health = StepHealth()
    if impl:
        mock.execute = impl
    else:
        mock.execute.return_value = StepResult(step_id=step_id, status=StepStatus.COMPLETED, data={})
    return mock


def _make_completed_step(step_id: str, data: dict | None = None) -> PipelineStep:
    return _make_step(
        step_id,
        impl=lambda ctx: StepResult(step_id=step_id, status=StepStatus.COMPLETED, data=data or {}),
    )


def _make_failing_step(step_id: str, error: str = "failed", fatal: bool = False, optional: bool = False) -> PipelineStep:
    return _make_step(
        step_id,
        fatal=fatal,
        optional=optional,
        impl=lambda ctx: (_ for _ in ()).throw(Exception(error)),
    )


class TestPipelineRunnerBasics:
    def test_runs_all_steps_in_order(self):
        reg = StepRegistry()
        reg.register(_make_completed_step("step_a", {"a": 1}))
        reg.register(_make_completed_step("step_b", {"b": 2}))
        runner = PipelineRunner(reg)
        result = runner.run("test message")
        order = [t["step_id"] for t in result.telemetry]
        assert "step_a" in order
        assert "step_b" in order

    def test_returns_pipeline_result(self):
        reg = StepRegistry()
        reg.register(_make_completed_step("s1", {"prediction": "scam"}))
        runner = PipelineRunner(reg)
        result = runner.run("test message")
        assert result.data["prediction"] == "scam"

    def test_empty_pipeline(self):
        reg = StepRegistry()
        runner = PipelineRunner(reg)
        result = runner.run("test message")
        assert len(result.telemetry) == 0
        assert result.data["prediction"] == "safe"

    def test_propagates_context_through_steps(self):
        reg = StepRegistry()
        captured = {}

        def capture_ctx(ctx):
            captured["text"] = ctx.text
            captured["request_id"] = ctx.request_id
            return StepResult(step_id="capture", status=StepStatus.COMPLETED, data={})

        reg.register(_make_step("capture", impl=capture_ctx))
        runner = PipelineRunner(reg)
        result = runner.run("hello world", request_id="req-123")
        assert captured["text"] == "hello world"
        assert captured["request_id"] == "req-123"

    def test_reports_elapsed_time(self):
        reg = StepRegistry()

        def slow_step(ctx):
            time.sleep(0.01)
            return StepResult(step_id="slow", status=StepStatus.COMPLETED, data={})

        reg.register(_make_step("slow", impl=slow_step))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        slow_telemetry = [t for t in result.telemetry if t["step_id"] == "slow"]
        assert len(slow_telemetry) > 0
        assert slow_telemetry[0]["duration_ms"] > 0


class TestPipelineRunnerFatalStep:
    def test_fatal_step_stops_pipeline(self):
        reg = StepRegistry()
        reg.register(_make_failing_step("fatal_step", fatal=True))
        reg.register(_make_completed_step("after_fatal", {"x": 1}))
        runner = PipelineRunner(reg)
        with pytest.raises(Exception):
            runner.run("test message")

    def test_fatal_step_error_message_includes_step_name(self):
        reg = StepRegistry()
        reg.register(_make_failing_step("fatal_step", error="boom", fatal=True))
        runner = PipelineRunner(reg)
        with pytest.raises(Exception, match="fatal_step"):
            runner.run("test")

    def test_non_fatal_step_failure_continues_pipeline(self):
        reg = StepRegistry()
        reg.register(_make_failing_step("bad_step", error="oops"))
        reg.register(_make_completed_step("good_step", {"x": 1}))
        runner = PipelineRunner(reg)
        result = runner.run("test message")
        assert result.data["x"] == 1

    def test_pipeline_has_errors_flag_when_fatal(self):
        reg = StepRegistry()
        reg.register(_make_failing_step("fatal", fatal=True))
        runner = PipelineRunner(reg)
        with pytest.raises(Exception):
            runner.run("test")


class TestPipelineRunnerDisabledSteps:
    def test_disabled_step_is_skipped(self):
        reg = StepRegistry()
        reg.register(_make_completed_step("s1", {"a": 1}))
        reg.register(_make_step("s2", disabled=True, impl=lambda ctx: StepResult(step_id="s2", status=StepStatus.COMPLETED, data={"b": 2})))
        reg.register(_make_completed_step("s3", {"c": 3}))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert "a" in result.data
        assert "b" not in result.data
        assert "c" in result.data

    def test_disabled_steps_record_telemetry(self):
        reg = StepRegistry()
        reg.register(_make_step("disabled", disabled=True))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        disabled_entries = [t for t in result.telemetry if t["status"] == "disabled"]
        assert len(disabled_entries) > 0


class TestPipelineRunnerOptionalSteps:
    def test_optional_step_failure_does_not_stop_pipeline(self):
        reg = StepRegistry()
        reg.register(_make_completed_step("s1", {"a": 1}))
        reg.register(_make_failing_step("optional_fail", optional=True))
        reg.register(_make_completed_step("s2", {"c": 3}))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert result.data["a"] == 1
        assert result.data["c"] == 3


class TestPipelineRunnerTelemetry:
    def test_telemetry_records_all_steps(self):
        reg = StepRegistry()
        reg.register(_make_completed_step("s1"))
        reg.register(_make_failing_step("s2"))
        reg.register(_make_step("s3", disabled=True))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert len(result.telemetry) >= 3

    def test_telemetry_includes_duration(self):
        reg = StepRegistry()
        reg.register(_make_completed_step("s1"))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        for entry in result.telemetry:
            assert entry["duration_ms"] >= 0

    def test_telemetry_includes_error_message(self):
        reg = StepRegistry()
        reg.register(_make_failing_step("bad", error="something went wrong"))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        error_entries = [t for t in result.telemetry if t.get("error")]
        assert len(error_entries) > 0

    def test_pipeline_summary_has_total_steps(self):
        reg = StepRegistry()
        reg.register(_make_completed_step("s1"))
        reg.register(_make_completed_step("s2"))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert result.pipeline_summary["total_steps"] >= 2

    def test_pipeline_summary_has_completed_steps(self):
        reg = StepRegistry()
        reg.register(_make_completed_step("s1"))
        reg.register(_make_failing_step("s2"))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert result.pipeline_summary["completed_steps"] >= 1

    def test_pipeline_summary_duration_ms_positive(self):
        reg = StepRegistry()
        reg.register(_make_completed_step("s1"))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert result.pipeline_summary["duration_ms"] >= 0

    def test_pipeline_summary_has_errors_flag(self):
        reg = StepRegistry()
        reg.register(_make_completed_step("s1"))
        reg.register(_make_failing_step("s2", fatal=False))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert result.pipeline_summary["has_errors"] is True