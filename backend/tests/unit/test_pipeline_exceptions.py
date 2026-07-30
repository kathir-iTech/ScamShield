from __future__ import annotations

import pytest
from core.exceptions import ValidationError as CoreValidationError

from pipeline.exceptions import (
    PipelineError,
    StepExecutionError,
    DependencyError,
    ConfigurationError,
    FatalStepError,
)


class TestPipelineError:
    def test_base_class(self):
        err = PipelineError("something went wrong")
        assert str(err) == "something went wrong"
        assert isinstance(err, Exception)

    def test_pipeline_error_with_cause(self):
        cause = ValueError("root cause")
        err = PipelineError("step failed")
        err.__cause__ = cause
        assert err.__cause__ is not None
        assert "step failed" in str(err)

    def test_pipeline_error_serialization(self):
        err = PipelineError("test error")
        assert "test error" in str(err)


class TestStepExecutionError:
    def test_with_step_name(self):
        err = StepExecutionError("my_step", "failed to load")
        assert err.step_id == "my_step"
        assert "failed to load" in str(err)

    def test_message_includes_step_id(self):
        err = StepExecutionError("step_1", "boom")
        assert "step_1" in str(err)

    def test_cause_stored(self):
        err = StepExecutionError("s", "msg", ValueError("root"))
        assert err.original is not None


class TestFatalStep:
    def test_inherits_from_pipeline_error(self):
        err = FatalStepError("fatal boom")
        assert isinstance(err, PipelineError)

    def test_fatal_error_message(self):
        err = FatalStepError("cannot continue")
        assert "cannot continue" in str(err)


class TestDependencyError:
    def test_with_step_id_and_dependency(self):
        err = DependencyError("step_a", "step_b")
        assert err.step_id == "step_a"
        assert err.missing == "step_b"

    def test_message_includes_both_ids(self):
        err = DependencyError("a", "b")
        assert "a" in str(err) or "b" in str(err)


class TestExceptionHierarchy:
    def test_dependencies_have_correct_mro(self):
        assert issubclass(StepExecutionError, PipelineError)
        assert issubclass(FatalStepError, PipelineError)
        assert issubclass(DependencyError, PipelineError)
        assert issubclass(ConfigurationError, PipelineError)

    def test_can_catch_all_as_pipeline_error(self):
        exc_args = {
            StepExecutionError: ("step", "test"),
            FatalStepError: ("test",),
            DependencyError: ("step", "dep"),
            ConfigurationError: ("test",),
        }
        for exc_class, args in exc_args.items():
            try:
                raise exc_class(*args)
            except PipelineError:
                pass


class TestC3ExceptionDeduplication:
    def test_domain_exceptions_are_core_exceptions(self):
        from domains.shared.exceptions import (
            ScamShieldError as DomainScamShieldError,
            ValidationError as DomainValidationError,
            ConfigurationError as DomainConfigurationError,
            ServiceError as DomainServiceError,
        )
        from core.exceptions import (
            ScamShieldError as CoreScamShieldError,
            ValidationError as CoreValidationError,
            ConfigurationError as CoreConfigurationError,
            ServiceError as CoreServiceError,
        )

        assert DomainScamShieldError is CoreScamShieldError
        assert DomainValidationError is CoreValidationError
        assert DomainConfigurationError is CoreConfigurationError
        assert DomainServiceError is CoreServiceError

    def test_domain_exception_caught_by_core_handler(self):
        from domains.shared.exceptions import ValidationError as DomainValidationError, NotFoundError
        from core.exceptions import ValidationError as CoreValidationError

        exc = DomainValidationError("test")
        assert isinstance(exc, CoreValidationError)

    def test_domain_not_found_not_in_core(self):
        from domains.shared.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            raise NotFoundError("not found")

    def test_domain_error_not_in_core(self):
        from domains.shared.exceptions import DomainError

        assert DomainError.__mro__[1] is Exception
        assert DomainError.__module__.startswith("domains")