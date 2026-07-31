# Sample API Requests — ScamShield RC2

> Base URL (local): `http://localhost:8000`
> Base URL (Docker): `http://localhost:8000`
> All requests use `Content-Type: application/json` unless noted.
> Auth endpoints return 404 when `SCAMSHIELD_AUTH_ENABLED=false`.

---

## Health & Liveness

### 1. GET /health
```
curl http://localhost:8000/health
```
**Expected:** 200, `{"status": "healthy", ...}`

### 2. GET /ready
```
curl http://localhost:8000/ready
```
**Expected:** 200, readiness state

### 3. GET /live
```
curl http://localhost:8000/live
```
**Expected:** 200, liveness state

### 4. GET /model/info
```
curl http://localhost:8000/model/info
```
**Expected:** 200, model metadata (version, accuracy, registry)

### 5. GET /metrics (Prometheus)
```
curl http://localhost:8000/metrics
```
**Expected:** 200, OpenMetrics text format

---

## Text Analysis

### 6. POST /analyze/text — Scam SMS
```bash
curl -X POST http://localhost:8000/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text": "URGENT: Your SBI account will be deactivated in 24 hours. Update KYC immediately: https://sbi-kyc.xyz"}'
```
**Expected:** 200, `is_scam: true`, category, confidence, reasoning

### 7. POST /analyze/text — Legitimate SMS
```bash
curl -X POST http://localhost:8000/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Hi, are we still meeting for coffee tomorrow at 5pm?"}'
```
**Expected:** 200, `is_scam: false`, low confidence

### 8. POST /analyze/text — Empty text (validation)
```bash
curl -X POST http://localhost:8000/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text": "   "}'
```
**Expected:** 400 validation error

### 9. POST /analyze/text — Missing field
```bash
curl -X POST http://localhost:8000/analyze/text \
  -H "Content-Type: application/json" \
  -d '{}'
```
**Expected:** 422 Unprocessable Entity

### 10. POST /analyze/text — Oversized text (>10000 chars)
```bash
curl -X POST http://localhost:8000/analyze/text \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$(printf 'a%.0s' {1..10001})\"}"
```
**Expected:** 422 validation error

---

## Image Analysis (OCR)

### 11. POST /analyze/image — Scam screenshot
```bash
curl -X POST http://localhost:8000/analyze/image \
  -F "file=@/path/to/test-scam-screenshot.png"
```
**Expected:** 200, `is_scam: true`, `ocr_text` field present

### 12. POST /analyze/image — Legit screenshot
```bash
curl -X POST http://localhost:8000/analyze/image \
  -F "file=@/path/to/test-legit-screenshot.png"
```
**Expected:** 200, `is_scam: false`

### 13. POST /analyze/image — Corrupted file
```bash
curl -X POST http://localhost:8000/analyze/image \
  -F "file=@/path/to/corrupted.txt"
```
**Expected:** 400 error

### 14. POST /analyze/image — Missing file
```bash
curl -X POST http://localhost:8000/analyze/image
```
**Expected:** 422 Unprocessable Entity

---

## Investigation

### 15. POST /analyze/investigation — Multiple artefacts
```bash
curl -X POST http://localhost:8000/analyze/investigation \
  -H "Content-Type: application/json" \
  -d '{"artefacts": [{"text": "URGENT: Your account is blocked. Call 1800-123-4567 now.", "type": "text"}, {"text": "Win a free iPhone! Click https://bit.ly/free-iphone", "type": "text"}]}'
```
**Expected:** 200, investigation with timeline, campaigns, relationship graph

### 16. POST /analyze/investigation — Empty artefacts
```bash
curl -X POST http://localhost:8000/analyze/investigation \
  -H "Content-Type: application/json" \
  -d '{"artefacts": []}'
```
**Expected:** 422 validation error

---

## Authentication (only when SCAMSHIELD_AUTH_ENABLED=true)

### 17. POST /auth/token — Get access token (client API key)
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your-client-api-key" \
  -d '{}'
```
**Expected:** 200, `{"access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 3600}`

### 18. POST /auth/token — Missing key (negative)
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{}'
```
**Expected:** 401 Unauthorized

### 19. POST /auth/token — Wrong key (negative)
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: wrong-key" \
  -d '{}'
```
**Expected:** 401 Unauthorized

### 20. POST /auth/token/admin — Admin token
```bash
curl -X POST http://localhost:8000/auth/token/admin \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your-admin-api-key" \
  -d '{"admin_key": "your-admin-api-key"}'
```
**Expected:** 200, admin token

### 21. POST /auth/refresh — Refresh access token
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "REPLACE_WITH_REFRESH_TOKEN"}'
```
**Expected:** 200, new access + refresh tokens

### 22. POST /auth/refresh — Reuse refresh token (negative)
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "REPLACE_WITH_USED_REFRESH_TOKEN"}'
```
**Expected:** 401 Unauthorized (reuse detected)

### 23. POST /auth/logout — Revoke refresh token
```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "REPLACE_WITH_REFRESH_TOKEN"}'
```
**Expected:** 200, `{"detail": "Logged out successfully"}`

### 24. POST /auth/revoke — Revoke token (requires auth)
```bash
curl -X POST http://localhost:8000/auth/revoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer REPLACE_WITH_ACCESS_TOKEN" \
  -d '{"token": "REPLACE_WITH_TOKEN_TO_REVOKE"}'
```
**Expected:** 200, `{"detail": "Token revoked"}`

### 25. POST /auth/revoke — No auth header (negative)
```bash
curl -X POST http://localhost:8000/auth/revoke \
  -H "Content-Type: application/json" \
  -d '{"token": "some-token"}'
```
**Expected:** 401 Unauthorized

### 26. POST /auth/verify — Verify token
```bash
curl -X POST http://localhost:8000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "REPLACE_WITH_ACCESS_TOKEN"}'
```
**Expected:** 200, `{"valid": true, "sub": "...", "role": "...", "token_type": "access"}`

### 27. POST /auth/verify — Invalid token (negative)
```bash
curl -X POST http://localhost:8000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "invalid.token.here"}'
```
**Expected:** 200, `{"valid": false, "detail": "..."}`
