# API Reference

## Base URL

`http://localhost:8000` (development) or `https://your-domain.com` (production)

## Endpoints

### POST /api/v1/analyze/text

Analyze SMS text for scam indicators.

**Request Body:**
```json
{
  "text": "Your Aadhaar KYC is expiring. Click https://fake-kyc.com to update."
}
```

**Response:**
```json
{
  "is_scam": true,
  "confidence_score": 0.87,
  "ml_probability": 0.82,
  "rule_matches": [
    {"rule": "kyc_impersonation", "category": "identity", "confidence": 0.9},
    {"rule": "suspicious_url", "category": "phishing", "confidence": 0.85}
  ],
  "entities": [
    {"type": "url", "value": "https://fake-kyc.com", "risk": "malicious"},
    {"type": "organization", "value": "Aadhaar", "risk": "impersonated"}
  ],
  "reasoning": "ML confidence 0.82 matches KYC impersonation pattern. URL domain appears suspicious.",
  "rule_summary": "Matched 2 of 18 rules across 2 categories.",
  "pipeline_used": ["ml", "rules", "confidence", "reasoning"]
}
```

### POST /api/v1/analyze/image

Analyze a screenshot for scam content.

**Request:** Multipart form with `file` field (image, max 10MB).

**Response:** Same structure as text analysis with `ocr_text` field added.

### GET /api/v1/health

System health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "ml_model_loaded": true,
  "ocr_available": true,
  "connectors": [
    {"name": "google_safe_browsing", "status": "healthy", "latency_ms": 150}
  ],
  "metrics": {
    "total_analyses": 1250,
    "avg_latency_ms": 58,
    "p95_latency_ms": 110
  }
}
```

### GET /api/v1/health/ping

Simple connectivity check.

**Response:** `{"ping": "pong"}`

### GET /api/v1/health/readiness

Readiness probe for orchestration.

**Response:** `{"status": "ready"}`
