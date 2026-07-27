# ScamShield Threat Intelligence Knowledge Base (TIKB)

A fully offline, deterministic knowledge layer for evidence enrichment — no LLMs, no embeddings, no vector databases, no paid APIs.

## Architecture

```
backend/intelligence/           ← Knowledge base (flat JSON files)
├── schemas.py                  ← ThreatRecord, AdvisoryRecord, HistoricalInvestigation dataclasses
├── loader.py                   ← Loads all JSON files from subdirectories
├── patterns/known_patterns.json    ← Known scam keyword patterns with family/risk
├── advisories/                     ← Official advisories from CERT-In, RBI, NPCI, banks
│   ├── cert_in.json
│   ├── rbi.json
│   ├── npci.json
│   ├── banks.json
│   └── internal.json
├── watchlists/                    ← Known malicious indicators
│   ├── phone_watchlist.json
│   ├── domain_watchlist.json
│   ├── upi_watchlist.json
│   └── email_watchlist.json
├── examples/known_scam_examples.json  ← Full-text examples of known scam templates
└── history/investigations.json        ← Previous investigation records for correlation

backend/services/knowledge_service.py  ← Retrieval engine & enrichment API
```

## Threat Record Schema

| Field | Type | Description |
|---|---|---|
| `indicator_id` | `str` | Unique identifier |
| `type` | `str` | url, domain, phone, email, upi, bank, bank_account, ifsc, qr, keyword |
| `value` | `str` | The indicator value |
| `aliases` | `List[str]` | Alternative known values |
| `family` | `str` | Scam family (Financial Fraud, Credential Theft, etc.) |
| `subfamily` | `str` | Scam subfamily (Banking, UPI, Phishing, etc.) |
| `risk` | `str` | CRITICAL, HIGH, MEDIUM, LOW |
| `confidence` | `float` | 0.0–1.0 |
| `source` | `str` | internal, cert-in, rbi, npci, bank, community, history |
| `first_seen` | `str` | ISO date of first observation |
| `last_seen` | `str` | ISO date of latest observation |
| `description` | `str` | Free-text description |
| `related_indicators` | `List[str]` | IDs of related indicators |
| `references` | `List[Dict]` | External references (title, url, source, date) |

## Similarity Matching (Deterministic)

| Method | Description | Threshold |
|---|---|---|
| **Exact** | Direct string equality after NFKC normalisation | 100% |
| **Normalised** | Lowercased, stripped, Unicode NFC/NFKC | 100% |
| **Prefix** | Record value starts with query | ≥4 chars |
| **Suffix** | Record value ends with query | ≥4 chars |
| **Domain Comparison** | Extract domain from URL, compare normalized | ≥7 chars for phone suffix |
| **Levenshtein** | Edit distance within configurable threshold | ≤3 edits or ≤20% of length |
| **Phone Digit Match** | Extract digits-only, compare last 7/10 digits | ≥7 digits |

All matching is Unicode-aware via `unicodedata.normalize('NFKC', ...)`.

## Advisory Matching

Advisories from CERT-In, RBI, NPCI, banks, and internal sources are matched against observed indicators by:
1. Keyword overlap between `affected_indicators` and query/keywords
2. Indicator type alignment
3. Relevance scoring capped at 1.0

## Historical Correlation

Previous investigations stored in `history/investigations.json` are correlated with current analysis by:
1. Shared entity values (phone, domain, UPI, email) — exact match
2. Shared indicator names
3. Family overlap
4. Campaign flag propagation

Confidence = `min(shared_count * 0.15 + campaign_overlap * 0.2 + family_match * 0.15, 1.0)`

## Retrieval API

### Direct search functions (via `knowledge_service.search_by_*`)

```python
from services.knowledge_service import get_service

ks = get_service()
ks.search_by_url("https://sbi-kyc-update.xyz/login")
ks.search_by_domain("evil-phishing.top")
ks.search_by_phone("+91-9876543210")
ks.search_by_email("support@phishing.com")
ks.search_by_upi("scam@paytm")
ks.search_by_bank("sbi")
ks.search_by_keywords(["kyc update", "account blocked"])
ks.search_by_family("Financial Fraud")
```

### Enrichment API (integrated into pipeline)

```python
from services.knowledge_service import enrich_analysis, enrich_investigation_result

# For single-message analysis
enrichment = enrich_analysis(analysis_dict)

# For multi-artefact investigation
enrichment = enrich_investigation_result(merged_entities, repeated_indicators, dominant_family)
```

Both return:
```json
{
  "knowledge_matches": [...],
  "advisory_references": [...],
  "historical_matches": [...],
  "match_count": 3,
  "advisory_count": 1,
  "historical_count": 0
}
```

## Report Enrichment

Knowledge enrichment data is embedded in:
- `AnalysisResponse.investigation_report.knowledge_enrichment` (for single messages)
- `InvestigationResponse.investigation_report.knowledge_enrichment` (for investigations)
- Top-level optional fields `knowledge_matches`, `advisory_references`, `historical_matches` on both responses (backward compatible, default empty)

No breaking API changes — all new fields are optional with defaults.

## Evaluation

```bash
# Standard benchmark (unchanged)
python evaluation/evaluation_runner.py --dataset datasets/benchmark.json

# Knowledge retrieval benchmark
python evaluation/evaluation_runner.py --mode knowledge --dataset datasets/knowledge_benchmark.json

# Investigation benchmark
python evaluation/evaluation_runner.py --mode investigation --dataset datasets/investigation_benchmark.json
```

## Extending the Knowledge Base

### Add a new pattern
Edit the relevant JSON file under `backend/intelligence/` following the schema.

### Add a new advisory
Create a new JSON file in `backend/intelligence/advisories/` and add it to the loader in `loader.py`.

### Add a new search type
1. Add a `search_by_*` method to `KnowledgeService` in `knowledge_service.py`
2. Add the mapping in `search_by_indicator()`
3. Add the type to `THREAT_TYPES` in `intelligence/schemas.py`

## Key Properties

- **Fully offline**: No internet or API calls needed
- **Deterministic**: Same input always produces same output
- **Explainable**: Every match has a `match_type` and `confidence` score
- **Extensible**: Add new indicators by editing JSON files
- **Backward compatible**: All new API fields are optional with defaults
- **No ML/LLM**: Pure string matching and Levenshtein distance
