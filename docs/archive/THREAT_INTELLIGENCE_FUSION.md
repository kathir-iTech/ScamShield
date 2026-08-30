# Multi-Source Threat Intelligence Fusion Engine

## Architecture

The fusion engine sits **above** all threat intelligence connectors. It collects raw connector results and produces a single explainable intelligence verdict.

```
Connectors                          Fusion Layer
┌─────────────────┐               ┌─────────────────────────┐
│ MockThreat       │───results───▶│ Indicator Clustering    │
├─────────────────┤               ├─────────────────────────┤
│ Google Safe      │               │ Deduplication           │
│ Browsing         │───results───▶├─────────────────────────┤
├─────────────────┤               │ Conflict Resolution     │
│ Future Connectors│───results───▶├─────────────────────────┤
└─────────────────┘               │ Evidence Ranking        │
                                  ├─────────────────────────┤
                                  │ Confidence Aggregation  │
                                  ├─────────────────────────┤
                                  │ Fused Verdict           │
                                  └─────────────────────────┘
                                          │
                                          ▼
                                  Pipeline & Report
```

## Fusion Algorithm

### 1. Deduplication
Results are deduplicated by `(source, indicator, indicator_type)` to prevent the same connector from being counted multiple times for the same indicator.

### 2. Indicator Clustering
Related indicators are grouped together. For example, a URL `https://evil.com/phish` and a domain `evil.com` resolve to the same domain cluster.

### 3. Weighted Confidence
Each source has a configurable reliability weight. Overall confidence is computed as:

```
overall_confidence = Σ(weight_i * confidence_i) / Σ(weight_i)
```

### 4. Agreement Score
Measures what fraction of indicators have unanimous verdicts across all consulted sources:

```
agreement_score = agreeing_indicators / total_indicators
```

### 5. Conflict Detection
When one source says malicious and another says clean for the same indicator, a conflict is recorded. Resolution strategy:
- **Higher weight wins** — the source with higher reliability is trusted
- **Equal weight** — matched (malicious) verdict is preferred over unmatched (clean)

### 6. Overall Verdict

| Condition | Verdict | Risk |
|-----------|---------|------|
| No matches | `clean` | `UNKNOWN` |
| >= 50% sources match, confidence >= 0.7, agreement >= 0.5 | `malicious` | `HIGH` |
| >= 30% sources match or confidence >= 0.5 | `suspicious` | `MEDIUM` |
| Otherwise | `clean` | `UNKNOWN` |

## Source Reliability Weights

Configured in `backend/config/settings.py`:

| Source | Weight |
|--------|--------|
| `google_safe_browsing` | 0.90 |
| `mock_threat` | 0.80 |
| *(unknown)* | 0.50 |

Weights are configurable via `FUSION_SOURCE_WEIGHTS` dict. Future connectors can be added without code changes.

## Evidence Ranking

| Rank | Condition |
|------|-----------|
| `critical` | Matched, HIGH/CRITICAL risk, confidence >= 0.8 |
| `strong` | Matched, HIGH/MEDIUM risk, confidence >= 0.6 |
| `supporting` | Matched, any risk/confidence |
| `weak` | Source unavailable (error) |
| `informational` | No threat detected |

## FuseResult Model

| Field | Type | Description |
|-------|------|-------------|
| `overall_verdict` | `str` | `clean`, `suspicious`, or `malicious` |
| `overall_confidence` | `float` | Weighted confidence (0.0 - 1.0) |
| `overall_risk` | `str` | Highest risk across matched sources |
| `contributing_sources` | `List[Dict]` | Each source's weight, verdict, latency |
| `agreement_score` | `float` | 0.0 (total disagreement) - 1.0 (full agreement) |
| `conflict_score` | `float` | 0.0 (no conflicts) - 1.0 (all conflicting) |
| `missing_evidence` | `List[str]` | Indicator types with no connector coverage |
| `evidence_ranking` | `List[Dict]` | All evidence sorted by rank then confidence |
| `conflict_resolution` | `List[Dict]` | Each conflict with resolution explanation |
| `sources_consulted` | `int` | Number of unique sources that responded |
| `matched_sources` | `int` | Number of sources that found threats |

## Report Enrichment

The fusion result is embedded in:
- `AnalysisResponse.threat_intel_fusion` (`Dict`, empty by default)
- `InvestigationResponse.threat_intel_fusion` (`Dict`, empty by default)
- `investigation_report.threat_intel_fusion` — full fusion dict

No API schema changes. All fields are optional with empty defaults.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `FUSION_SOURCE_WEIGHTS` | `{"google_safe_browsing": 0.90, "mock_threat": 0.80}` | Source reliability weights |
| `FUSION_AGREEMENT_THRESHOLD` | `0.5` | Minimum agreement for malicious verdict |
| `FUSION_CONFLICT_THRESHOLD` | `0.3` | Conflict score above this triggers flag |
| `FUSION_MIN_SOURCES` | `1` | Minimum sources needed for verdict |

## Adding a New Source

1. Create a connector implementing `BaseConnector`
2. Add its source name and weight to `FUSION_SOURCE_WEIGHTS`
3. The fusion engine automatically picks it up — no code changes needed

## Failure Handling

- No connectors configured → verdict is `clean`, confidence 0.0
- All connectors fail → verdict is `clean`, sources are listed with their errors
- Partial failures → fusion uses whatever results are available
- Individual connector errors never break the fusion process

## Determinism

The fusion engine is fully deterministic. Given the same set of connector results, the fused verdict will always be identical.
