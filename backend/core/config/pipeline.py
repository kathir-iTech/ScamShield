__all__ = [
    "PIPELINE_DEFAULT_STEP_PRIORITY", "PIPELINE_STEP_PRIORITIES",
]

PIPELINE_DEFAULT_STEP_PRIORITY: int = 100

PIPELINE_STEP_PRIORITIES: dict = {
    "ml": 10,
    "rules": 20,
    "explanation": 30,
    "intelligence": 40,
    "evidence": 50,
    "assessment": 60,
    "refinement": 70,
    "reasoning": 80,
    "report": 90,
    "knowledge": 100,
    "connector": 110,
    "fusion": 120,
}
