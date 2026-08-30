# ScamShield Investigation Report Format

## Overview

The investigation report is the final structured output of the ScamShield analysis pipeline. It consolidates all prior analysis layers into a single comprehensive report.

## Report Structure

### `report_id`
- Type: `string` (UUID v4)
- Description: Unique identifier for each report.
- Generated via: Python `uuid.uuid4()`

### `generated_at`
- Type: `string` (ISO 8601)
- Description: UTC timestamp when the report was generated.
- Format: `2026-07-25T12:00:00.000000+00:00`

### `executive_summary`
- Type: `string` (2–4 sentences)
- Description: Professional-language summary of the investigation outcome.
- Logic: Varies by assessment score band:
  - ≥76: "Immediate action required" tone
  - 51–75: "Investigation warranted" tone
  - 21–50: "Further review suggested" tone
  - ≤20: "No concerns" tone

### `assessment`
- Type: `object`
- Fields:
  - `score` (int, 0–100): Unified assessment score
  - `band` (string): One of the four assessment bands
  - `confidence` (string): HIGH / MEDIUM / LOW
  - `summary` (string): One-line assessment summary

### `scam_category`
- Type: `string`
- Description: Detected scam category (e.g., "Bank KYC Scam", "Lottery Scam", "Unknown Scam")
- Source: Explanation service category engine

### `severity`
- Type: `string`
- Description: Risk severity level (VERY LOW / LOW / MEDIUM / HIGH / CRITICAL)
- Source: Explanation service severity calculator

### `investigation_findings`
- Type: `array` of `string`
- Description: Numbered findings from all analysis layers.
- Min items: 1 (always has at least "No suspicious indicators detected")
- Max items: 12
- Sources: Detected indicators, rule engine reasons, evidence descriptions
- Deduplication: Case-insensitive text deduplication

### `detected_entities`
- Type: `object`
- Fields:
  - `total` (int): Total number of extracted entities
  - `by_type` (object): Entity type → `{count, values[]}`
  - `high_risk_entities` (array): Entities marked as HIGH risk with type
- Source: Threat Intelligence engine

### `evidence_summary`
- Type: `object`
- Fields:
  - `total_items` (int): Total supporting evidence items
  - `high_severity` (int): Count of HIGH severity evidence
  - `medium_severity` (int): Count of MEDIUM severity evidence
  - `by_source` (object): Source → count (ml, rules, explanation, intel, evidence)
  - `key_findings` (array): Descriptions of top high-severity findings

### `technical_analysis`
- Type: `object`
- Fields:
  - `ml_confidence` (float): Raw ML confidence (0–1)
  - `ml_classification` (string): "scam" or "safe"
  - `decision_score` (int): Evidence engine decision score (0–100)
  - `assessment_score` (int): Unified assessment score (0–100)
  - `evidence_count` (int): Number of evidence items
  - `entity_count` (int): Total extracted entities
  - `methodology` (string): Description of the analysis pipeline

### `business_analysis`
- Type: `object`
- Fields:
  - `category` (string): Scam category
  - `likely_attacker_objective` (string): What the attacker aims to achieve
  - `potential_victim_impact` (string): What the victim may suffer
  - `top_risk_factors` (array): `{risk, score}` objects sorted by score
  - `business_impact_summary` (string): Plain-language business reason

### `risk_summary`
- Type: `object`
- Fields:
  - `overall_severity` (string): VER Y LOW / LOW / MEDIUM / HIGH / CRITICAL
  - `risk_scores` (object): Breakdown by risk type (0–100 each)
  - `primary_risk` (string): The risk type with the highest score

### `recommended_actions`
- Type: `array` of `string`
- Description: Actionable steps for the end user
- Logic: Varies by assessment score:
  - ≥91: Block, report, change passwords, monitor accounts
  - 76–90: Do not engage, verify independently
  - 51–75: Do not share info, verify sender
  - 21–50: Exercise caution
  - ≤20: No action required

### `incident_timeline`
- Type: `array` of `object`
- Fields per stage:
  - `stage` (int): Stage number (1–6)
  - `event` (string): Stage name
  - `description` (string): What happened at this stage
- Stages (deterministic):
  1. Message Received
  2. Content Analysed
  3. Entities Extracted
  4. Evidence Correlated
  5. Risk Assessed
  6. Report Generated

### `user_guidance`
- Type: `object`
- Fields:
  - `immediate_actions` (array): Actions to take right now
  - `short_term_actions` (array): Actions to take within 24 hours
  - `long_term_safety_tips` (array): Ongoing safety practices

## Determinism

All report fields except `report_id` and `generated_at` are deterministic given the same input.

## Backward Compatibility

The report is appended as a single `investigation_report` field. All prior fields remain unchanged.
