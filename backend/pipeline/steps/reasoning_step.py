from typing import Any

from domains.reasoning.public import reason

from ..step import AnalysisStep


class ReasoningStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="reasoning", name="Reasoning", priority=80, dependencies=["refinement"])

    def execute(self, context: Any) -> Any:
        analysis = dict(context.shared)
        assessment = {
            "assessment_score": context.data.assessment_score,
            "assessment_confidence": context.data.assessment_confidence,
        }
        applied_rules = context.data.refinement_applied_rules
        refinement_result = {
            "applied_rules": applied_rules,
            "refinement_summary": context.data.refinement_summary,
        } if applied_rules else None

        reasoning_result = reason(analysis, assessment, refinement_result)
        context.data.reasoning_family = reasoning_result.family
        context.data.reasoning_subfamily = reasoning_result.subfamily
        context.data.reasoning_family_confidence = reasoning_result.family_confidence
        context.data.reasoning_summary = reasoning_result.reasoning_summary
        context.data.reasoning_evidence_graph = reasoning_result.evidence_graph
        context.data.reasoning_decision_trace = reasoning_result.decision_trace
        context.data.reasoning_primary_evidence = reasoning_result.primary_evidence
        context.data.reasoning_supporting_evidence = reasoning_result.supporting_evidence
        context.data.reasoning_weak_evidence = reasoning_result.weak_evidence
        context.data.reasoning_contradictory_evidence = reasoning_result.contradictory_evidence
        context.data.reasoning_dominant_evidence_chain = reasoning_result.dominant_evidence_chain
        return self._ok({
            "reasoning_family": reasoning_result.family,
            "reasoning_subfamily": reasoning_result.subfamily,
            "reasoning_family_confidence": reasoning_result.family_confidence,
            "reasoning_summary": reasoning_result.reasoning_summary,
            "reasoning_evidence_graph": reasoning_result.evidence_graph,
            "reasoning_decision_trace": reasoning_result.decision_trace,
            "reasoning_primary_evidence": reasoning_result.primary_evidence,
            "reasoning_supporting_evidence": reasoning_result.supporting_evidence,
            "reasoning_weak_evidence": reasoning_result.weak_evidence,
            "reasoning_contradictory_evidence": reasoning_result.contradictory_evidence,
            "reasoning_dominant_evidence_chain": reasoning_result.dominant_evidence_chain,
        })
