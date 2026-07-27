# API Security Guide

## Authentication

### JWT-Based Authentication

ScamShield uses stateless JWT (HMAC-SHA256) for authentication.

| Endpoint | Method | Description |
|---|---|---|
| `/auth/token` | POST | Issue access + refresh tokens (role: authenticated) |
| `/auth/token/admin` | POST | Issue access + refresh tokens (role: admin) |
| `/auth/refresh` | POST | Exchange refresh token for new token pair |
| `/auth/verify` | POST | Validate a token and return its claims |

Token endpoints return 404 when `SCAMSHIELD_AUTH_ENABLED=false`.

### Token Format

```json
{
  "access_token": "<JWT>",
  "refresh_token": "<JWT>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using Tokens

```
Authorization: Bearer <access_token>
```

### Token Claims

| Claim | Description |
|---|---|
| `sub` | Subject (user identifier) |
| `role` | User role: `guest`, `authenticated`, `admin` |
| `exp` | Expiration timestamp |
| `iat` | Issued-at timestamp |
| `jti` | Unique token ID (for revocation tracking) |
| `token_type` | `access` or `refresh` |

---

## API Keys

### Key Types

| Type | Role | Typical Scopes |
|---|---|---|
| Developer | `authenticated` | `analyze:text`, `analyze:image` |
| Internal Service | `authenticated` | `analyze:*`, `health:read` |
| Admin | `admin` | `admin:all` |

### Key Format

Keys are returned once at creation:
- `key_id`: `scm_<16 hex chars>` (for management)
- `raw_key`: 48 hex characters (for authentication)

Store the raw key securely; it cannot be retrieved later.

### Using API Keys

```
Authorization: Bearer <raw_key>
```

### Key Management

| Operation | Description |
|---|---|
| Create | `POST /admin/api-keys` |
| Revoke | `POST /admin/api-keys/{key_id}/revoke` |
| Rotate | `POST /admin/api-keys/{key_id}/rotate` |
| List | `GET /admin/api-keys` |
| Info | `GET /admin/api-keys/{key_id}` |

### Scopes

| Scope | Permission |
|---|---|
| `analyze:text` | Submit text for scam analysis |
| `analyze:image` | Submit images for analysis |
| `analyze:investigation` | Run investigations |
| `health:read` | Read health/readiness/liveness endpoints |
| `metrics:read` | Read metrics endpoint |
| `admin:all` | Full administrative access |

---

## Rate Limiting

### Per-IP Sliding Window

| Environment | Max Requests | Window | Burst |
|---|---|---|---|
| development | 200 | 60s | — |
| testing | 200 | 60s | — |
| staging | 100 | 60s | — |
| production | 60 | 60s | — |
| local | 500 | 60s | — |

### Rate Limit Headers

Every response includes:

| Header | Description |
|---|---|
| `X-RateLimit-Limit` | Maximum requests per window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |

### 429 Response

```json
{
  "detail": "Too many requests. Please try again later."
}
```

Includes `Retry-After` header with seconds until reset.

### Temporary IP Blocking

After 3 consecutive rate-limit violations, the IP is temporarily blocked
with exponential backoff:
- 1st block: 60 seconds
- 2nd block: 120 seconds
- 3rd block: 240 seconds
- Max block: 3600 seconds (1 hour)

---

## Quota Model

### Per-IP Quotas

- Based on sliding window (not fixed window)
- Window slides on each request (old entries expire)
- Each IP has its own counter
- Violations tracked for temporary blocking

### Per-User Quotas (Future)

The quota system is designed to support per-user quotas:
1. Extend `SlidingWindowRateLimiter` to accept a user identifier
2. Add user-ID extraction from JWT or API key
3. Track separately from IP-based limits

### Burst Protection

- Consecutive violations trigger escalating block durations
- Block durations: 60s, 120s, 240s, up to 3600s
- Block clears automatically after timeout
- Rate limit window slides continuously (no reset on block)

---

## Security Checklist

### Authentication
- [ ] `SCAMSHIELD_AUTH_ENABLED=true` in production
- [ ] `SCAMSHIELD_JWT_SECRET` set to strong random value (min 48 bytes)
- [ ] JWT access TTL ≤ 900s (15 min) in production
- [ ] JWT refresh TTL ≤ 86400s (24h) in production

### API Keys
- [ ] API keys scoped to minimum required permissions
- [ ] Keys rotated on a regular schedule
- [ ] Revoked keys no longer accepted
- [ ] Key usage monitored for anomalies

### Rate Limiting
- [ ] Rate limits configured per environment
- [ ] IP blocking enabled for repeated violations
- [ ] Rate limit headers exposed to clients
- [ ] Rate limit events monitored in audit log

### Headers
- [ ] HSTS enabled in production
- [ ] CSP configured for frontend
- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff
- [ ] Referrer-Policy: strict-origin-when-cross-origin
- [ ] Permissions-Policy restricts sensitive APIs

### Input Validation
- [ ] All inputs validated by Pydantic (type, length, range)
- [ ] File uploads restricted by type and size
- [ ] Image uploads protected against decompression bombs
- [ ] Content-Type enforced for file uploads

### Logging
- [ ] Structured JSON format in production
- [ ] No secrets, tokens, or PII in logs
- [ ] Audit events recorded for auth, key management, security events
- [ ] Log rotation configured

---

## OWASP API Security Top 10 Mapping

| # | Category | ScamShield Status |
|---|---|---|
| API1 | Broken Object Level Authorization | Mitigated by RBAC (guest/authenticated/admin) |
| API2 | Broken Authentication | JWT with HMAC-SHA256, expiry, refresh tokens |
| API3 | Excessive Data Exposure | Response models strictly typed with Pydantic |
| API4 | Lack of Resources & Rate Limiting | Sliding window rate limiter, body size limits, IP blocking |
| API5 | Broken Function Level Authorization | Role-based permission checks (`require_role`, `require_admin`) |
| API6 | Mass Assignment | Pydantic models with explicit fields |
| API7 | Security Misconfiguration | Profile-based defaults, fail-fast validation |
| API8 | Injection | Input sanitisation (NFKC, control char removal) |
| API9 | Improper Assets Management | Version endpoint, registered route logging |
| API10 | Insufficient Logging & Monitoring | Structured audit logging, metrics, health checks |

---

## Operational Recommendations

### Production Deployment

1. **Enable authentication**: Set `SCAMSHIELD_AUTH_ENABLED=true`
2. **Configure CORS**: Set `SCAMSHIELD_CORS_ORIGINS` to specific origins
3. **Set JWT secret**: Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
4. **Enable JSON logging**: Set `SCAMSHIELD_LOG_FORMAT=json`
5. **Monitor rate limiting**: Watch `rate_limit_events` metric
6. **Audit logs**: Route to centralized log aggregation
7. **IP blocking**: Let the sliding window rate limiter handle abuse
8. **Secrets rotation**: Rotate JWT secret and API keys regularly

### Monitoring Thresholds

| Metric | Warning | Critical |
|---|---|---|
| Average latency | > 1s | > 5s |
| Error rate | > 1% | > 5% |
| Rate limit events | > 10/min | > 50/min |
| Auth failures | > 5/min | > 20/min |
| Pipeline failures | > 1/min | > 5/min |

### Incident Response

See `PRODUCTION_OPERATIONS.md` for the full incident response checklist.
