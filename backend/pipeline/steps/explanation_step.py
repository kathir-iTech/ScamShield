from typing import Any

from domains.assessment.explanation import generate_explanation

from ..step import AnalysisStep


class ExplanationStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="explanation", name="Explanation Generation", priority=30, fatal=True)

    def execute(self, context: Any) -> Any:
        explanation = generate_explanation(context.text, dict(context.shared))
        return self._ok({
            "summary": explanation["summary"],
            "risk_level": explanation["risk_level"],
            "scam_category": explanation["scam_category"],
            "detected_indicators": explanation["detected_indicators"],
            "threats": explanation["threats"],
            "recommended_actions": explanation["recommended_actions"],
        })
