from typing import Any

from domains.reasoning.public import refine

from ..step import AnalysisStep


class RefinementStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="refinement", name="Refinement", priority=70, dependencies=["assessment"])

    def execute(self, context: Any) -> Any:
        analysis = dict(context.shared)
        analysis["_original_text"] = context.text
        assessment = {
            "assessment_score": context.data.assessment_score,
            "assessment_confidence": context.data.assessment_confidence,
            "review_required": context.data.review_required,
        }
        refinement_result = refine(analysis, assessment)
        context.data.refined_prediction = refinement_result.refined_prediction
        context.data.refined_assessment_score = refinement_result.refined_assessment_score
        context.data.refined_assessment_confidence = refinement_result.refined_assessment_confidence
        context.data.refined_review_required = refinement_result.refined_review_required
        context.data.decision_stable = refinement_result.decision_stable
        context.data.stability_concerns = refinement_result.stability_concerns
        context.data.refinement_summary = refinement_result.refinement_summary
        return self._ok({
            "refined_prediction": refinement_result.refined_prediction,
            "refined_assessment_score": refinement_result.refined_assessment_score,
            "refined_assessment_confidence": refinement_result.refined_assessment_confidence,
            "refined_review_required": refinement_result.refined_review_required,
            "decision_stable": refinement_result.decision_stable,
            "stability_concerns": refinement_result.stability_concerns,
            "refinement_applied_rules": refinement_result.applied_rules,
            "refinement_summary": refinement_result.refinement_summary,
        })
