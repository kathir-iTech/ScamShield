# ScamShield Assessment Engine

## Overview

The Assessment Engine is the final unified risk assessment layer. It consumes all prior analysis layers (ML, Rules, Explanation, Threat Intelligence, Evidence) and produces a single deterministic assessment.

## Scoring Rules

### Assessment Score (0–100)

The score is a weighted composite of 6 components:

| # | Component | Weight | Max Pts | Rule |
|---|-----------|--------|---------|------|
| 1 | ML Alignment | 25% | 25 | If ML says "scam": `25 × confidence`. If "safe": `25 × (1 − confidence)`. Higher confidence in scam = higher score. Low confidence in "safe" also raises score (uncertainty). |
| 2 | Decision Score | 30% | 30 | `30 × (decision_score / 100)`. The Evidence Engine's decision score is the most comprehensive single metric. |
| 3 | Evidence Quality | 20% | 20 | `min(HIGH_count × 5, 15) + min(MED_count × 2, 6)`. More high-severity evidence = higher score. Capped at 20. |
| 4 | Threat Indicators | 10% | 10 | `0→0, 1→4, 2→7, 3→9, 4+→10`. More distinct indicator categories indicate broader attack surface. |
| 5 | Entity Risk | 10% | 10 | `min(HIGH_entities × 3, 6) + min(MED_entities × 2, 4)`. Concrete extracted entities are hard evidence. |
| 6 | Conflict Penalty | −5% | −3 | `min(conflicts × 3, 3)`. Conflicting signals reduce confidence. |

**Formula:**
```
assessment_score = max(0, min(ML + Decision + Evidence + Indicators + Entities − Conflict, 100))
```

## Assessment Bands

| Score Range | Band | Meaning |
|-------------|------|---------|
| 0–20 | Suitable for normal communication | No significant threat detected. Standard handling applies. |
| 21–50 | Further assessment required | Some signals detected but inconclusive. Non-critical monitoring suggested. |
| 51–75 | Suitable for security investigation | Multiple strong indicators. Security team review recommended. |
| 76–100 | Suitable for immediate action | Clear and present threat. Immediate response required. |

**Exactly these four values. No others.**

## Assessment Confidence

| Level | Criteria |
|-------|----------|
| HIGH | ML confidence > 0.8 AND overall confidence ≥ 60 AND no conflicts |
| MEDIUM | ML confidence > 0.5 OR overall confidence ≥ 40 |
| LOW | ML confidence ≤ 0.5 AND overall confidence < 40 |

## Manual Review Logic

`review_required = true` when any condition below is met:

| Condition | Reason |
|-----------|--------|
| ML confidence > 0.7 AND conflicting evidence exists | High ML confidence but rules/entities disagree |
| Scam category is "Unknown Scam" AND score ≥ 21 | Message flagged but unclassifiable |
| Assessment confidence is LOW AND score ≥ 21 | Low confidence despite elevated score |
| ML says "scam" with confidence < 0.6 AND rule label is "low" | Neither ML nor rules are confident |

Otherwise `review_required = false`.

`manual_review_reason` is only populated when `review_required = true`.

## Recommended Action

| Score | Action |
|-------|--------|
| 0–20 | Ignore |
| 21–50 | Monitor |
| 51–75 | Verify independently |
| 76–90 | Do not interact |
| 91–100 | Block and report |

## Decision Tree

```
Input: ML + Rules + Explanation + Intel + Evidence
                │
                ▼
          ML Alignment? ───► 25 pts max
          Decision Score? ──► 30 pts max
          Evidence Qual? ───► 20 pts max
          Indicators? ──────► 10 pts max
          Entity Risk? ─────► 10 pts max
          Conflicts? ───────► −3 pts max
                │
                ▼
        Assessment Score (0-100)
                │
                ▼
       ┌────────┴────────┐
       │                 │
   0-20               21-50
   Normal Comm.       Further
       │             Assessment
   51-75                │
   Security         76-100
   Investigation    Immediate
       │             Action
       ▼
   Assessment Confidence (HIGH/MEDIUM/LOW)
       │
       ▼
   Manual Review Required? (true/false)
       │
       ▼
   Recommended Action (Ignore/Monitor/Verify/Do not interact/Block and report)
```

## Input Sources

| Source | Key Fields Used |
|--------|-----------------|
| ML | `prediction`, `confidence` |
| Rules | `rule_score`, `rule_label`, `reasons` |
| Explanation | `scam_category`, `detected_indicators`, `risk_level` |
| Threat Intelligence | `entities`, `entity_summary`, `entity_risk` |
| Evidence | `decision_score`, `supporting_evidence`, `conflicting_evidence`, `confidence_breakdown` |

## Output Schema

```json
{
  "assessment_score": 87,
  "assessment_band": "Suitable for immediate action",
  "assessment_confidence": "HIGH",
  "assessment_summary": "Urgent: Bank KYC Scam. Immediate action required.",
  "business_reason": "This message is part of a bank kyc scam and poses an immediate threat.",
  "technical_reason": "Assessment based on ML model identifies scam patterns (24/25); ...",
  "recommended_action": "Do not interact",
  "review_required": false,
  "manual_review_reason": ""
}
```

## Design Principles

- **Deterministic**: Same input always produces same output. No randomness.
- **Offline**: No external APIs, no LLMs, no network calls.
- **Documented weights**: Every scoring rule is documented above.
- **Backward compatible**: All prior output fields remain untouched.
- **Single final score**: `assessment_score` is the authoritative risk score.
