# ScamShield Investigation Engine

Multi-message investigation engine that correlates evidence across multiple artefacts (SMS, WhatsApp, email, screenshots, etc.) to detect coordinated campaigns, reconstruct timelines, build relationship graphs, and produce a unified global risk assessment.

## Architecture

```
POST /analyze/investigation
  └─ investigate(artefacts)          # Entry point
       ├─ _validate_artefacts()       # Normalise artefacts
       ├─ _analyse_artefacts()        # Run pipeline on each
       ├─ _merge_entities()           # Cross-message entity dedup
       ├─ _detect_repeated_indicators()
       ├─ _build_timeline()           # Chronological event sequence
       ├─ _detect_campaign()          # Shared-entity pattern detection
       ├─ _build_relationship_graph() # Node-edge graph
       ├─ _compute_global_risk()      # Unified risk score
       └─ _build_investigation_summary()
```

## Entity Merging

Entities are normalised and deduplicated across artefacts:

| Entity Type   | Normalisation                          |
|---------------|----------------------------------------|
| URL           | Lowercased, trailing slash stripped    |
| Phone         | Digits only, last 10 digits            |
| Email         | Lowercased                             |
| UPI ID        | Lowercased                             |
| Bank/IFSC     | Lowercased                             |

Each merged entity tracks: `occurrences`, `first_seen_artefact`, `sources` (artefact indices), `max_risk`.

## Timeline Reconstruction

Automatically generated event types from each artefact's analysis:

- `message_received` — Artefact submitted for analysis
- `classification` — Prediction with score and category
- `link_shared` — Suspicious/Shortened URL detected
- `payment_requested` — Payment indicator detected
- `otp_requested` — OTP/verification request detected
- `threat_escalation` — Account threat/suspension warning
- `identity_requested` — KYC/identity document request
- `qr_requested` — QR code scan request
- `high_risk_entity` — High-risk entities present

## Campaign Detection

A campaign is detected when 2+ artefacts share entities or patterns:

- **Shared phone numbers** across artefacts (+0.20)
- **Shared domains/URLs** across artefacts (+0.15)
- **Shared UPI IDs** across artefacts (+0.20)
- **Shared email addresses** (+0.10)
- **Shared bank details** (+0.15)
- **Same scam family** across all artefacts (+0.25)
- **Repeated wording** (>30% word overlap) (+0.15)
- **Per shared entity** (+0.05 each, max +0.20)

Campaign threshold: **>= 0.30 confidence** → `campaign_detected: true`

## Relationship Graph

Nodes: `artefact`, `entity`, `campaign`, `indicator`
Edges: `mentions`, `belongs_to_campaign`

Max 30 nodes / 40 edges per investigation.

## Global Risk Assessment

```
overall_score = peak_score * 0.6 + avg_score * 0.4 + campaign_boost
```

Where `campaign_boost = 0.15` if campaign detected.

Risk bands:
- **CRITICAL**: >= 76
- **HIGH**: 51–75
- **MEDIUM**: 21–50
- **LOW**: 0–20

Confidence is derived from the maximum per-artefact confidence, boosted by campaign detection (max 1.0). Single-artefact investigations have confidence reduced by 10%.

## API

### POST /analyze/investigation

```json
{
  "artefacts": [
    {"text": "Your UPI payment of ₹5000 is pending...", "type": "sms"},
    {"text": "Click here to complete KYC update...", "type": "sms"}
  ]
}
```

Response includes: `investigation_id`, `artefact_results`, `merged_entities`, `repeated_indicators`, `campaign`, `timeline`, `relationship_graph`, `global_assessment`, `investigation_report`.

## Evaluation

```bash
# Standard single-message evaluation
python evaluation/evaluation_runner.py --dataset datasets/benchmark.json

# Investigation mode
python evaluation/evaluation_runner.py --mode investigation --dataset datasets/investigation_benchmark.json
```

## Extending

Add new entity types: extend `_merge_entities()` in `investigation_service.py` and the normalisation functions.

Add new timeline events: add indicator checks in `_build_timeline()`.

Adjust campaign sensitivity: modify threshold constants in `core/constants.py` or `config/settings.py`.
