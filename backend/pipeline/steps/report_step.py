from typing import Any

from domains.reporting.public import generate_report

from ..step import AnalysisStep


class ReportStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="report", name="Report Generation", priority=90, dependencies=["reasoning"])

    def execute(self, context: Any) -> Any:
        report = generate_report(dict(context.shared))
        return self._ok({
            "investigation_report": report,
        })
