# Threat Intelligence Connector Framework

## Architecture

```
connector/
├── __init__.py          # Public API exports
├── base.py              # BaseConnector abstract class
├── manager.py           # ConnectorManager — lifecycle, parallel execution, merge
├── registry.py          # ConnectorRegistry — auto-discovery, registration
├── models.py            # LookupResult dataclass
├── exceptions.py        # Connector exception hierarchy
├── utils.py             # Normalization, merge, confidence aggregation
├── cache.py             # TTL-based thread-safe cache
└── mock.py              # MockThreatConnector (offline, uses local JSON)
```

## Connector Lifecycle

1. **Discovery** — `ConnectorRegistry.discover()` scans the `connectors` package for subclasses of `BaseConnector` and auto-registers them.
2. **Registration** — Connectors can also be registered manually via `ConnectorRegistry.register(instance)`.
3. **Loading** — `ConnectorManager.load_connectors()` triggers discovery once.
4. **Lookup** — `manager.lookup(indicator, indicator_type)` finds enabled connectors supporting the type, runs them in parallel, merges results, deduplicates, and aggregates confidence.
5. **Caching** — Each result is cached with configurable TTL. Cache key is normalized.
6. **Enrichment** — `enrich_with_connectors(analysis)` extracts entities/indicators from analysis context and runs them through all applicable connectors.

## BaseConnector Interface

Every connector must implement:

| Method / Property      | Returns           | Description                              |
|------------------------|-------------------|------------------------------------------|
| `name`                 | `str`             | Unique connector identifier              |
| `version`              | `str`             | Semantic version                         |
| `enabled`              | `bool`            | Whether the connector is active          |
| `priority`             | `int`             | Lower = higher priority                  |
| `supported_indicators()` | `List[str]`     | Indicator types the connector handles    |
| `health()`             | `Dict`            | Returns status dict with `status` key    |
| `lookup()`             | `LookupResult`    | Perform threat intelligence lookup       |
| `normalize()`          | `str`             | Normalize indicator (default: strip+lower) |
| `confidence()`         | `float`           | Override confidence scoring              |
| `metadata()`           | `Dict`            | Connector metadata                       |

## LookupResult Model

| Field            | Type          | Description                              |
|------------------|---------------|------------------------------------------|
| `indicator`      | `str`         | Original indicator value                 |
| `indicator_type` | `str`         | Type (url, domain, phone, email, upi...) |
| `matched`        | `bool`        | Whether a threat match was found         |
| `risk`           | `str`         | Risk level (HIGH, MEDIUM, LOW, UNKNOWN)  |
| `confidence`     | `float`       | Match confidence (0.0 - 1.0)             |
| `source`         | `str`         | Connector name                           |
| `summary`        | `str`         | Human-readable summary                   |
| `evidence`       | `List[Dict]`  | Supporting evidence items                |
| `references`     | `List[Dict]`  | External reference links                 |
| `timestamp`      | `float`       | Unix timestamp of lookup                 |
| `latency`        | `float`       | Lookup duration in milliseconds          |
| `error`          | `str`         | Error message if the lookup failed       |

## Caching

- `ConnectorCache` stores lookup results by normalized key: `{connector}:{type}:{indicator}`.
- Default TTL is 300 seconds (configurable via `CONNECTOR_CACHE_TTL`).
- Thread-safe via `threading.Lock`.
- Supports `get`, `set`, `evict`, `clear`, `purge_expired`.
- Cache key normalization ensures `Evil.Com` and `evil.com` map to the same entry.

## Configuration (settings.py)

| Setting                      | Default | Description                              |
|------------------------------|---------|------------------------------------------|
| `CONNECTOR_ENABLED`          | `True`  | Master switch for all connectors         |
| `CONNECTOR_TIMEOUT`          | `10`    | Per-connector timeout in seconds         |
| `CONNECTOR_RETRY_COUNT`      | `1`     | Number of retries on failure             |
| `CONNECTOR_PARALLELISM`      | `4`     | Max parallel connector executions        |
| `CONNECTOR_CACHE_TTL`        | `300`   | Cache TTL in seconds                     |
| `CONNECTOR_MAX_RESULTS`      | `10`    | Max merged results returned              |

All configs can be overridden via environment variables:
- `SCAMSHIELD_CONNECTOR_TIMEOUT`
- `SCAMSHIELD_CONNECTOR_RETRY_COUNT`
- `SCAMSHIELD_CONNECTOR_PARALLELISM`
- `SCAMSHIELD_CONNECTOR_CACHE_TTL`
- `SCAMSHIELD_CONNECTOR_MAX_RESULTS`

## MockThreatConnector

`MockThreatConnector` is a built-in connector that uses local intelligence data from `backend/intelligence/`. It runs entirely offline, requires no network access, and provides deterministic results.

- Priority: 0 (highest)
- Indicators: url, domain, phone, email, upi, keyword
- Matching: exact, domain suffix, phone suffix/prefix, word overlap

## Response Enrichment

Connector results are embedded in `AnalysisResponse.connector_matches` and `InvestigationResponse.connector_matches` as `List[Dict]` (empty by default, no API breaking change).

The pipeline also enriches `investigation_report.connector_enrichment` with the full list.

## Developing a New Connector

1. Create `backend/connectors/<name>.py`
2. Subclass `BaseConnector` and implement all abstract methods
3. The registry auto-discovers it on next load
4. Optionally add config to `settings.py`

Example minimal connector:

```python
from typing import Dict, List
from connectors.base import BaseConnector
from connectors.models import LookupResult

class ExampleConnector(BaseConnector):
    @property
    def name(self) -> str:
        return "example"

    @property
    def version(self) -> str:
        return "1.0.0"

    def supported_indicators(self) -> List[str]:
        return ["url", "domain"]

    def health(self) -> Dict:
        return {"status": "ok"}

    def lookup(self, indicator: str, indicator_type: str) -> LookupResult:
        # Your lookup logic here
        return LookupResult(
            indicator=indicator,
            indicator_type=indicator_type,
            matched=False,
            risk="UNKNOWN",
            confidence=0.0,
            source=self.name,
        )
```

## Failure Handling

- Individual connector failures never break the pipeline.
- Timeouts are enforced per-connector via `CONNECTOR_TIMEOUT`.
- Retries (`CONNECTOR_RETRY_COUNT`) are attempted before reporting failure.
- Unhealthy connectors (health check fails) return an error result immediately.
- All errors are caught and recorded in the result's `error` field.
- Parallel execution isolates failures via `ThreadPoolExecutor`.

## Merge Strategy

1. Separates matched and unmatched results.
2. Deduplicates by source name (first result wins).
3. Sorts by descending confidence, then ascending latency.
4. Caps at `CONNECTOR_MAX_RESULTS`.
5. Confidence aggregation uses inverse-rank weighting.

## Future Connectors (not yet implemented)

- VirusTotal connector
- Google Safe Browsing connector
- WHOIS/RDAP connector
- URLhaus connector
- PhishTank connector
- Custom API connectors
