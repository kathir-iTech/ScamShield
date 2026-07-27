# Calibration Guide

## Confidence Thresholds

The system uses three confidence thresholds calibrated for production:

| Band | Threshold | Range |
|------|-----------|-------|
| VERY_LOW | — | 0.00 – 0.39 |
| LOW | 0.4 | 0.40 – 0.59 |
| MEDIUM | 0.6 | 0.60 – 0.79 |
| HIGH | 0.8 | 0.80 – 1.00 |

**Bug Fixed**: `LOW_CONFIDENCE_THRESHOLD` was 0.6 (higher than MEDIUM at 0.5).
Now correctly set to 0.4.

## Scoring Weights

The final score uses five weighted components:

| Component | Weight | Source |
|-----------|--------|--------|
| ML Confidence | 35% | Logistic Regression |
| Rule Score | 25% | Rules Engine |
| Entity Risk | 20% | Entity Extraction |
| Explanation Coherence | 10% | Reasoning Engine |
| Threat Intel | 10% | Intelligence Service |

## FP Reduction Rules

Seven refinement rules detect false positives:

- FP-001: Legitimate banking notification
- FP-002: Government alert
- FP-003: Delivery notification
- FP-004: Legitimate OTP message
- FP-005: Transaction receipt
- FP-006: Subscription reminder
- FP-007: High ML confidence, insufficient evidence

## FN Reduction Rules

Nine refinement rules detect false negatives:

- FN-001: Obfuscated URL
- FN-002: Unicode spoofing
- FN-003: Urgency + payment request
- FN-004: Credential harvesting
- FN-005: Social engineering triad
- FN-006: Fake customer support
- FN-007: QR code payment scam
- FN-008: Investment scam
- FN-009: Obfuscated contact

## Recalibration

To recalibrate thresholds against benchmark data:

```python
from core.calibration import recalibrate_thresholds, optimize_scoring_weights

threshold, fpr, tpr = recalibrate_thresholds(y_true, y_scores, target_fpr=0.10)
best_weights = optimize_scoring_weights(y_true, ml, rule, entity, expl, threat)
```
