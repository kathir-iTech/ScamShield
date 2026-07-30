import importlib
import os
import sys
from types import ModuleType

import pytest


@pytest.fixture
def quality_gate() -> ModuleType:
    base = os.path.join(os.path.dirname(__file__), "..", "..")
    sys.path.insert(0, base)
    qg = importlib.import_module("scripts.quality_gate")
    return qg


class TestQualityGateFunctions:
    def test_all_check_functions_exist(self, quality_gate: ModuleType) -> None:
        check_funcs = [
            "_check_pytest",
            "_check_imports",
            "_check_config_loads",
            "_check_models_exist",
            "_check_openapi",
            "_check_response_schemas",
            "_check_documentation_exists",
            "_check_no_circular_imports",
            "_check_no_duplicated_constants",
        ]
        for name in check_funcs:
            assert hasattr(quality_gate, name), f"{name} not found in quality_gate"
            func = getattr(quality_gate, name)
            assert callable(func), f"{name} is not callable"

    def test_all_check_functions_return_bool(self, quality_gate: ModuleType) -> None:
        check_funcs = [
            "_check_pytest",
            "_check_imports",
            "_check_config_loads",
            "_check_models_exist",
            "_check_openapi",
            "_check_response_schemas",
            "_check_documentation_exists",
            "_check_no_circular_imports",
            "_check_no_duplicated_constants",
        ]
        for name in check_funcs:
            func = getattr(quality_gate, name)
            import typing
            hints = typing.get_type_hints(func)
            assert "return" in hints, f"{name} missing return type hint"
            assert hints["return"] == bool, f"{name} return type hint is {hints['return']}, expected bool"

    def test_main_exists_and_returns_int(self, quality_gate: ModuleType) -> None:
        assert hasattr(quality_gate, "main")
        assert callable(quality_gate.main)
        import typing
        hints = typing.get_type_hints(quality_gate.main)
        assert "return" in hints
        assert hints["return"] == int

    def test_documentation_files_referenced_exist(self, quality_gate: ModuleType) -> None:
        base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        parent = os.path.dirname(base)
        required_docs = [
            "ARCHITECTURE_REVIEW.md",
            "PRODUCTION_HARDENING.md",
            "ENGINEERING_DECISIONS.md",
            "RELEASE_READINESS.md",
        ]
        for doc in required_docs:
            path = os.path.join(base, doc)
            if not os.path.isfile(path):
                path = os.path.join(parent, doc)
            assert os.path.isfile(path), f"Documentation file not found: {doc}"


class TestQualityGateMain:
    def test_main_runs(self, quality_gate: ModuleType) -> None:
        result = quality_gate.main()
        assert isinstance(result, int)
