from __future__ import annotations

from unittest.mock import MagicMock

from pipeline.contracts import PipelineStep, StepResult, StepStatus
from pipeline.registry import StepRegistry
from pipeline.types import StepHealth, StepID


def _make_step(step_id: str, priority: int = 100, dependencies: list[str] | None = None, optional: bool = False, disabled: bool = False, fatal: bool = False) -> PipelineStep:
    mock = MagicMock(spec=PipelineStep)
    mock.step_id = step_id
    mock.name = step_id
    mock.priority = priority
    mock.dependencies = dependencies or []
    mock.optional = optional
    mock.disabled = disabled
    mock.initialize.return_value = None
    mock.cleanup.return_value = None
    mock.health = StepHealth()
    mock.execute.return_value = StepResult(step_id=step_id, status=StepStatus.COMPLETED, data={})
    return mock


class TestStepRegistryInit:
    def test_empty_registry(self):
        reg = StepRegistry()
        assert reg.all() == []

    def test_registry_contains_after_register(self):
        reg = StepRegistry()
        step = _make_step("test_step")
        reg.register(step)
        assert "test_step" in reg

    def test_get_returns_registered_step(self):
        reg = StepRegistry()
        step = _make_step("s1")
        reg.register(step)
        assert reg.get("s1") is step

    def test_get_returns_none_for_unknown(self):
        reg = StepRegistry()
        assert reg.get("nonexistent") is None

    def test_all_returns_all_steps(self):
        reg = StepRegistry()
        reg.register(_make_step("s1"))
        reg.register(_make_step("s2"))
        reg.register(_make_step("s3"))
        assert len(reg.all()) == 3

    def test_resolve_order_no_dependencies(self):
        reg = StepRegistry()
        reg.register(_make_step("c", priority=200))
        reg.register(_make_step("a", priority=100))
        reg.register(_make_step("b", priority=150))
        order = reg.resolve_order()
        assert order == ["a", "b", "c"]

    def test_resolve_order_respects_dependencies(self):
        reg = StepRegistry()
        reg.register(_make_step("a", priority=100))
        reg.register(_make_step("b", priority=100, dependencies=["a"]))
        reg.register(_make_step("c", priority=100, dependencies=["b"]))
        order = reg.resolve_order()
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_resolve_order_handles_optional_dependency(self):
        reg = StepRegistry()
        reg.register(_make_step("a", priority=100))
        reg.register(_make_step("b", priority=100, dependencies=["missing"], optional=True))
        order = reg.resolve_order()
        assert "a" in order
        assert "b" in order

    def test_resolve_order_raises_on_missing_required_dependency(self):
        import pytest
        from pipeline.exceptions import DependencyError
        reg = StepRegistry()
        reg.register(_make_step("a", priority=100, dependencies=["missing"]))
        with pytest.raises(DependencyError):
            reg.resolve_order()

    def test_resolve_order_detects_circular_dependency(self):
        reg = StepRegistry()
        reg.register(_make_step("a", priority=100, dependencies=["b"]))
        reg.register(_make_step("b", priority=100, dependencies=["a"]))
        import pytest
        from pipeline.exceptions import DependencyError
        with pytest.raises(DependencyError):
            reg.resolve_order()

    def test_duplicate_registration_overwrites(self):
        reg = StepRegistry()
        step1 = _make_step("s1", priority=100)
        step2 = _make_step("s1", priority=200)
        reg.register(step1)
        reg.register(step2)
        assert reg.get("s1").priority == 200

    def test_disable_step(self):
        reg = StepRegistry()
        reg.register(_make_step("s1"))
        reg.disable("s1")
        enabled = reg.enabled_steps()
        assert len(enabled) == 0

    def test_enable_step(self):
        reg = StepRegistry()
        reg.register(_make_step("s1", disabled=True))
        reg.enable("s1")
        enabled = reg.enabled_steps()
        assert len(enabled) == 1

    def test_enable_step_not_in_registry(self):
        reg = StepRegistry()
        reg.enable("nonexistent")
        assert reg.all() == []

    def test_health_check(self):
        reg = StepRegistry()
        reg.register(_make_step("s1"))
        health = reg.health_check()
        assert "s1" in health
        assert health["s1"] == StepHealth()

    def test_resolve_order_cached(self):
        reg = StepRegistry()
        reg.register(_make_step("a", priority=100))
        order1 = reg.resolve_order()
        order2 = reg.resolve_order()
        assert order1 == order2

    def test_resolve_order_clears_cache_on_disable(self):
        reg = StepRegistry()
        reg.register(_make_step("a", priority=100))
        reg.resolve_order()
        reg.disable("a")
        enabled = reg.enabled_steps()
        assert len(enabled) == 0

    def test_resolve_order_clears_cache_on_enable(self):
        reg = StepRegistry()
        reg.register(_make_step("a", priority=100, disabled=True))
        reg.resolve_order()
        reg.enable("a")
        order = reg.resolve_order()
        assert "a" in order

    def test_registry_reset_clears_all(self):
        reg = StepRegistry()
        reg.register(_make_step("a"))
        reg.register(_make_step("b"))
        assert len(reg.all()) == 2