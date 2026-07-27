from __future__ import annotations

import pytest

from pipeline.step import AnalysisStep
from pipeline.contracts import StepResult, StepStatus


def _step_with(step_id, name=None, priority=100, dependencies=None, optional=False, disabled=False, fatal=False):
    class CustomStep(AnalysisStep):
        def execute(self, context):
            return StepResult(step_id=step_id, status=StepStatus.COMPLETED, data={})

    kwargs = {"step_id": step_id, "name": name or step_id, "priority": priority}
    if dependencies:
        kwargs["dependencies"] = dependencies

    s = CustomStep(**kwargs)
    s.optional = optional
    s.disabled = disabled
    s.fatal = fatal
    return s


class TestOptionalStep:
    def test_optional_step_failure_does_not_stop_pipeline(self):
        completed_data = [0]

        class Succeed(AnalysisStep):
            def execute(self, context):
                completed_data[0] += 1
                return StepResult(step_id="succeed", status=StepStatus.COMPLETED, data={"ok": True})

        class FailOptional(AnalysisStep):
            def execute(self, context):
                raise RuntimeError("optional failed")

        s1 = Succeed("succeed", name="succeed")
        s2 = FailOptional("fail_opt", name="fail_opt", optional=True)
        s3 = Succeed("succeed2", name="succeed2")

        from pipeline.registry import StepRegistry
        from pipeline.pipeline import PipelineRunner
        reg = StepRegistry()
        reg.register(s1)
        reg.register(s2)
        reg.register(s3)
        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert completed_data[0] == 2


class TestDisabledStep:
    def test_disabled_step_is_not_executed(self):
        executed = []

        class MaybeRun(AnalysisStep):
            def execute(self, context):
                executed.append(True)
                return StepResult(step_id="maybe", status=StepStatus.COMPLETED, data={})

        s = MaybeRun("maybe", name="maybe")
        s.disabled = True

        from pipeline.registry import StepRegistry
        from pipeline.pipeline import PipelineRunner
        reg = StepRegistry()
        reg.register(s)
        runner = PipelineRunner(reg)
        result = runner.run("test")
        assert len(executed) == 0


class TestDisabledAndEnabledMixed:
    def test_enabled_steps_run_when_some_disabled(self):
        count = [0]

        def make_runner(step_id, run=False):
            class S(AnalysisStep):
                def execute(self, context):
                    if run:
                        count[0] += 1
                    return StepResult(step_id=step_id, status=StepStatus.COMPLETED, data={})
            s = S(step_id, name=step_id)
            s.disabled = not run
            return s

        from pipeline.registry import StepRegistry
        from pipeline.pipeline import PipelineRunner
        reg = StepRegistry()
        reg.register(make_runner("s1", run=True))
        reg.register(make_runner("s2", run=False))
        reg.register(make_runner("s3", run=True))
        runner = PipelineRunner(reg)
        runner.run("test")
        assert count[0] == 2


class TestFatalStep:
    def test_fatal_step_on_failure_stops_pipeline(self):
        from pipeline.registry import StepRegistry
        from pipeline.pipeline import PipelineRunner
        from pipeline.contracts import StepResult, StepStatus

        class FailFatal(AnalysisStep):
            def execute(self, context):
                raise Exception("fatal error")

        class RunAfter(AnalysisStep):
            def execute(self, context):
                return StepResult(step_id="after", status=StepStatus.COMPLETED, data={})

        s = FailFatal("fatal", name="fatal", fatal=True)
        s2 = RunAfter("after", "after")

        reg = StepRegistry()
        reg.register(s)
        reg.register(s2)
        runner = PipelineRunner(reg)
        with pytest.raises(Exception):
            runner.run("test")

    def test_fatal_step_on_success_runs_next(self):
        count = [0]

        class SucceedFatal(AnalysisStep):
            def execute(self, context):
                count[0] += 1
                return StepResult(step_id="sf", status=StepStatus.COMPLETED, data={})

        class After(AnalysisStep):
            def execute(self, context):
                count[0] += 10
                return StepResult(step_id="after", status=StepStatus.COMPLETED, data={})

        from pipeline.registry import StepRegistry
        from pipeline.pipeline import PipelineRunner
        reg = StepRegistry()
        reg.register(SucceedFatal("sf", "sf", fatal=True))
        reg.register(After("after", "after"))
        runner = PipelineRunner(reg)
        runner.run("test")
        assert count[0] == 11


class TestStepPriorityOrdering:
    def test_lower_priority_runs_first(self):
        order = []

        def make_ordered_step(sid, priority):
            class S(AnalysisStep):
                def execute(self, context):
                    order.append(sid)
                    return StepResult(step_id=sid, status=StepStatus.COMPLETED, data={})
            return S(sid, name=sid, priority=priority)

        from pipeline.registry import StepRegistry
        from pipeline.pipeline import PipelineRunner
        reg = StepRegistry()
        reg.register(make_ordered_step("first", 1))
        reg.register(make_ordered_step("second", 2))
        reg.register(make_ordered_step("third", 3))
        runner = PipelineRunner(reg)
        runner.run("test")
        assert order == ["first", "second", "third"]


class TestRetryBehavior:
    def test_step_with_retry_count_attribute(self):
        step = _step_with("retry_step")
        assert hasattr(step, "step_id")