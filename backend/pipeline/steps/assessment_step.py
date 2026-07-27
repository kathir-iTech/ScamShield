from typing import Any

from domains.assessment.public import assess

from ..step import AnalysisStep


class AssessmentStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="assessment", name="Assessment", priority=60, dependencies=["evidence"])

    def execute(self, context: Any) -> Any:
        assessment = assess(dict(context.shared))
        return self._ok({
            "assessment_score": assessment["assessment_score"],
            "assessment_band": assessment["assessment_band"],
            "assessment_confidence": assessment["assessment_confidence"],
            "assessment_summary": assessment["assessment_summary"],
            "business_reason": assessment["business_reason"],
            "technical_reason": assessment["technical_reason"],
            "recommended_action": assessment["recommended_action"],
            "review_required": assessment["review_required"],
            "manual_review_reason": assessment["manual_review_reason"],
        })
