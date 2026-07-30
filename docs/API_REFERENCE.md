# API Reference

## Base URL

`http://localhost:8000` (development) or `https://your-domain.com` (production)

## Endpoints

### POST /analyze/text

Analyze SMS text for scam indicators.

**Request Body:**
```json
{
  "text": "Your Aadhaar KYC is expiring. Click https://fake-kyc.com to update."
}
```

### POST /analyze/image

Analyze a screenshot for scam content.

**Request:** Multipart form with `file` field (image, max 10MB).

**Response:** Same structure as text analysis with `ocr_text` field added.

### POST /analyze/investigation

Run a full investigation pipeline on input text.

### POST /auth/token

Obtain an access token. Requires `CLIENT_API_KEY` when `AUTH_ENABLED=true`.

### POST /auth/token/admin

Obtain an admin access token. Requires `ADMIN_API_KEY` when `AUTH_ENABLED=true`.

### POST /auth/refresh

Refresh an access token using a refresh token.

### POST /auth/logout

Revoke the current session's tokens.

### POST /auth/revoke

Revoke a specific token by value. Requires authentication.

### POST /auth/verify

Verify a token and return its payload without requiring authentication.

### GET /health

System health check.

### GET /ready

Readiness probe for orchestration.

### GET /live

Liveness probe for orchestration.

### GET /model/info

Model metadata (version, accuracy, registry info).
