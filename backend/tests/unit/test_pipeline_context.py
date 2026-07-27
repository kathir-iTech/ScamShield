from __future__ import annotations

import time

import pytest

from pipeline.context import PipelineContext
from pipeline.contracts import PipelineContext as PipelineContextContract
from pipeline.types import TelemetryEntry, StepStatus
from pipeline.contracts import StepResult


class TestPipelineContext:
    def test_creation_with_required_fields(self):
        ctx = PipelineContext(
            request_id="req-1",
            text="hello world",
        )
        assert ctx.request_id == "req-1"
        assert ctx.text == "hello world"

    def test_creation_with_config(self):
        ctx = PipelineContext(
            request_id="req-1",
            text="hello",
            config={"max_length": 100},
        )
        assert ctx.config["max_length"] == 100

    def test_config_defaults_to_empty_dict(self):
        ctx = PipelineContext(request_id="r", text="t")
        assert ctx.config == {}

    def test_shared_defaults_to_empty_dict(self):
        ctx = PipelineContext(request_id="r", text="t")
        assert ctx.shared == {}

    def test_telemetry_starts_empty(self):
        ctx = PipelineContext(request_id="r", text="t")
        assert ctx.telemetry == []

    def test_step_results_starts_empty(self):
        ctx = PipelineContext(request_id="r", text="t")
        assert ctx.step_results == {}

    def test_metadata_starts_empty(self):
        ctx = PipelineContext(request_id="r", text="t")
        assert ctx.metadata == {}

    def test_store_result_updates_shared(self):
        ctx = PipelineContext(request_id="r", text="t")
        result = StepResult(
            step_id="s1",
            status=StepStatus.COMPLETED,
            data={"prediction": "scam", "confidence": 0.9},
        )
        ctx.store_result("s1", result)
        assert ctx.shared["prediction"] == "scam"
        assert ctx.shared["confidence"] == 0.9

    def test_record_step_appends_to_telemetry(self):
        ctx = PipelineContext(request_id="r", text="t")
        ctx.record_step("s1", StepStatus.COMPLETED, 10.5)
        assert len(ctx.telemetry) == 1

    def test_record_step_with_error(self):
        ctx = PipelineContext(request_id="r", text="t")
        ctx.record_step("s1", StepStatus.FAILED, 5.0, error="boom")
        assert ctx.telemetry[0].error == "boom"

    def test_record_step_with_warnings(self):
        ctx = PipelineContext(request_id="r", text="t")
        ctx.record_step("s1", StepStatus.COMPLETED, 10.0, warnings=["low confidence"])
        assert ctx.telemetry[0].warnings == ["low confidence"]

    def test_multiple_record_steps(self):
        ctx = PipelineContext(request_id="r", text="t")
        ctx.record_step("s1", StepStatus.COMPLETED, 10.0)
        ctx.record_step("s2", StepStatus.FAILED, 5.0, error="fail")
        ctx.record_step("s3", StepStatus.DISABLED, 0.0)
        assert len(ctx.telemetry) == 3

    def test_get_step_result(self):
        ctx = PipelineContext(request_id="r", text="t")
        result = StepResult(step_id="s1", status=StepStatus.COMPLETED, data={"x": 1})
        ctx.store_result("s1", result)
        stored = ctx.step_results["s1"]
        assert stored.data["x"] == 1

    def test_store_result_overwrites(self):
        ctx = PipelineContext(request_id="r", text="t")
        r1 = StepResult(step_id="s1", status=StepStatus.COMPLETED, data={"x": 1})
        r2 = StepResult(step_id="s1", status=StepStatus.COMPLETED, data={"x": 2})
        ctx.store_result("s1", r1)
        ctx.store_result("s1", r2)
        assert ctx.step_results["s1"].data["x"] == 2

    def test_shared_is_updated_in_place(self):
        ctx = PipelineContext(request_id="r", text="t")
        result = StepResult(step_id="s1", status=StepStatus.COMPLETED, data={"items": [1, 2, 3]})
        ctx.store_result("s1", result)
        assert ctx.shared["items"] == [1, 2, 3]

    def test_empty_pipeline_context_has_no_telemetry(self):
        ctx = PipelineContext(request_id="r", text="t")
        assert len(ctx.telemetry) == 0

    def test_context_isolation_different_instances(self):
        c1 = PipelineContext(request_id="r1", text="t1")
        c2 = PipelineContext(request_id="r2", text="t2")
        c1.store_result("s", StepResult(step_id="s", status=StepStatus.COMPLETED, data={"v": 1}))
        assert "s" not in c2.step_results