# ScamShield Evaluation Framework

A professional benchmark suite for measuring ScamShield's detection
performance objectively. Every future AI improvement must be measured
against this framework.

## Directory Structure

```
evaluation/
├── datasets/
│   ├── benchmark.json          # Combined benchmark dataset (162 samples)
│   ├── legitimate/             # Category-specific source samples
│   ├── phishing/
│   ├── upi/
│   ├── banking/
│   ├── job/
│   ├── lottery/
│   ├── investment/
│   ├── delivery/
│   ├── government/
│   ├── qr/
│   └── mixed/
├── labels/                     # Per-sample label exports
├── reports/                    # Generated evaluation reports
├── scripts/
│   ├── schema.py               # Schema definitions + validation
│   ├── build_dataset.py        # Dataset generator
│   ├── report.py               # HTML report generator (inline SVG)
│   └── error_analysis.py       # Error analysis engine
├── evaluation_runner.py        # Main CLI entry point
└── EVALUATION.md               # This file
```

## Dataset Format

Each sample is a JSON object with these fields:

| Field | Required | Type | Description |
|---|---|---|---|
| `id` | Yes | string | Unique identifier (e.g. `bank-kyc-001`) |
| `text` | Yes | string | The message text to classify |
| `expected_prediction` | Yes | string | `scam` or `safe` |
| `expected_category` | Yes | string | Scam category label |
| `expected_risk_level` | Yes | string | CRITICAL / HIGH / MEDIUM / LOW / VERY LOW |
| `expected_decision_level` | Yes | string | CRITICAL / HIGH RISK / SUSPICIOUS / LOW RISK / SAFE |
| `expected_assessment_band` | Yes | string | Assessment band label |
| `expected_entities` | No | array | Entity types expected (e.g. `["url", "bank_name"]`) |
| `expected_confidence_min` | No | float | Minimum expected confidence (0.0–1.0) |
| `expected_confidence_max` | No | float | Maximum expected confidence (0.0–1.0) |
| `difficulty` | Yes | string | `easy`, `medium`, or `hard` |
| `language` | Yes | string | `en`, `ta`, or `tangling` |
| `source_type` | Yes | string | `sms`, `whatsapp`, `email`, `telegram`, `social` |
| `ground_truth_reason` | No | string | Why this is the correct label |
| `notes` | No | string | Additional context |
| `expected_action` | No | string | Recommended action for the sample |
| `expected_priority` | No | string | Priority level |

### Adding Samples

1. Add entries to `scripts/build_dataset.py` following the existing pattern
2. Rebuild the dataset: `python scripts/build_dataset.py`
3. Validate: `python -c "from scripts.schema import validate_dataset; import json; samples = json.load(open('datasets/benchmark.json')); valid, errs, _ = validate_dataset(samples); print(f'{len(samples)} samples, valid={valid}')"`

To add a new category, add the category name to `VALID_CATEGORIES` in `scripts/schema.py`.

## Usage

### Basic Evaluation

```bash
# Run against local backend
python evaluation_runner.py

# Run against a remote API
python evaluation_runner.py --api http://server:8000

# Limit to 10 samples for a quick test
python evaluation_runner.py --sample 10

# Verbose output
python evaluation_runner.py --verbose
```

### Custom Dataset

```bash
python evaluation_runner.py --dataset my_custom_dataset.json
```

### Custom Output

```bash
python evaluation_runner.py --output my_results/
```

## Metrics

| Metric | Definition |
|---|---|
| Accuracy | (TP + TN) / Total |
| Precision | TP / (TP + FP) |
| Recall | TP / (TP + FN) |
| F1 Score | 2 × Precision × Recall / (Precision + Recall) |
| False Positive Rate | FP / (FP + TN) |
| False Negative Rate | FN / (FN + TP) |
| Category Accuracy | Correct category predictions / Correct scam predictions |
| Risk Level Accuracy | Exact risk level match rate |
| Assessment Accuracy | Exact assessment band match rate |
| Average Confidence | Mean confidence score across all predictions |
| Average Inference Time | Mean API response time |
| P95 Latency | 95th percentile inference latency |

## Error Analysis

The framework automatically identifies:

- **False Positives**: Safe messages classified as scam
- **False Negatives**: Scam messages classified as safe
- **Wrong Category**: Correctly identified as scam but wrong category
- **Low Confidence**: Scam predictions below 40% confidence
- **Entity Extraction Failures**: Expected entity types not detected

## Comparing Model Versions

1. Run evaluation on baseline version:
   ```bash
   python evaluation_runner.py --output reports/v1.0.0/
   ```

2. Run evaluation on new version:
   ```bash
   python evaluation_runner.py --output reports/v1.1.0/
   ```

3. Compare metrics side by side:
   ```bash
   python -c "
   import json
   v1 = json.load(open('reports/v1.0.0/metrics.json'))
   v2 = json.load(open('reports/v1.1.0/metrics.json'))
   print(f'{\"Metric\":25s} {\"v1.0.0\":>10s} {\"v1.1.0\":>10s} {\"Change\":>10s}')
   for k in ['accuracy','precision','recall','f1','category_accuracy']:
       if k in v1 and k in v2:
           d = v2[k] - v1[k]
           print(f'{k:25s} {v1[k]:9.1%} {v2[k]:9.1%} {d:+8.1%}')
   "
   ```

## Reports

The HTML report includes:

- Overall metrics dashboard
- Confusion matrix (inline SVG)
- Per-category accuracy bar chart
- Sample count distribution
- Error analysis summary tables
- False positive and false negative examples
- Timestamp and metadata

No external services or JavaScript libraries are required.
