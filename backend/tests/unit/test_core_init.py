import importlib
import sys
from types import ModuleType
from typing import List

import pytest


@pytest.fixture
def core_module() -> ModuleType:
    return importlib.import_module("core")


class TestCoreExports:
    EXPECTED_EXPORTS: List[str] = [
        "StructuredLogger", "logger", "reconfigure",
        "Metrics", "metrics",
        "get_request_id", "get_correlation_id",
        "ScamShieldError", "ValidationError", "ConfigurationError",
        "RequestIDMiddleware",
        "SecurityHeadersMiddleware",
        "SlidingWindowRateLimiter",
        "RequestTimeoutMiddleware", "CircuitBreaker",
        "calibrate_confidence", "confidence_band",
        "APIKeyManager", "get_api_key_manager",
        "get_diagnostics",
        "LogConfig", "load_config",
        "detect_language",
        "EvaluationMetrics",
        "configure_auth", "require_auth", "require_admin",
    ]

    def test_core_has_all(self, core_module: ModuleType) -> None:
        assert hasattr(core_module, "__all__")
        assert isinstance(core_module.__all__, list)
        assert len(core_module.__all__) > 0

    def test_all_exports_are_strings(self, core_module: ModuleType) -> None:
        for name in core_module.__all__:
            assert isinstance(name, str), f"__all__ entry {name!r} is not a string"

    def test_expected_names_importable(self, core_module: ModuleType) -> None:
        for name in self.EXPECTED_EXPORTS:
            assert hasattr(core_module, name), f"{name} not found in core module"

    def test_all_names_are_actually_defined(self, core_module: ModuleType) -> None:
        for name in core_module.__all__:
            assert hasattr(core_module, name), (
                f"__all__ includes {name!r} but it is not defined in core"
            )

    def test_import_star_works(self) -> None:
        mod = importlib.import_module("core")
        names = dir(mod)
        assert "Metrics" in names
        assert "logger" in names
