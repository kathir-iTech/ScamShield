import pytest
from unittest.mock import patch, MagicMock

from services.orchestrator import analyze_text
from pipeline.registry import StepRegistry
from pipeline.pipeline import PipelineRunner
from pipeline.steps import (
    MLStep, RulesStep, ExplanationStep, IntelligenceStep, EvidenceStep,
    AssessmentStep, RefinementStep, ReasoningStep, ReportStep,
)


class TestChaosPipeline:
    def test_non_fatal_step_failure_continues(self):
        with patch("pipeline.steps.KnowledgeStep.execute") as mock_execute:
            mock_execute.side_effect = Exception("Knowledge source unavailable")
            result = analyze_text("test message")
            assert result is not None
            assert "prediction" in result

    def test_pipeline_with_empty_step_registry(self):
        reg = StepRegistry()
        runner = PipelineRunner(reg)
        result = runner.run("test message")
        assert result is not None

    def test_pipeline_with_single_step(self):
        reg = StepRegistry()
        step = RulesStep()
        reg.register(step)
        runner = PipelineRunner(reg)
        result = runner.run("test message")
        assert result is not None


class TestPartialFailures:
    def test_pipeline_handles_multiple_step_failures(self):
        with patch("pipeline.steps.KnowledgeStep.execute") as mock_know, \
             patch("pipeline.steps.EvidenceStep.execute") as mock_evid:
            mock_know.side_effect = Exception("Knowledge failed")
            mock_evid.side_effect = Exception("Evidence failed")
            result = analyze_text("test message")
            assert result is not None

    def test_pipeline_handles_late_step_failure(self):
        with patch("pipeline.steps.ReportStep.execute") as mock_report:
            mock_report.side_effect = Exception("Report generation failed")
            result = analyze_text("test message")
            assert result is not None


class TestDegradedMode:
    def test_degraded_analyses_still_work(self):
        for i in range(3):
            result = analyze_text(f"degraded test {i}")
            assert result is not None

    def test_pipeline_handles_empty_input_gracefully(self):
        result = analyze_text("")
        assert result is not None
