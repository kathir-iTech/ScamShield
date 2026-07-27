from typing import Any

from predict import predict as ml_predict

from ..step import AnalysisStep


class MLStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="ml", name="ML Prediction", priority=10, fatal=True)

    def execute(self, context: Any) -> Any:
        label, confidence = ml_predict(context.text)
        return self._ok({"prediction": label, "confidence": confidence})
