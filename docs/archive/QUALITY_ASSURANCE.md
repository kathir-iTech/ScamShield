# Quality Assurance

## Quality Gates

The quality gate (`scripts/quality_gate.py`) runs these checks:

| Check | Description |
|-------|-------------|
| pytest | All tests pass |
| Imports | All modules import successfully |
| Config | Settings load correctly |
| Models | Model artefacts exist |
| OpenAPI | API spec generated correctly |
| Schemas | Response schemas defined |

## Continuous Evaluation

`scripts/continuous_eval.py` extends the quality gate:

- Runs pytest with configurable arguments
- Runs performance benchmarks
- Verifies all module imports
- Evaluates model against benchmark datasets
- Generates versioned evaluation reports

## Quality Dashboard

`scripts/quality_dashboard.py` generates a machine-readable summary:

- Overall quality score (0-100)
- Test count
- Module health percentage
- Evaluation history
- Threshold health
- Latest metrics

## Regression Workflow

1. Run evaluation on baseline:
   ```
   python evaluation/evaluation_runner.py --output reports/baseline/
   ```

2. Run evaluation on current version:
   ```
   python evaluation/evaluation_runner.py --output reports/current/ --compare reports/baseline/metrics.json
   ```

3. If regression detected, the report will highlight:
   - Accuracy drops > 2%
   - Precision drops > 2%
   - FPR increases > 2%

## Target Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Accuracy | 83.3% | >= 90% |
| Precision | 90.4% | >= 95% |
| Recall | 89.8% | >= 95% |
| F1 | 90.1% | >= 95% |
| FPR | 52.0% | < 10% |
| FNR | 10.2% | < 5% |
| Tests | 342 | 400+ |
