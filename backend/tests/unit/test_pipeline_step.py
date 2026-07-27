from __future__ import annotations

import pytest

from pipeline.step import AnalysisStep
from pipeline.contracts import StepResult, StepStatus
from pipeline.types import StepID


def _make_test_step(step_id: str) -> AnalysisStep:
    class TestStep(AnalysisStep):
        def execute(self, context):
            return StepResult(step_id=step_id, status=StepStatus.COMPLETED, data={})

    return TestStep(step_id=step_id, name=step_id)


class TestStepBasics:
    def test_step_has_correct_id(self):
        step = _make_test_step("my_step")
        assert step.step_id == "my_step"

    def test_step_has_correct_name(self):
        step = _make_test_step("my_step")
        assert step.name == "my_step"

    def test_step_default_priority(self):
        step = _make_test_step("my_step")
        assert step.priority == 100

    def test_step_custom_priority(self):
        class CustomStep(AnalysisStep):
            def execute(self, context):
                return StepResult(step_id="c", status=StepStatus.COMPLETED, data={})

        step = CustomStep(step_id="c", name="c", priority=50)
        assert step.priority == 50

    def test_step_default_dependencies_empty(self):
        step = _make_test_step("my_step")
        assert step.dependencies == []

    def test_step_custom_dependencies(self):
        class CustomStep(AnalysisStep):
            def execute(self, context):
                return StepResult(step_id="c", status=StepStatus.COMPLETED, data={})

        step = CustomStep(step_id="c", name="c", dependencies=["dep1", "dep2"])
        assert step.dependencies == ["dep1", "dep2"]

    def test_step_is_not_optional_by_default(self):
        step = _make_test_step("my_step")
        assert step.optional is False

    def test_step_is_not_fatal_by_default(self):
        step = _make_test_step("my_step")
        assert step.fatal is False

    def test_step_is_not_disabled_by_default(self):
        step = _make_test_step("my_step")
        assert step.disabled is False

    def test_step_has_initial_health(self):
        step = _make_test_step("my_step")
        assert step.health.healthy is True
        assert step.health.consecutive_failures == 0


class TestStepExecute:
    def test_execute_returns_step_result(self):
        class ReturnStep(AnalysisStep):
            def execute(self, context):
                return StepResult(step_id="r", status=StepStatus.COMPLETED, data={"key": "value"})

        step = ReturnStep(step_id="r", name="r")
        result = step.execute(None)
        assert result.data["key"] == "value"

    def test_execute_failing_step_raises(self):
        class FailStep(AnalysisStep):
            def execute(self, context):
                raise RuntimeError("test failure")

        step = FailStep(step_id="f", name="f", fatal=True)
        with pytest.raises(RuntimeError, match="test failure"):
            step.execute(None)

    def test_step_helpers_ok(self):
        step = _make_test_step("s")
        result = step._ok({"data": 1})
        assert result.status == StepStatus.COMPLETED
        assert result.data["data"] == 1

    def test_step_helpers_fail(self):
        step = _make_test_step("s")
        result = step._fail("something went wrong", {"partial": True})
        assert result.status == StepStatus.FAILED
        assert result.error == "something went wrong"
        assert result.data["partial"] is True

    def test_step_helpers_skip(self):
        step = _make_test_step("s")
        result = step._skip("not applicable")
        assert result.status == StepStatus.SKIPPED
        assert result.error == "not applicable"

    def test_step_helpers_fail_without_data(self):
        step = _make_test_step("s")
        result = step._fail("error")
        assert result.data == {}


class TestStepInitializeCleanup:
    def test_initialize_default_noop(self):
        step = _make_test_step("s")
        step.initialize()

    def test_cleanup_default_noop(self):
        step = _make_test_step("s")
        step.cleanup()


class TestStepHealthTracking:
    def test_health_has_healthy_status_initially(self):
        step = _make_test_step("s")
        assert step.health.healthy is True
        assert step.health.consecutive_failures == 0

    def test_health_has_ok_status_initially(self):
        step = _make_test_step("s")
        assert step.health.healthy is True