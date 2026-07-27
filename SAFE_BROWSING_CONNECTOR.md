# Google Safe Browsing Connector

## Overview

The Google Safe Browsing connector enables ScamShield to check URLs and domains against Google's Safe Browsing database for known threats including malware, social engineering (phishing), unwanted software, and potentially harmful applications.

The connector is **entirely optional**. ScamShield works offline without it. No internet access is required at startup.

## Configuration

All settings are in `backend/config/settings.py` and overridable via environment variables:

| Setting | Env Variable | Default | Description |
|---------|-------------|---------|-------------|
| `SAFE_BROWSING_ENABLED` | `SCAMSHIELD_SAFE_BROWSING_ENABLED` | `True` | Master switch |
| `SAFE_BROWSING_API_KEY` | `SCAMSHIELD_SAFE_BROWSING_API_KEY` | `""` | Google API key (required) |
| `SAFE_BROWSING_TIMEOUT` | `SCAMSHIELD_SAFE_BROWSING_TIMEOUT` | `15` | HTTP timeout in seconds |
| `SAFE_BROWSING_CACHE_TTL` | `SCAMSHIELD_SAFE_BROWSING_CACHE_TTL` | `300` | Cache TTL in seconds |
| `SAFE_BROWSING_MAX_BATCH` | `SCAMSHIELD_SAFE_BROWSING_MAX_BATCH` | `500` | Max URLs per API request |

## API Key Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable the **Safe Browsing API**
4. Create an API key under **Credentials**
5. Restrict the key to the Safe Browsing API only

Set the key via environment variable:

```bash
set SCAMSHIELD_SAFE_BROWSING_API_KEY=your_api_key_here
```

Or add it to your `.env` file:

```
SCAMSHIELD_SAFE_BROWSING_API_KEY=your_api_key_here
```

## Behaviour

### When disabled (no API key)

- Connector self-reports as disabled.
- `lookup()` returns an unmatched result with summary "Google Safe Browsing is disabled (no API key)".
- `health()` returns `{"status": "disabled", "reason": "No API key configured"}`.
- The connector is excluded from lookups by the framework.
- ScamShield continues working normally offline.

### When enabled

- URLs and domains extracted from user messages are checked against Google Safe Browsing.
- Matches are returned with risk, confidence, threat types, and evidence.
- Results are cached with the configured TTL.

## Failure Handling

| Scenario | Behaviour |
|----------|-----------|
| Invalid API key (HTTP 403) | Returns error result, no retry |
| Rate limited (HTTP 429) | Retries up to 2 times with exponential backoff (2s, 4s) |
| Network timeout | Retries up to 2 times with exponential backoff |
| Server error (HTTP 5xx) | Returns error result |
| Malformed response | Returns error result |
| All retries exhausted | Returns error result with details |

No connector failure ever fails an investigation.

## Caching

The connector reuses the framework's `ConnectorCache`. The manager caches individual lookup results before returning them. Cache TTL is configurable via `SAFE_BROWSING_CACHE_TTL` (default 300s).

Cache key format: `google_safe_browsing:{type}:{normalised_indicator}`

## Rate Limiting

Google Safe Browsing API has usage quotas. The connector:
- Batches up to 500 URLs per request (`SAFE_BROWSING_MAX_BATCH`)
- Uses exponential backoff on rate limit (429) responses
- Caches results to avoid duplicate lookups
- Respects the configured timeout per request

## Threat Type Mapping

| Google Threat Type | Risk | Confidence | Description |
|--------------------|------|------------|-------------|
| `MALWARE` | HIGH | 0.90 | Malicious software |
| `SOCIAL_ENGINEERING` | HIGH | 0.85 | Phishing/social engineering |
| `UNWANTED_SOFTWARE` | MEDIUM | 0.70 | Unwanted software |
| `POTENTIALLY_HARMFUL_APPLICATION` | MEDIUM | 0.65 | Potentially harmful app |

## Security Considerations

- **Do not hardcode API keys** in source code. Use environment variables.
- Restrict the API key to the Safe Browsing API in Google Cloud Console.
- Consider using a key rotation strategy for production deployments.
- All traffic to Google is over HTTPS.
- The connector logs only error messages, not API keys or full request bodies.

## Testing

The connector is tested with mocked HTTP responses — no real network calls during tests.

```bash
cd backend
python -m pytest tests/unit/test_google_safe_browsing.py -v
```

Test coverage includes:
- Successful lookup (safe URL, malicious URL, domain)
- API timeout
- Invalid API key (403)
- Rate limiting (429) with retry
- Server errors (500)
- Malformed JSON response
- Empty response
- Connector disabled (no key, flag off)
- Health checks
- Batch lookup
- Auto-discovery
- Retry behaviour

## Response Model

Each lookup returns a standard `LookupResult`:

```python
{
    "indicator": "https://phishing.example.com",
    "indicator_type": "url",
    "matched": True,
    "risk": "HIGH",
    "confidence": 0.85,
    "source": "google_safe_browsing",
    "summary": "Google Safe Browsing flagged: SOCIAL_ENGINEERING",
    "evidence": [
        {
            "threat_type": "SOCIAL_ENGINEERING",
            "platform_type": "ANY_PLATFORM",
            "threat_entry_type": "URL",
            "matched_url": "https://phishing.example.com",
            "cache_duration": "300s"
        }
    ],
    "references": [
        {
            "source": "Google Safe Browsing",
            "url": "https://safebrowsing.google.com/",
            "threat_types": ["SOCIAL_ENGINEERING"]
        }
    ],
    "timestamp": 1234567890.0,
    "latency": 150.0,
    "error": None
}
```
