# ScamShield Refinement Engine

## Architecture

The Refinement Engine is a post-assessment review layer that reduces false
positives and false negatives through deterministic, explainable rules. It
operates after the Assessment step in the pipeline and before Report
generation.

```
ML Prediction -> Rule Engine -> Explanation -> Intel -> Evidence
  -> Assessment -> Refinement -> Report
```

### Components

| Component | File | Purpose |
|-----------|------|---------|
| Refinement Service | `backend/services/refinement_service.py` | Core engine with FP/FN rules |
| Rule Definitions | `refinement_service.py` | All refinement rules with metadata |
| Pipeline Integration | `backend/services/orchestrator.py` | `_step_refinement` in `_run_pipeline` |
| API Schema | `backend/schemas/responses.py` | Optional refinement fields (backward compatible) |
| Constants | `backend/core/constants.py` | Refinement constants and thresholds |
| Settings | `backend/config/settings.py` | Configurable weights, thresholds, regression params |

### Data Flow

1. **Input**: Preliminary assessment dict (from assessment_service) + full analysis dict
2. **Processing**: Check all FP rules -> Check all FN rules -> Apply adjustments -> Check decision stability
3. **Output**: RefinementResult with refined prediction, score, confidence, summary

## Rule Lifecycle

### Structure

Each rule has:

```
rule_id: str          -- Unique identifier (e.g., "FP-001")
description: str      -- Human-readable purpose
category: str         -- fp_reduction | fn_reduction | stability
priority: str         -- HIGH | MEDIUM | LOW
confidence_impact: float  -- Impact on confidence (-0.20 to +0.25)
condition: Callable   -- Deterministic function returning bool
reason: str           -- Traceable explanation
```

### Adding a New Rule

1. Add a condition function in `refinement_service.py`
2. Add a `RefinementRule` instance to `FP_RULES` or `FN_RULES`
3. Add to `ALL_RULES` (automatic via concatenation)
4. (Optional) Add new entity/entity constants if needed
5. Update tests

### Rule IDs

- **FP-001 to FP-007**: False Positive reduction rules
- **FN-001 to FN-009**: False Negative reduction rules

## Error Analysis

### Automated Profiling

The `profile_errors()` function in `refinement_service.py` analyzes evaluation
output and categorises errors:

- **FP by category**: Which categories produce the most false positives
- **FN by category**: Which categories produce the most false negatives
- **Obfuscated URL rate**: FN samples with URL obfuscation
- **Urgency+Payment rate**: FN samples with combined urgency and payment
- **Fake Support rate**: FN samples with customer care impersonation
- **Category confusions**: Expected vs actual category mismatches
- **Entity extraction gaps**: Which entity types are most commonly missed

### Running Error Analysis

```bash
python evaluation/evaluation_runner.py --dataset evaluation/datasets/benchmark.json
```

Results are saved to `evaluation/reports/eval_<timestamp>/error_analysis.json`.

## Refinement Process

### Step 1: Profile Assessment

The engine receives the preliminary assessment containing:
- ML prediction + confidence
- Rule score + label
- Detected indicators and entities
- Evidence items (supporting + conflicting)
- Assessment score, band, confidence

### Step 2: Apply FP Reduction Rules

Each FP rule is evaluated in order. If a rule's condition matches:
- Assessment score is reduced by a configurable amount
- Rule details are logged with rule_id, description, reason
- Total FP adjustment is capped at 30 points

#### FP Rules

| ID | Description | Trigger | Impact |
|----|-------------|---------|--------|
| FP-001 | Legitimate banking notification | Bank name + transaction phrase, no phishing | -15 pts |
| FP-002 | Government alert | Govt reference, no payment/URL | -15 pts |
| FP-003 | Delivery notification | Tracking keywords, no payment/URL | -15 pts |
| FP-004 | Legitimate OTP | OTP code present, no sharing request, no URL | -11 pts |
| FP-005 | Transaction receipt | Transaction ref, no payment/URL/threat | -15 pts |
| FP-006 | Subscription reminder | Subscription keywords, no threat/URL | -11 pts |
| FP-007 | High ML conf, no evidence | Confident scam but 0-1 indicators, 0 entities, low rule score | -8 pts |

### Step 3: Apply FN Reduction Rules

Each FN rule is evaluated in order. If a rule's condition matches:
- Assessment score is increased by a configurable amount
- Rule details are logged
- Total FN adjustment is capped at 30 points

#### FN Rules

| ID | Description | Trigger | Impact |
|----|-------------|---------|--------|
| FN-001 | Obfuscated URL | bit[dot]ly, hxxp://, "click here" patterns | +19 pts |
| FN-002 | Unicode spoofing | Non-ASCII chars in domain-like patterns | +15 pts |
| FN-003 | Urgency + Payment | Immediate action + money request combo | +15 pts |
| FN-004 | Credential harvesting | OTP/password/Aadhaar/bank detail requests | +19 pts |
| FN-005 | Social engineering triad | Threat + reward + call-to-action | +11 pts |
| FN-006 | Fake customer support | Customer care phrase + phone number | +11 pts |
| FN-007 | QR payment scam | QR code + payment request | +15 pts |
| FN-008 | Investment scam | Investment + guaranteed returns + urgency | +15 pts |
| FN-009 | Obfuscated contact | Email/contact with [at], [dot] patterns | +11 pts |

### Step 4: Prediction Override

**FP override**: If total FP adjustment >= 15 and no FN rules fired and
refined score < 40, prediction flips to "safe".

**FN override**: If total FN adjustment >= 20 and no FP rules fired and
refined score >= 51, prediction flips to "scam".

### Step 5: Decision Stability Check

Evaluates whether small input changes could alter the classification:

- Assessment score within 3 points of any decision boundary (20, 40, 65, 85)
- ML confidence near 0.5 threshold (0.45 - 0.55)

Flags stability concerns when detected.

### Step 6: Output

Returns `RefinementResult` containing:
- `refined_prediction`: Potentially corrected prediction
- `refined_assessment_score`: Adjusted score (0-100)
- `refined_assessment_confidence`: HIGH/MEDIUM/LOW
- `refined_review_required`: True if stability concerns
- `decision_stable`: Boolean flag
- `stability_concerns`: List of human-readable concerns
- `applied_rules`: Full trace of applied rules
- `refinement_summary`: Concise text summary

## False Positive Reduction Strategy

Target patterns generalised to avoid hard-coding:

1. **Legitimate communications** that share vocabulary with scams (bank
   notifications, OTP messages, delivery updates)
2. **Government/public service messages** with scheme information
3. **Transaction receipts** and account alerts without phishing indicators
4. **High-confidence ML predictions** that lack supporting evidence

Pattern matching relies on the ABSENCE of phishing indicators (suspicious
URLs, payment requests, account threats) combined with the PRESENCE of
legitimate context keywords.

## False Negative Reduction Strategy

Target patterns that evade detection:

1. **Evasion techniques**: Obfuscated URLs, Unicode spoofing, obfuscated
   contact info
2. **Social engineering**: Threat+reward+CTA triad, fear tactics
3. **Credential harvesting**: Direct requests for sensitive data
4. **Emerging scam patterns**: QR payment scams, fake support
5. **Cross-signal patterns**: Urgency + payment, investment + guarantees

## Decision Stability

The engine evaluates classification confidence near decision boundaries.

### Vulnerability Categories

| Category | Detection | Mitigation |
|----------|-----------|------------|
| Whitespace | Score near boundary | Flagged for review |
| Capitalisation | Score near boundary | Flagged for review |
| Emoji | Score near boundary | Flagged for review |
| Punctuation | Score near boundary | Flagged for review |
| Minor spelling | Confidence near 0.5 | Flagged for review |

These are flagged rather than automated to avoid over-fitting to specific
input variations.

## Benchmark and Regression Safety

### Running a Comparison

```bash
# Run baseline evaluation
python evaluation/evaluation_runner.py --dataset evaluation/datasets/benchmark.json --output evaluation/reports/baseline

# Run evaluation with refinement (after changes)
python evaluation/evaluation_runner.py --dataset evaluation/datasets/benchmark.json --output evaluation/reports/refined --compare evaluation/reports/baseline/metrics.json
```

### Regression Thresholds

| Metric | Default Threshold | Description |
|--------|-------------------|-------------|
| Accuracy | -0.02 (2% drop) | Maximum acceptable accuracy decrease |
| Precision | -0.02 (2% drop) | Maximum acceptable precision decrease |
| Recall | -0.02 (2% drop) | Maximum acceptable recall decrease |
| F1 | -0.02 (2% drop) | Maximum acceptable F1 decrease |
| False Positives | +1 | Maximum acceptable FP increase |
| False Negatives | +1 | Maximum acceptable FN increase |
| P95 Latency | +50ms | Maximum acceptable latency increase |

Custom thresholds can be passed via `--regression-thresholds`:

```bash
--regression-thresholds '{"accuracy": 0.01, "fp": 2}'
```

### Regression Safety Enforcement

The evaluation runner performs the following checks:

1. Accuracy decrease > threshold -> FAIL
2. Precision decrease > threshold -> FAIL
3. Recall decrease > threshold -> FAIL
4. F1 decrease > threshold -> FAIL
5. False Positives increase > threshold -> FAIL
6. False Negatives increase > threshold -> FAIL
7. P95 Latency increase > threshold -> FAIL

If any check fails, the evaluation summary displays FAILED with details.
The process continues but the regression failure is clearly documented.

## Configuration

All refinement parameters are configurable via `backend/config/settings.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| REFINEMENT_ENABLED | True | Master switch |
| REFINEMENT_FP_IMPACT_PER_RULE | 0.15 | FP impact multiplier |
| REFINEMENT_FN_IMPACT_PER_RULE | 0.15 | FN impact multiplier |
| REFINEMENT_MAX_FP_TOTAL | 30 | Max total FP adjustment (points) |
| REFINEMENT_MAX_FN_TOTAL | 30 | Max total FN adjustment (points) |
| REFINEMENT_SCORE_OVERRIDE_THRESHOLD | 15 | Min FP adjustment for prediction override |
| REFINEMENT_FLIP_THRESHOLD_SCORE | 40 | Score below which safe override triggers |
| REFINEMENT_FN_FLIP_THRESHOLD_SCORE | 51 | Score above which scam override triggers |
| REFINEMENT_FN_FLIP_ADJUSTMENT_MIN | 20 | Min FN adjustment for prediction override |
| REFINEMENT_BOUNDARY_PROXIMITY | 3 | Points from boundary to flag stability concern |
| REFINEMENT_CONFIDENCE_NEAR_THRESHOLD_LOW | 0.45 | Low end of confidence instability range |
| REFINEMENT_CONFIDENCE_NEAR_THRESHOLD_HIGH | 0.55 | High end of confidence instability range |

## Future Tuning Strategy

1. **Rule weight calibration**: Use evaluation results to adjust
   confidence_impact values for each rule
2. **Category-specific rules**: Add rules targeted at specific scam
   categories with high error rates
3. **Adaptive thresholds**: Adjust boundary proximity based on historical
   evaluation data
4. **Active learning loop**: Periodically re-evaluate and tune rules using
   the benchmark dataset
5. **A/B testing**: Run pipeline with/without refinement and compare
   metrics
6. **New evasion techniques**: Continuously monitor for new obfuscation
   patterns and add rules

## Validation

### Test Commands

```bash
# Backend unit tests
cd backend && python -m pytest tests/ -v --tb=short

# Evaluation framework
cd evaluation && python evaluation_runner.py --dataset datasets/benchmark.json --sample 5

# Full benchmark with comparison
cd evaluation && python evaluation_runner.py --dataset datasets/benchmark.json --output reports/baseline
python evaluation_runner.py --dataset datasets/benchmark.json --output reports/refined --compare reports/baseline/metrics.json
```
