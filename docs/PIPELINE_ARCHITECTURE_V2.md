# Pipeline Architecture v2 — Typed, Registry-Driven Pipeline

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    services/orchestrator.py              │
│  (thin facade — backward compat: analyze_text,          │
│   PipelineError)                                        │
└──────────────┬──────────────────────────────────────────┘
               │ delegates to
               ▼
┌─────────────────────────────────────────────────────────┐
│                 pipeline/PipelineRunner                   │
│  - resolves execution order via registry                 │
│  - executes steps sequentially                           │
│  - handles fatal/non-fatal errors                        │
│  - records telemetry                                     │
└──────────────┬──────────────────────────────────────────┘
               │ orchestrates
               ▼
┌─────────────────────────────────────────────────────────┐
│                 pipeline/StepRegistry                     │
│  - register / get / enable / disable steps               │
│  - topological sort with dependency resolution           │
│  - health check aggregation                              │
└─────────────────────────────────────────────────────────┘

Each step implements AnalysisStep (pipeline/step.py):
  ┌─────────────┐
  │   MLStep    │  priority=10, fatal
  ├─────────────┤
  │  RulesStep  │  priority=20, fatal
  ├─────────────┤
  │ExplnStep    │  priority=30, fatal
  ├─────────────┤
  │  IntelStep  │  priority=40
  ├─────────────┤
  │ EvidenceStep│  priority=50
  ├─────────────┤
  │AssessStep   │  priority=60
  ├─────────────┤
  │RefineStep   │  priority=70
  ├─────────────┤
  │ReasonStep   │  priority=80
  ├─────────────┤
  │ ReportStep  │  priority=90
  ├─────────────┤
  │KnowledgeStep│  priority=100
  ├─────────────┤
  │ConnectStep  │  priority=110
  ├─────────────┤
  │ FusionStep  │  priority=120
  └─────────────┘
```

## File Layout

```
backend/pipeline/
├── __init__.py         # Public API exports (PipelineRunner, PipelineResult, etc.)
├── types.py            # Type aliases, enums (StepStatus, StepHealth, TelemetryEntry)
├── contracts.py        # Protocol interfaces (PipelineStep, StepResult, PipelineContext)
├── exceptions.py       # Typed exception hierarchy (PipelineError, StepExecutionError, etc.)
├── context.py          # PipelineContext — shared state, telemetry recording
├── registry.py         # StepRegistry — register, resolve_order, health_check
├── step.py             # AnalysisStep abstract base class
├── result.py           # PipelineResult — dict accumulator with all default fields
├── pipeline.py         # PipelineRunner — execution engine
└── steps/
    ├── __init__.py
    ├── ml_step.py
    ├── rules_step.py
    ├── explanation_step.py
    ├── intelligence_step.py
    ├── evidence_step.py
    ├── assessment_step.py
    ├── refinement_step.py
    ├── reasoning_step.py
    ├── report_step.py
    ├── knowledge_step.py
    ├── connector_step.py
    └── fusion_step.py
```

## Key Design Decisions

### 1. Typed Step Contracts
Each step declares typed I/O through `StepResult.data` — specific dict keys it produces. The `PipelineResult` merges all step data into a flat dict matching the legacy `AnalysisResult.asdict()` output.

### 2. Dependency Resolution (Topological Sort)
Steps declare `dependencies=[...]` by step_id. The registry performs DFS-based topological sort, detecting circular dependencies, respecting priority as tiebreaker. Missing optional dependencies are silently skipped; missing required dependencies raise `DependencyError`.

### 3. Fatal vs Non-Fatal Errors
- **Fatal steps** (ML, Rules, Explanation): failure raises `PipelineError` (preserved from old `ScamShieldError` base)
- **Non-fatal steps**: failure logs a warning and continues with partial results

### 4. Backward Compatibility
- `services.orchestrator.analyze_text(text: str) -> Dict[str, object]` — unchanged signature
- `services.orchestrator.PipelineError(ScamShieldError)` — unchanged class
- Output dict contains all 60+ keys from old `AnalysisResult.asdict()`
- Side-effect mutations of `investigation_report` in knowledge/connector steps are preserved via shared dict reference

### 5. Telemetry
Each step records `(step_id, status, duration_ms, error, warnings)` into `PipelineContext.telemetry`. The pipeline runner aggregates these into `pipeline_summary.telemetry`. Callers can also subscribe to metrics via `core.metrics.record_stage()`.

## Extension Guide

To add a new pipeline stage:

```python
from pipeline.step import AnalysisStep

class MyNewStep(AnalysisStep):
    def __init__(self):
        super().__init__(
            step_id="my_step",
            name="My New Analysis",
            priority=55,           # insert between existing steps
            dependencies=["evidence"],
            fatal=False,
        )

    def execute(self, context):
        # Access accumulated results: context.shared (flat dict)
        my_data = do_something(context.text, dict(context.shared))
        return self._ok({"my_field": my_data})
```

Then register in `services/orchestrator.py`:

```python
_registry.register(MyNewStep())
```

## Old vs New Comparison

| Aspect | Old (orchestrator.py) | New (pipeline/) |
|--------|----------------------|-----------------|
| Step definition | 12 private functions | 12 typed classes |
| Shared state | `AnalysisResult` dataclass with 60+ fields | `PipelineResult` dict accumulator |
| Error handling | `_try_step` / `_timed_step` wrappers | Registry-level fatal flag |
| Ordering | Hardcoded in `_run_pipeline` | Topological sort via registry |
| Dependencies | Implicit (calling order) | Explicit `dependencies=[...]` |
| Serialization | `asdict()` called 10+ times | Merged once at the end |
| Telemetry | `metrics.record_stage()` in each step | Automatic via `PipelineRunner` |
| Extensibility | Edit `_run_pipeline` + add step function | Register new class in registry |
| Testing steps | Integration-only | Unit-testable in isolation |
