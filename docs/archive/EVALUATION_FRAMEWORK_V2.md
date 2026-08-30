# Evaluation Framework V2

## Overview

ScamShield Evaluation Framework V2 provides deterministic, auditable, and
reproducible evaluation of detection quality across all pipeline stages.

## Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| Accuracy | (TP + TN) / Total | >= 90% |
| Precision | TP / (TP + FP) | >= 95% |
| Recall | TP / (TP + FN) | >= 95% |
| F1 | 2 x P x R / (P + R) | >= 95% |
| FPR | FP / (FP + TN) | < 10% |
| FNR | FN / (FN + TP) | < 5% |
| MCC | Matthews Correlation Coefficient | > 0.8 |
| Balanced Accuracy | (Recall + Specificity) / 2 | > 0.9 |

## Components

- `core/evaluation_v2.py` — Programmatic evaluation API with EvaluationMetrics
- `core/calibration.py` — Confidence calibration and threshold optimization
- `core/dataset_manager.py` — Dataset versioning and integrity verification
- `core/multilingual.py` — Language detection and Tanglish/Tamil preprocessing
- `evaluation/evaluation_runner.py` — CLI evaluation against benchmark datasets

## Usage

```python
from core.evaluation_v2 import EvaluationMetrics, evaluate_classification

metrics = EvaluationMetrics(y_true, y_pred, y_scores)
print(metrics.summary())

result = evaluate_classification(classifier_fn, samples)
print(result["summary"])
```

## Regression Detection

```python
from core.evaluation_v2 import regression_check

issues = regression_check(baseline_metrics, current_metrics)
if not issues["passed"]:
    for issue in issues["issues"]:
        print(f"REGRESSION: {issue}")
```

## Quality Gate

```bash
python scripts/continuous_eval.py --dataset evaluation/datasets/benchmark.json --check
```
