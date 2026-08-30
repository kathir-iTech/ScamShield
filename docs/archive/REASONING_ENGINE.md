# ScamShield Multi-Evidence Reasoning Engine

## Architecture

The Reasoning Engine is a post-refinement reasoning layer that constructs a
unified evidence model from all pipeline signals, classifies into a
hierarchical scam family taxonomy, and generates an auditable decision
trace.

```
ML Prediction -> Rule Engine -> Explanation -> Intel -> Evidence
  -> Assessment -> Refinement -> Reasoning -> Report
```

### Components

| Component | File | Purpose |
|-----------|------|---------|
| Reasoning Service | `backend/services/reasoning_service.py` | Evidence graph, family classification, decision trace |
| Evidence Graph | `reasoning_service.py` | `EvidenceNode`, `EvidenceEdge` dataclasses |
| Family Taxonomy | `reasoning_service.py` | `SCAM_FAMILY_TAXONOMY` hierarchy |
| Pipeline Integration | `backend/services/orchestrator.py` | `_step_reasoning` in `_run_pipeline` |
| API Schema | `backend/schemas/responses.py` | Optional reasoning fields (backward compatible) |
| Constants | `backend/core/constants.py` | Family and subfamily constants |
| Report | `backend/services/report_service.py` | Internal reasoning section in investigation report |

### Data Flow

1. **Input**: Full analysis dict + assessment dict + optional refinement result
2. **Processing**:
   a. Collect evidence nodes from all pipeline stages
   b. Build directed edges (supports, contradicts, strengthens, weakens, duplicates)
   c. Classify into scam family/subfamily using category + indicators
   d. Rank evidence by importance weight
   e. Generate decision trace
3. **Output**: ReasoningResult with family, evidence ranks, graph, trace

## Evidence Graph Model

### Nodes

Nodes represent individual pieces of evidence collected from pipeline
outputs. Each node has:

| Field | Type | Description |
|-------|------|-------------|
| node_id | str | Unique identifier (n_001, n_002, ...) |
| node_type | str | Type classification (ml_prediction, rule_score, indicator, entity, url, phone, email, upi, bank, government, conflict, correlation) |
| label | str | Human-readable summary (truncated to 80 chars) |
| severity | str | HIGH, MEDIUM, LOW |
| weight | float | Numeric importance (0-20) |
| confidence | float | Confidence in evidence accuracy (0-1) |
| source | str | Pipeline origin (ml, rules, explanation, intel, evidence) |

Node types are derived from:
- **Supporting evidence** items (from `evidence_service.build_evidence`)
- **Conflicting evidence** items (from `evidence_service.detect_conflicts`)
- **Entity types** (from `intelligence_service.analyze`)
- **Detected indicators** (from `explanation_service.generate_explanation`)

### Edges

Edges represent relationships between evidence nodes:

| Relationship | Direction | Weight Range | Description |
|-------------|-----------|-------------|-------------|
| supports | bidirectional | 0.1-0.2 | General supporting connection |
| contradicts | bidirectional | 0.3 | Conflicting signals |
| strengthens | directional | 0.4-0.85 | One signal amplifies another |
| weakens | directional | 0.3 | One signal reduces another |
| duplicates | bidirectional | 0.2 | Same evidence type detected twice |

#### Edge Detection Rules

| Pattern | Condition | Relationship | Weight |
|---------|-----------|-------------|--------|
| Conflict node | node type is "conflict" | contradicts | 0.3 |
| Same type | identical node_type | duplicates | 0.2 |
| ML+Rule/Indicator | ml_prediction + rule_score/indicator | strengthens | 0.4 |
| Indicator+Correlation | indicator + correlation | strengthens | 0.4 |
| Urgency+Payment+URL | all three detected | strengthens | 0.8 |
| Bank+URL+OTP | bank + url + otp indicators | strengthens | 0.85 |
| Government+URL | govt reference + url | strengthens | 0.6 |
| QR+Payment | qr code + payment request | strengthens | 0.75 |

### Graph Construction

```python
# Pseudo-code for graph building
nodes = _build_evidence_nodes(supporting, conflicting, entities, indicators)
edges = _build_edges(nodes, node_types, indicators, entities)
graph = {"nodes": nodes[:20], "edges": edges[:30]}
```

The graph is capped at 20 nodes and 30 edges for performance.

## Scam Family Taxonomy

### Hierarchy

```
Financial Fraud
├── Banking              Bank KYC Scam, Account Suspension, OTP Scam
├── UPI                  UPI Scam, QR Code Scam
├── Loan                 Loan Scam
├── Investment           Investment Scam
└── Crypto               Crypto Scam

Credential Theft
├── KYC                  Bank KYC Scam, Phishing
├── OTP                  OTP Scam
├── Fake Login           Phishing
└── Identity Theft       Government Scheme Scam, Job Scam

Social Engineering
├── Fake Support         Fake Customer Care, Fake Support
├── Government           Government Scheme Scam
├── Delivery             Courier Scam
└── Customs              Customs Scam

Consumer Fraud
├── Lottery              Lottery Scam
├── Subscription         Subscription Scam, Electricity Bill Scam
└── Prize                Lottery Scam

Legitimate
└── Safe                 Legitimate
```

### Classification Algorithm

1. Collect the detected scam category and indicators
2. Score each family based on matching indicators (20 pts each)
3. Boost families where the detected category matches a subfamily (35 pts)
4. Apply 0.5x penalty for unknown categories
5. Select the highest-scoring family
6. Within the winning family, select the best subfamily
7. Boost confidence if ML prediction is "scam"
8. Return family, subfamily, and confidence (0-1)

```
family_score = sum(indicator_matches * 20) + (category_match ? 35 : 0)
family_confidence = family_score / total_score
```

## Cross-Evidence Reasoning

### Pattern Detection

The engine detects compound evidence patterns:

| Pattern | Signals | Classification |
|---------|---------|---------------|
| Banking Scam | Bank impersonation + Suspicious URL + Urgency | Strengthens (weight 0.85) |
| Credential Theft | Bank + URL + OTP request | Strengthens (weight 0.85) |
| Phishing | Government reference + URL | Strengthens (weight 0.6) |
| QR Scam | QR code + Payment request | Strengthens (weight 0.75) |
| Urgent Payment | Urgency + Payment + URL | Strengthens (weight 0.8) |

### Contradiction Resolution

When conflicting evidence is detected:
- Contradictory nodes are marked in the evidence graph
- A contradiction penalty reduces family confidence
- The decision trace records the conflict with explanation
- The final summary notifies users of contradictory signals

```python
conf_adjustment = 0.0
contradiction_penalty = min(contradiction_count * 0.05, 0.2)
```

### Evidence Weighting

Each evidence node's importance is computed as:

```
importance = weight * confidence * severity_multiplier
where severity_multiplier = 1.5 for HIGH severity
```

Evidence is ranked into tiers:

| Tier | Threshold | Description |
|------|-----------|-------------|
| Primary | >= 8.0 | Core evidence driving classification |
| Supporting | >= 4.0 | Corroborating evidence |
| Weak | < 4.0 (new type) | Low-confidence or tangential |
| Contradictory | conflict type | Evidence conflicting with main finding |
| Ignored | < 4.0 (duplicate type) | Duplicate or redundant evidence |

## Decision Trace

The expanded decision trace records:

### Reasoning Steps

| Step | Action | Detail |
|------|--------|--------|
| 1 | Evidence collection | Total nodes collected |
| 2 | Relationship detection | Total edges identified |
| 3 | Family classification | Family > Subfamily + confidence |
| 4 | Evidence ranking | Counts per tier |
| 5 | Contradiction resolution | Penalty applied (if any) |

### Trace Output

```json
{
  "reasoning_steps": [...],
  "graph_summary": {
    "total_nodes": 15,
    "total_edges": 22,
    "node_types": {"ml_prediction": 1, "indicator": 5, ...},
    "edge_relationships": {"supports": 12, "strengthens": 6, ...}
  },
  "dominant_evidence": [
    "ML model classifies message as 'scam' with 95% confidence",
    "Rule engine score: 80/100 (high risk)"
  ],
  "discarded_evidence": [...],
  "evidence_chain": [...],
  "confidence_adjustments": {
    "family_classification": 0.85,
    "contradiction_penalty": -0.05,
    "evidence_strength_bonus": 0.05,
    "net_assessment_impact": 0.0
  }
}
```

## Evidence Importance Ranking

### Classification Output

The reasoning service returns evidence classified into five categories:

- **Primary Evidence**: High-importance items driving the classification
- **Supporting Evidence**: Corroborating items that reinforce the finding
- **Weak Evidence**: Low-confidence or tangential signals
- **Contradictory Evidence**: Items that conflict with the main finding
- **Ignored Evidence**: Duplicate or redundant signals

### Example

For a Bank KYC scam message:

```
Primary:
  - ML prediction: scam (0.95)
  - Rule engine: high risk (80/100)

Supporting:
  - Indicator: OTP Request
  - Indicator: Bank Impersonation
  - Entity: URL (suspicious_tld)

Contradictory:
  - (none)

Weak:
  - Indicator: Urgency Language

Ignored:
  - Entity: bank_name (duplicate)
```

## Report Integration

The reasoning output is embedded in the investigation report's assessment
section (without changing the API contract):

```json
{
  "assessment": {
    "score": 76,
    "band": "Suitable for immediate action",
    "confidence": "HIGH",
    "summary": "...",
    "reasoning": {
      "family_classification": {
        "family": "Financial Fraud",
        "subfamily": "Banking",
        "confidence": 0.85
      },
      "dominant_evidence_chain": [
        "ML model classifies message as 'scam' with 95% confidence",
        "Rule engine score: 80/100 (high risk)"
      ],
      "primary_evidence_count": 3,
      "supporting_evidence_count": 5
    }
  }
}
```

## Benchmark Metrics

The evaluation framework tracks family and subfamily accuracy in addition
to standard metrics:

### Family Mapping

| Category | Expected Family |
|----------|----------------|
| Bank KYC Scam | Financial Fraud |
| UPI Scam | Financial Fraud |
| Lottery Scam | Consumer Fraud |
| Courier Scam | Social Engineering |
| ... | ... |

### Subfamily Mapping

| Category | Expected Subfamily |
|----------|-------------------|
| Bank KYC Scam | Banking |
| UPI Scam | UPI |
| Fake Customer Care | Fake Support |
| ... | ... |

### Running with Family Metrics

```bash
python evaluation_runner.py --dataset datasets/benchmark.json
```

Output includes:
```
Family Acc:       92.0%
Subfamily Acc:    88.0%
```

## Configuration

All reasoning parameters are configurable via `backend/config/settings.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| REASONING_EVIDENCE_HIGH_THRESHOLD | 8.0 | Importance threshold for primary evidence |
| REASONING_EVIDENCE_MEDIUM_THRESHOLD | 4.0 | Importance threshold for supporting evidence |
| REASONING_MAX_PRIMARY_EVIDENCE | 5 | Max primary evidence items returned |
| REASONING_MAX_SUPPORTING_EVIDENCE | 8 | Max supporting evidence items |
| REASONING_MAX_WEAK_EVIDENCE | 5 | Max weak evidence items |
| REASONING_MAX_CONTRADICTORY_EVIDENCE | 5 | Max contradictory evidence items |
| REASONING_FAMILY_INDICATOR_WEIGHT | 20.0 | Weight per indicator match in family scoring |
| REASONING_FAMILY_CATEGORY_BOOST | 35.0 | Boost when category matches a subfamily |
| REASONING_UNKNOWN_CATEGORY_PENALTY | 0.5 | Penalty multiplier for unknown categories |

## Future Extensions

1. **Temporal evidence tracking**: Correlate evidence over time across
   multiple messages from the same sender
2. **Dynamic graph pruning**: Remove edges below confidence threshold
3. **Rule-based graph patterns**: Add more compound evidence patterns
   as new scam variants emerge
4. **Confidence propagation**: Propagate confidence through graph edges
   using belief propagation
5. **Evidence provenance**: Track which pipeline stage generated each
   evidence node for audit trails
6. **Cross-message reasoning**: Link evidence across related messages
   for coordinated campaign detection
