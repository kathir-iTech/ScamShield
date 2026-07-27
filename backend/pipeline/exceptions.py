class PipelineError(Exception):
    pass


class StepExecutionError(PipelineError):
    def __init__(self, step_id: str, message: str, original: Exception | None = None) -> None:
        self.step_id = step_id
        self.original = original
        super().__init__(f"[{step_id}] {message}")


class DependencyError(PipelineError):
    def __init__(self, step_id: str, missing: str) -> None:
        self.step_id = step_id
        self.missing = missing
        super().__init__(f"[{step_id}] missing dependency: {missing}")


class ConfigurationError(PipelineError):
    pass


class FatalStepError(PipelineError):
    pass
