from typing import Any

from rules import analyze_message as rules_analyze
from rules import get_suggested_action

from ..step import AnalysisStep


class RulesStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="rules", name="Rule Engine", priority=20, fatal=True)

    def execute(self, context: Any) -> Any:
        rule_result = rules_analyze(context.text)
        return self._ok({
            "rule_score": rule_result["risk_score"],
            "rule_label": rule_result["risk_label"],
            "reasons": rule_result["reasons"],
            "suggested_action": get_suggested_action(str(rule_result["risk_label"])),
        })
