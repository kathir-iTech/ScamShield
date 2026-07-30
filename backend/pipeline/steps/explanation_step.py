from typing import Any

from domains.assessment.explanation import generate_explanation

from ..step import AnalysisStep


class ExplanationStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="explanation", name="Explanation Generation", priority=30, fatal=True)

    def execute(self, context: Any) -> Any:
        explanation = generate_explanation(context.text, dict(context.shared))
        context.data.summary = explanation["summary"]
        context.data.risk_level = explanation["risk_level"]
        context.data.scam_category = explanation["scam_category"]
        context.data.detected_indicators = explanation["detected_indicators"]
        context.data.threats = explanation["threats"]
        context.data.recommended_actions = explanation["recommended_actions"]
        return self._ok({
            "summary": explanation["summary"],
            "risk_level": explanation["risk_level"],
            "scam_category": explanation["scam_category"],
            "detected_indicators": explanation["detected_indicators"],
            "threats": explanation["threats"],
            "recommended_actions": explanation["recommended_actions"],
        })
