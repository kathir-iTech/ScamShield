# Security Architecture

## Overview

ScamShield implements a defense-in-depth security model suitable for public
deployment. The architecture supports three tiers of access and enables
configurable authentication for different deployment environments.

---

## Authentication Flow

```
Client                    FastAPI Middleware Stack
  |                              |
  |  POST /auth/token            |
  |  POST /auth/token/admin      |
  |------------------------->    |  JWT issued (HS256)
  |<-------------------------    |  access_token + refresh_token
  |                              |
  |  POST /analyze/text          |
  |  Authorization: Bearer <JWT> |
  |------------------------->    |  get_current_user dependency
  |                              |  - Decodes JWT
  |                              |  - Validates signature (HMAC-SHA256)
  |                              |  - Checks expiration
  |                              |  - Extracts role & subject
  |<-------------------------    |  Returns result or 401
```

### Token Lifecycle

- **Access Token**: Short-lived (default 1 hour, configurable via
  `SCAMSHIELD_JWT_ACCESS_TTL`). Carries subject and role. Signed with HMAC-SHA256.
- **Refresh Token**: Long-lived (default 30 days, configurable via
  `SCAMSHIELD_JWT_REFRESH_TTL`). Used exclusively via `POST /auth/refresh` to
  obtain new access tokens without re-authentication.
- No server-side session state: tokens are fully self-contained (stateless).

### Endpoints

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/auth/token` | POST | None | Issue access + refresh token (authenticated role) |
| `/auth/token/admin` | POST | None | Issue access + refresh token (admin role) |
| `/auth/refresh` | POST | None | Exchange refresh token for new token pair |
| `/auth/verify` | POST | None | Validate a token and return its claims |

Auth endpoints return 404 when `SCAMSHIELD_AUTH_ENABLED=false`.

---

## Authorization Model

### Roles

| Role | Rank | Description |
|---|---|---|
| `guest` | 0 | Unauthenticated users. Can access public endpoints. |
| `authenticated` | 1 | Users with a valid access token. |
| `admin` | 2 | Users with an admin-scoped token. |

### Permission Checking

Centralized in `core/auth/deps.py`. Roles are hierarchical: admin inherits all
authenticated permissions; authenticated inherits all guest permissions.

| Dependency | Required Role | Used For |
|---|---|---|
| `optional_auth` | None (guest allowed) | Health check, public endpoints |
| `require_auth` | authenticated+ | Analysis endpoints |
| `require_role(role)` | specific role+ | Fine-grained endpoint protection |
| `require_admin` | admin | Metrics, administration |

---

## CORS Configuration

CORS is no longer wildcard. Origins are read from `SCAMSHIELD_CORS_ORIGINS`
environment variable and validated against the environment:

| Environment | Default | Validation |
|---|---|---|
| `development` | `http://localhost,http://localhost:3000,http://localhost:5173` | None |
| `staging` | Per-env config | Required, no wildcard |
| `production` | Per-env config | Required, wildcard rejected |

Allowed methods: `GET`, `POST`, `OPTIONS`
Allowed headers: `Authorization`, `Content-Type`, `X-Request-ID`
Credentials flag: enabled only when origins are not wildcard.

---

## Middleware Stack

| Middleware | Order | Purpose |
|---|---|---|
| CORSMiddleware | 1 | Cross-Origin Resource Sharing |
| RequestIDMiddleware | 2 | UUID per request, timing, structured logging |
| SecurityHeadersMiddleware | 3 | HSTS, CSP, XFO, XSS, Referrer-Policy, Permissions-Policy, Cache-Control |
| RateLimitMiddleware | 4 | Per-IP token bucket (default 100 req/min) |
| RequestBodySizeMiddleware | 5 | Reject bodies > 10 MB |

### Security Headers

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `0` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
| `Content-Security-Policy` | `default-src 'self'` (HTML responses only) |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (HTML only) |
| `Cache-Control` | `no-store` (GET/HEAD < 300) |

---

## Secrets Management

- **No hardcoded secrets** in the codebase. All configuration comes from
  environment variables.
- **Startup validation**: `config/settings.py:validate_config()` checks all
  required variables and validates ranges.
- **`.env.example`**: provides documentation for every configurable variable.
- **JWT secret**: required when `SCAMSHIELD_AUTH_ENABLED=true`. Generate with:
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- **Safe Browsing API key**: read from `SCAMSHIELD_SAFE_BROWSING_API_KEY`.
  Empty key disables the connector gracefully.

---

## Input Validation

### Pydantic Constraints

| Model | Field | Constraints |
|---|---|---|
| `TextAnalysisRequest` | `text` | `min_length=1, max_length=100000` |
| `InvestigationArtefact` | `text` | `min_length=1, max_length=100000` |
| `InvestigationRequest` | `artefacts` | `min_length=1, max_length=100` |

### Runtime Validation

- **Text**: NFKC normalization, control char/zero-width char stripping, length
  enforcement (`MAX_TEXT_LENGTH`, default 10,000).
- **Image**: content-type whitelist (`image/jpeg`, `image/png`, `image/webp`,
  `image/bmp`), file size limit (default 10 MB), decompression bomb protection
  (max 50 MP), dimension limits (max 10,000 px).
- **File uploads**: temporary files with safe suffixes only.

---

## Logging & Audit

### Structured Logging

- JSON or text format via `SCAMSHIELD_LOG_FORMAT`.
- Every log entry includes: timestamp, level, logger name, message, request ID.
- Exception entries include exception type and message.
- File output with rotation: 10 MB max, 5 backups.

### PII Masking

The `_mask_pii()` function is applied to all exception messages before they are
logged or returned to the client. Patterns masked:

| Pattern | Replacement |
|---|---|
| 10+ digit numbers | `<REDACTED>` |
| Credit card numbers (1234-5678-9012-3456) | `<CARD>` |
| Email addresses | `<EMAIL>` |
| Phone numbers (international) | `<PHONE>` |
| UPI references | `<UPI>` |
| OTP references | `<OTP>` |
| PAN/Aadhar/Voter/Driving License references | `<ID>` |

### What Is Logged

- Request ID, duration, status code, method, path.
- Character counts (not the actual text).
- Error types and masked error messages.
- Pipeline stage failures (stage name only).
- Token issuance events (no token values, no secrets).

### What Is Never Logged

- Raw message text or OCR output.
- Analysis results or predictions.
- Token values, API keys, or secrets.
- Client IP (in production; logged in development for debugging).

---

## Threat Model

### Trust Boundaries

```
[Internet] --> [Reverse Proxy] --> [FastAPI App] --> [ML Model]
                    |                    |               |
                    | TLS termination    | Auth check    | File-system read
                    | Rate limiting      | Validation    | (no network)
                    | WAF                | CORS check
```

### Assets Protected

1. **Analysis API**: protected by JWT authentication (when enabled), rate
   limiting, request body size limits, and input validation.
2. **ML Models**: accessed only via the application. No direct access from
   outside.
3. **API Keys / Secrets**: never in code. Read from environment variables.
4. **User Data**: never persisted beyond request lifetime. Temporary files
   cleaned up in `finally` blocks.

### Attack Scenarios Mitigated

| Attack | Mitigation |
|---|---|
| Unauthenticated API access | JWT auth layer (configurable) |
| Cross-origin data theft | CORS allow-list, no wildcard in production |
| XSS | CSP header, input sanitisation, no HTML rendering |
| Clickjacking | `X-Frame-Options: DENY` |
| MIME-type confusion | `X-Content-Type-Options: nosniff` |
| Brute-force / DoS | Rate limiting, request body size limits |
| Decompression bombs | Pixel/dimension limits in OCR |
| Path traversal | No user-controlled file paths |
| Secrets leakage from URLs | Key passed via env var, not URL |

---

## Environment Setup

### Minimal production .env

```
SCAMSHIELD_ENVIRONMENT=production
SCAMSHIELD_CORS_ORIGINS=https://app.scamshield.com
SCAMSHIELD_AUTH_ENABLED=true
SCAMSHIELD_JWT_SECRET=<generate with secrets.token_urlsafe(48)>
SCAMSHIELD_JWT_ACCESS_TTL=3600
SCAMSHIELD_JWT_REFRESH_TTL=2592000
SCAMSHIELD_LOG_FORMAT=json
SCAMSHIELD_LOG_OUTPUT=both
SCAMSHIELD_LOG_FILE=/var/log/scamshield/scamshield.log
```

### Development .env

```
SCAMSHIELD_ENVIRONMENT=development
SCAMSHIELD_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
SCAMSHIELD_AUTH_ENABLED=false
SCAMSHIELD_LOG_FORMAT=text
SCAMSHIELD_LOG_OUTPUT=stdout
```

---

## Security Checklist

- [ ] `SCAMSHIELD_AUTH_ENABLED=true` in production
- [ ] `SCAMSHIELD_JWT_SECRET` set to a strong random value
- [ ] `SCAMSHIELD_CORS_ORIGINS` set to specific origins (no wildcard)
- [ ] `SCAMSHIELD_ENVIRONMENT=production`
- [ ] HTTPS termination at reverse proxy (nginx, Cloudflare, etc.)
- [ ] Rate limiting at reverse proxy as defense-in-depth
- [ ] Logging configured to JSON format for log aggregation
- [ ] Log files rotated and access-restricted
- [ ] Safe Browsing API key set (if connector enabled)
- [ ] Model files and data directory permissions are read-only for app user
- [ ] Regular dependency CVE scanning in CI
- [ ] No secrets committed to repository (use `.env` only)

---

## Deployment Recommendations

1. **Reverse proxy**: place behind nginx or Cloudflare for TLS termination,
   additional rate limiting, and WAF rules.
2. **Network isolation**: run the backend in a private subnet. Only the reverse
   proxy should have direct access.
3. **Minimal permissions**: app user should have read access to model files and
   write access only to the log directory.
4. **Monitoring**: integrate structured JSON logs with a SIEM or log
   aggregation service.
5. **Updates**: subscribe to CVE alerts for FastAPI, Starlette, Pydantic, and
   Pillow.
6. **No root**: never run the application as root. Use a dedicated user.
