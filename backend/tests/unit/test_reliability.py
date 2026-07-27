import pytest
import time
from unittest.mock import patch, MagicMock

from services.orchestrator import analyze_text
from pipeline.pipeline import PipelineRunner
from pipeline.registry import StepRegistry
from pipeline.contracts import PipelineStep, StepResult
from pipeline.types import StepStatus, StepHealth
from pipeline.context import PipelineContext
from core.auth import UserRole, create_access_token


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


class TestReliability:
    def test_repeated_investigation_execution(self):
        for i in range(5):
            result = analyze_text(f"test message {i}")
            assert result is not None
            assert "prediction" in result

    def test_long_running_request_does_not_hang(self):
        def slow_step_impl(ctx):
            time.sleep(0.1)
            return StepResult(step_id="slow_step", status=StepStatus.COMPLETED, data={"worked": True})

        reg = StepRegistry()
        reg.register(_make_step("slow_step", impl=slow_step_impl))
        runner = PipelineRunner(reg)

        start_time = time.perf_counter()
        result = runner.run("test long running")
        elapsed_time = time.perf_counter() - start_time

        assert result is not None
        assert elapsed_time < 5.0

    def test_repeated_analysis_does_not_crash(self):
        for i in range(10):
            result = analyze_text(f"reliability test {i}")
            assert result is not None

    def test_create_token_works(self):
        token = create_access_token(subject="test", role=UserRole.ADMIN)
        assert token is not None
        assert isinstance(token, str)

    def test_differs_after_multiple_tokens(self):
        tokens = set()
        for _ in range(5):
            token = create_access_token(subject="test", role=UserRole.ADMIN)
            tokens.add(token)
        assert len(tokens) > 1
