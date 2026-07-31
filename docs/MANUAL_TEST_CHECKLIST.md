# Manual Test Checklist — ScamShield RC2

> Generated: 2026-07-31
> Branch: main (commit b789ef9)
> Status: Manual Verification Required

---

## Installation

- [ ] Fresh clone: `git clone https://github.com/kathir-iTech/ScamShield.git`
- [ ] Fresh branch from `main`
- [ ] `cd ScamShield/backend && pip install -r requirements.txt` completes without error
- [ ] `cd ScamShield/frontend && npm ci` completes without error
- [ ] `npm run build` in frontend succeeds (verified in CI)

## Fresh Clone Verification

- [ ] No local `.env` files leaked to git (confirmed: `.env` in `.gitignore`)
- [ ] No `*.joblib` model files tracked by git (confirmed: `.gitignore` excludes `*.joblib`)
- [ ] All secrets excluded (`.gitignore` includes `.env`, `.env.local`)

## Documentation Validation

- [ ] README.md badges accurate (820+ tests, 95.1% accuracy)
- [ ] API_REFERENCE.md paths match actual routes (no `/api/v1/` prefix)
- [ ] `.env.example` lists all active `SCAMSHIELD_*` variables
- [ ] `docs/CRITICAL_ISSUE_VERIFICATION.md` reflects current state
- [ ] `docs/CRITICAL_FIX_REPORT.md` describes all critical fixes
- [ ] `docs/RC2_COMPLETION_REPORT.md` describes RC2 blockers fixed

---

## Authentication

### Login
- [ ] GET `/auth/token` with valid `SCAMSHIELD_CLIENT_API_KEY` in header returns 200 + JWT
- [ ] GET `/auth/token` without API key returns 401 (when `AUTH_ENABLED=true`)
- [ ] GET `/auth/token` with wrong API key returns 401
- [ ] GET `/auth/admin` with valid `SCAMSHIELD_ADMIN_API_KEY` returns admin JWT
- [ ] When `AUTH_ENABLED=false`, all auth endpoints return 404

### JWT
- [ ] Access tokens expire after TTL
- [ ] Refresh tokens rotate (single-use)
- [ ] Reused refresh token is rejected
- [ ] Revoked tokens are rejected on subsequent use
- [ ] Tampered tokens are rejected

### Expired Tokens
- [ ] Expired access token returns 401 with "Token has expired"

### Revoked Tokens
- [ ] Blacklisted token returns 401 on verification

### Missing Tokens
- [ ] Missing `Authorization` header on protected endpoint returns 401

### Invalid API Keys
- [ ] Wrong `CLIENT_API_KEY` returns 401 on `/auth/token`
- [ ] Wrong `ADMIN_API_KEY` returns 401 on `/auth/token/admin`

---

## Backend

### Every Endpoint
- [ ] GET `/health` returns 200 + status "healthy"
- [ ] GET `/ready` returns 200 + ready state
- [ ] GET `/live` returns 200
- [ ] GET `/model/info` returns model metadata
- [ ] POST `/analyze/text` with valid text returns 200 + prediction
- [ ] POST `/analyze/image` with valid image returns 200 + prediction
- [ ] POST `/analyze/investigation` returns full investigation
- [ ] POST `/auth/token` with valid API key returns token (when AUTH_ENABLED=true)
- [ ] POST `/auth/admin` with valid admin key returns admin token (when AUTH_ENABLED=true)
- [ ] POST `/auth/refresh` with valid refresh token returns new access token
- [ ] POST `/auth/logout` with valid token invalidates token
- [ ] POST `/auth/revoke` with valid token + auth returns success
- [ ] POST `/auth/verify` with valid token returns payload info

### Status Codes
- [ ] 200 for successful requests
- [ ] 400 for malformed input
- [ ] 401 for unauthenticated requests (when AUTH_ENABLED=true)
- [ ] 403 for unauthorized requests
- [ ] 404 for missing endpoints
- [ ] 413 for oversized payloads
- [ ] 429 for rate-limited requests
- [ ] 500 for internal errors

### Headers
- [ ] `X-RateLimit-Limit` present on rate-limited endpoints
- [ ] `X-RateLimit-Remaining` present on rate-limited endpoints
- [ ] `X-RateLimit-Reset` present on rate-limited endpoints
- [ ] Security headers present (X-Content-Type-Options, X-Frame-Options, etc.)
- [ ] CORS headers correct for allowed origins

### Rate Limiting
- [ ] Requests exceeding limit return 429
- [ ] Sliding window correctly counts requests
- [ ] Rate limit resets after window expires
- [ ] When Redis is down: `is_blocked` returns True (fail-closed)
- [ ] When Redis is down: `record_request` returns False (fail-closed)
- [ ] When Redis is down: `remaining` returns 0 (fail-closed)

### Error Handling
- [ ] Malformed JSON returns 422
- [ ] Empty text returns 400 with error detail
- [ ] Oversized text returns 413
- [ ] Invalid image file returns 400

---

## Frontend

### Navigation
- [ ] Sidebar navigation works
- [ ] URL routing works (React Router)
- [ ] Deep links work on direct load
- [ ] Browser back/forward works

### Forms
- [ ] Text analysis form submits correctly
- [ ] Image upload works
- [ ] API key input works (when auth enabled)
- [ ] Form validation works

### Accessibility
- [ ] All form elements have labels
- [ ] Keyboard navigation works
- [ ] Screen reader announces results
- [ ] Color contrast meets WCAG AA

### Responsive Layouts
- [ ] Desktop view (≥1024px) renders correctly
- [ ] Tablet view (768-1024px) renders correctly
- [ ] Mobile view (<768px) renders correctly

### Dark Mode
- [ ] Light/dark theme toggle works (if applicable)

### Loading
- [ ] Loading spinner shows during analysis
- [ ] Progress indicators for long-running operations

### Errors
- [ ] Network errors display user-friendly messages
- [ ] Validation errors display inline
- [ ] 429 rate limit errors display correctly

---

## AI

### Legitimate SMS
- [ ] "OK lar... joking wif u oni" classified as safe
- [ ] "Thanks for subscribing to our newsletter" classified as safe
- [ ] Confidence score low for legitimate messages

### Scam SMS
- [ ] "URGENT: Your account will be deactivated" classified as scam
- [ ] "Congratulations! You won 50 Lakh in our lottery" classified as scam
- [ ] "Double your investment in 30 days" classified as scam

### UPI Scams
- [ ] UPI payment scam patterns correctly detected
- [ ] "Scan the QR code to receive cashback" flagged

### Bank Scams
- [ ] Bank impersonation patterns detected (ICICI, SBI, etc.)
- [ ] Fake customer care numbers detected

### OTP
- [ ] OTP-based scams detected
- [ ] "Your OTP is 482916" flagged correctly

### Lottery
- [ ] Lottery win scams detected
- [ ] "You won 50 Lakh" classified as scam

### Phishing
- [ ] Suspicious URL detection works
- [ ] "Click here to update your KYC" flagged

### Regional Language
- [ ] Tamil text handled correctly
- [ ] Hindi text handled correctly
- [ ] Tanglish (Tamil+English) handled correctly

### Emoji
- [ ] Messages with emojis analyzed correctly

### Unicode
- [ ] Unicode spoofing detected (e.g., homoglyph attacks)

---

## OCR

### Clean Screenshots
- [ ] Clean screenshot with legible text extracts correctly

### Blurry
- [ ] Blurry screenshot handled gracefully (returns safe/error as appropriate)

### Rotated
- [ ] Rotated screenshot handled gracefully

### Huge
- [ ] Large image within 10MB limit processed correctly

### Tiny
- [ ] Tiny image processed correctly

### Corrupted
- [ ] Corrupted image file returns appropriate error

---

## Security

### SQL Injection
- [ ] SQL injection payloads in text fields are sanitized, not executed

### XSS
- [ ] Script tags in input are escaped in output

### Large Payloads
- [ ] Requests exceeding `max_request_body_size` return 413

### Malformed JSON
- [ ] Invalid JSON body returns 422

### Invalid Files
- [ ] Non-image files sent to image endpoint return 400

### Concurrent Abuse
- [ ] Rapid requests from same IP are rate-limited
- [ ] Different IPs are tracked independently

---

## Infrastructure

### Redis Restart
- [ ] Rate limiter fails closed when Redis restarts (denies requests)
- [ ] Operators receive ERROR logs when Redis fails

### Backend Restart
- [ ] Backend restarts cleanly
- [ ] Model loads correctly on warm restart
- [ ] Health endpoint returns 200 after restart

### Frontend Restart
- [ ] Frontend serves correctly after restart
- [ ] No stale cached state

### Container Restart
- [ ] Backend container starts correctly with `readOnlyRootFilesystem: true`
- [ ] Model files accessible from read-only filesystem
- [ ] `/tmp` writable via emptyDir volume

### Kubernetes Rollout
- [ ] `kubectl rollout status` completes successfully
- [ ] Rolling update replaces old pods with new ones
- [ ] No downtime during rollout

### Rollback
- [ ] `kubectl rollout undo` works
- [ ] Previous pod version restored

---

## Browsers

### Chrome
- [ ] All pages render correctly
- [ ] All interactions work

### Edge
- [ ] All pages render correctly
- [ ] All interactions work

### Firefox
- [ ] All pages render correctly
- [ ] All interactions work

### Mobile
- [ ] Touch interactions work
- [ ] Layout adapts to mobile viewport

---

## Performance

### Latency
- [ ] Text analysis P50 < 50ms
- [ ] Text analysis P95 < 100ms
- [ ] Inference P50 < 3ms per 1000 chars
- [ ] Cold start < 1s after warmup

### Memory
- [ ] Backend memory stays within 512MB limit
- [ ] No memory leaks after sustained load

### CPU
- [ ] CPU usage proportional to request volume
- [ ] No runaway processes

### Concurrent Users
- [ ] 100 concurrent users handled without errors
- [ ] Rate limiting activates correctly at limit

---

## Bug Tracking

See `BUG_TRACKER.md` for active bugs and their status.

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| QA Lead | | | |
| SRE | | | |
| Security Engineer | | | |
| ML Engineer | | | |
| Release Manager | | | |
