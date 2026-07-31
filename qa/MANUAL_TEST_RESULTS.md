# Manual Test Results — ScamShield RC2

> Test Date: ____________
> Tester: ____________
> Environment: [ ] Local  [ ] Docker  [ ] Kubernetes
> Backend URL: ____________
> AUTH_ENABLED: [ ] true  [ ] false
> CLI used: [ ] curl  [ ] Postman  [ ] Swagger UI

---

## 1. Installation

| # | Test Case | Expected | Actual | Status | Notes |
|---|-----------|----------|--------|--------|-------|
| 1.1 | Fresh clone | Clone succeeds | | | |
| 1.2 | `pip install -r requirements.txt` | Success | | | |
| 1.3 | `npm ci` | Success | | | |
| 1.4 | `npm run build` | Success | | | |

## 2. Health & Liveness

| # | Test Case | Expected | Actual | Status | Notes |
|---|-----------|----------|--------|--------|-------|
| 2.1 | GET /health | 200, healthy | | | |
| 2.2 | GET /ready | 200, ready | | | |
| 2.3 | GET /live | 200 | | | |
| 2.4 | GET /model/info | 200, model info | | | |
| 2.5 | GET /metrics | 200, metrics | | | |

## 3. Authentication

| # | Test Case | Expected | Actual | Status | Notes |
|---|-----------|----------|--------|--------|-------|
| 3.1 | POST /auth/token (valid key) | 200, tokens | | | |
| 3.2 | POST /auth/token (missing key) | 401 | | | |
| 3.3 | POST /auth/token (wrong key) | 401 | | | |
| 3.4 | POST /auth/token/admin (valid key) | 200, admin token | | | |
| 3.5 | POST /auth/refresh (valid) | 200, new tokens | | | |
| 3.6 | POST /auth/refresh (reused) | 401 | | | |
| 3.7 | POST /auth/logout | 200 | | | |
| 3.8 | POST /auth/revoke (with auth) | 200 | | | |
| 3.9 | POST /auth/revoke (no auth) | 401 | | | |
| 3.10 | POST /auth/verify (valid) | 200, valid=true | | | |
| 3.11 | POST /auth/verify (invalid) | 200, valid=false | | | |
| 3.12 | Protected endpoint, no token | 401 | | | |
| 3.13 | Expired token | 401 | | | |
| 3.14 | Revoked token | 401 | | | |

## 4. Text Analysis

| # | Test Case | Expected | Actual | Status | Notes |
|---|-----------|----------|--------|--------|-------|
| 4.1 | Scam SMS (sample #1) | is_scam=true | | | |
| 4.2 | Legit SMS (sample #1) | is_scam=false | | | |
| 4.3 | Empty text | 400 | | | |
| 4.4 | Missing field | 422 | | | |
| 4.5 | Oversized text | 422 | | | |
| 4.6 | UPI scam | is_scam=true | | | |
| 4.7 | Bank scam | is_scam=true | | | |
| 4.8 | OTP scam | is_scam=true | | | |
| 4.9 | Lottery scam | is_scam=true | | | |
| 4.10 | Phishing URL | is_scam=true | | | |
| 4.11 | Regional language (Tamil) | handled | | | |
| 4.12 | Unicode/emoji | handled | | | |

## 5. Image Analysis (OCR)

| # | Test Case | Expected | Actual | Status | Notes |
|---|-----------|----------|--------|--------|-------|
| 5.1 | Clean scam screenshot | is_scam=true | | | |
| 5.2 | Clean legit screenshot | is_scam=false | | | |
| 5.3 | Blurry screenshot | graceful | | | |
| 5.4 | Rotated screenshot | graceful | | | |
| 5.5 | Tiny image | graceful | | | |
| 5.6 | Huge image | 200/400 | | | |
| 5.7 | Corrupted file | 400 | | | |
| 5.8 | Missing file | 422 | | | |

## 6. Investigation

| # | Test Case | Expected | Actual | Status | Notes |
|---|-----------|----------|--------|--------|-------|
| 6.1 | Multiple artefacts | 200, full report | | | |
| 6.2 | Empty artefacts | 422 | | | |

## 7. Security

| # | Test Case | Expected | Actual | Status | Notes |
|---|-----------|----------|--------|--------|-------|
| 7.1 | SQL injection payload | sanitized/400 | | | |
| 7.2 | XSS payload | escaped output | | | |
| 7.3 | Large payload (>10MB) | 413/400 | | | |
| 7.4 | Malformed JSON | 422 | | | |
| 7.5 | Invalid file type | 400 | | | |
| 7.6 | Concurrent rapid requests | 429 after limit | | | |
| 7.7 | Rate limit headers present | X-RateLimit-* | | | |
| 7.8 | Redis down: fail-closed | 429/deny + error log | | | |

## 8. Frontend (if applicable)

| # | Test Case | Expected | Actual | Status | Notes |
|---|-----------|----------|--------|--------|-------|
| 8.1 | Navigation works | | | | |
| 8.2 | Text analysis form | | | | |
| 8.3 | Image upload | | | | |
| 8.4 | Loading states | | | | |
| 8.5 | Error states | | | | |
| 8.6 | Mobile layout | | | | |

## 9. Performance

| # | Test Case | Expected | Actual | Status | Notes |
|---|-----------|----------|--------|--------|-------|
| 9.1 | Text analysis P50 | <50ms | | | |
| 9.2 | Text analysis P95 | <100ms | | | |
| 9.3 | Cold start | <5s | | | |
| 9.4 | 100 concurrent users | no errors | | | |

---

## Summary

| Category | Passed | Failed | Skipped | Total |
|----------|--------|--------|---------|-------|
| Installation | | | | |
| Health | | | | |
| Authentication | | | | |
| Text Analysis | | | | |
| OCR | | | | |
| Investigation | | | | |
| Security | | | | |
| Frontend | | | | |
| Performance | | | | |
| **TOTAL** | | | | |

## Bugs Found (link to BUG_REPORT_TEMPLATE.md)

| Bug ID | Severity | Summary | Link |
|--------|----------|---------|------|
| | | | |

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| QA Lead | | | |
| Tester | | | |
