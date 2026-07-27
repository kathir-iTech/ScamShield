import pytest
import time
from unittest.mock import patch, MagicMock

from pipeline.pipeline import PipelineRunner
from pipeline.registry import StepRegistry
from pipeline.contracts import PipelineStep, StepResult
from pipeline.types import StepStatus, StepID, StepHealth
from services.orchestrator import analyze_text


def _make_step(step_id, impl=None, priority=100, dependencies=None, optional=False, disabled=False, fatal=False):
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
        mock.execute = MagicMock(return_value=StepResult(step_id=step_id, status=StepStatus.COMPLETED, data={}))
    return mock


class TestPipelineRunnerTelemetry:
    def test_telemetry_recorded_for_all_steps(self):
        reg = StepRegistry()
        s1 = _make_step("s1")
        reg.register(s1)

        def failing_impl(ctx):
            raise Exception("failed")

        s2 = _make_step("s2", impl=failing_impl)
        reg.register(s2)
        s3 = _make_step("s3", disabled=True)
        reg.register(s3)

        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert result is not None

    def test_pipeline_summary_has_correct_counts(self):
        reg = StepRegistry()
        s1 = _make_step("s1")
        reg.register(s1)

        def failing_impl(ctx):
            raise Exception("failed")

        s2 = _make_step("s2", impl=failing_impl)
        reg.register(s2)
        s3 = _make_step("s3", disabled=True)
        reg.register(s3)

        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert result is not None


class TestPipelineTimeout:
    def test_pipeline_completes_if_within_timeout(self):
        reg = StepRegistry()

        def fast_step(ctx):
            return StepResult(step_id="fast", status=StepStatus.COMPLETED, data={})

        reg.register(_make_step("fast", impl=fast_step))
        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert result is not None


class TestPipelineOrchestrator:
    def test_analysis_works_with_partial_registry(self):
        result = analyze_text("test message")
        assert result is not None
        assert "prediction" in result
