# REPORT 2: THREAT MODEL

## 1. Assets

| Asset | Sensitivity | Location | Protection |
|---|---|---|---|
| ML Model file (model.joblib) | Medium | `backend/model.joblib` | None (no integrity check) |
| Training dataset (scam_dataset.csv) | Low (public SMS) | `backend/dataset/` | None |
| JWT Signing Secret | **Critical** | `SECRET_KEY` env var | Env var only, no rotation |
| Rate Limiting State | Low | In-memory | None (lost on restart) |
| Audit Logs | Medium | `audit.py` stdout | Structured JSON, no persistence |
| User-submitted SMS text | Medium | Request body | Transient (not stored) |
| Image uploads | Medium | Temp file during OCR | Deleted after processing |
| API Tokens | **Critical** | `auth.py` | JWT with expiry, no revocation |
| Connector API Keys | Medium | Env vars | None (no encryption at rest) |
| Passive DNS / enrichment results | Low | Response body | Transient |

## 2. Trust Boundaries

```
[User/Browser] → HTTPS → [Nginx] → [FastAPI Backend] → [Tesseract OCR]
                                        → [ML Model]
                                        → [Google Safe Browsing API]
                                        → [WhoisXML API (mock)]
                                        → [VirusTotal API (mock)]
```

- External boundary: User ↔ Backend (authenticated for investigation, anonymous for analysis)
- Internal boundary: Backend ↔ External APIs (Google Safe Browsing, etc.)
- ML model runs in-process — no sandboxing

## 3. Threats by STRIDE

### Spoofing
- **T1: JWT token forgery** — If SECRET_KEY is weak or leaked, attacker can forge any role. Token validation has no key rotation, no JWK, no kid header.
- **T2: API key theft** — Connector API keys stored in env vars; if attacker gains shell access, all keys exposed.

### Tampering
- **T3: Model poisoning** — No integrity check on model.joblib. If file replaced, predictions could be manipulated. No signed checksum.
- **T4: Dataset tampering** — No integrity check on scam_dataset.csv.
- **T5: Request/response tampering** — No request signing. HTTPS relies entirely on TLS. No HMAC or nonce.

### Repudiation
- **T6: No non-repudiation** — Audit logs are stdout-only, no persistence, no signing. Cannot prove who analyzed what when.

### Information Disclosure
- **T7: PII leakage via detailed evidence** — Evidence builder extracts phone numbers, emails, URLs which may be PII. Sent in API response. No redaction control per role.
- **T8: Error message information leakage** — Error handlers return generic messages but traceback may leak in dev mode. No structured error classification.
- **T9: Timing attacks** — Pipeline runtime varies by content. ML confidence + rule matches could leak processing characteristics.

### Denial of Service
- **T10: OCR resource exhaustion** — Large image uploads to `/analyze/image` consume Tesseract process + memory. No file size limit beyond middleware `max_body_size` (10MB default).
- **T11: Pipeline CPU exhaustion** — No request queuing, no concurrency limits per user/endpoint. Burst of analysis requests could saturate CPU.
- **T12: Entity extraction regex DoS** — Entity extraction uses regex; crafted input with exponential backtracking could freeze pipeline. No ReDoS protection.

### Elevation of Privilege
- **T13: Role escalation** — JWT `role` field is client-asserted. No server-side role database. Anyone with valid token can set any role.
- **T14: Admin token bypass** — `/auth/token/admin` creates admin tokens but only logs the event — no actual validation of who can request admin tokens.

## 4. Current Mitigations (Present)

| Threat | Mitigation | Effectiveness |
|---|---|---|
| Brute force login | Rate limiting on auth endpoints | **Partial** — rate limit resets on restart, no per-IP tracking |
| Body size attacks | `max_body_size` middleware (10MB) | **Present** |
| Certificate transparency | Nginx with strong TLS config | **Present** |
| Security headers | Nginx + middleware (HSTS, CSP, etc.) | **Present** |
| Request tracing | Correlation ID middleware | **Present** |
| Input validation | Pydantic schemas + Zod on frontend | **Present** |
| XSS | CSP headers (Nginx) | **Present** |
| CORS | Configured middleware | **Present** |

## 5. Gaps (Missing Mitigations)

| Gap | Severity | Priority | Suggested Fix |
|---|---|---|---|
| No ML model integrity check | **High** | **High** | Add SHA-256 checksum, verify at startup |
| JWT secret hardcoded in env, no rotation | **High** | **Medium** | Add secret rotation support, JWK endpoint |
| No request rate limiting per IP (per-endpoint) | **High** | **High** | Integrate with Redis bucket per IP + path |
| No input size limits for text analysis | Medium | High | Add char limit to text analysis endpoint (e.g. 5000 chars) |
| OCR endpoint has no dimension/pixel limit | Medium | High | Reject images > 4000px on any side |
| Entity extraction regex may be vulnerable to ReDoS | Medium | Medium | Audit all regex patterns, add regex timeout wrap |
| No request signing / nonce | Medium | Low | Add HMAC signature for non-TLS fallback |
| Admin token endpoint has no auth | **Critical** | **Immediate** | Remove or gate behind admin credentials |
| No audit log persistence | Medium | Medium | Add log shipping to file or external sink |
| No secret scanning in CI | Medium | Low | Add `trufflehog` or `git-secrets` to CI |
| No dependency vulnerability scanning | Medium | Medium | Add `pip-audit` or `safety` to CI |
| No SBOM generation | Low | Low | Add `cyclonedx-bom` to CI |
| No container image scanning | Medium | Medium | Add Trivy to CI pipeline |
| No input sanitisation bypass for Unicode | Medium | Medium | Add NFKC normalization before analysis |

## 6. Attack Tree: Bypassing Scam Detection

```
Goal: Submit scam SMS that is classified as "safe"
├── OR 1: Manipulate ML prediction
│   ├── Train adversarial examples (requires model access)
│   └── OR Replace model file (requires filesystem access)
├── OR 2: Bypass rule engine
│   ├── Use Unicode homoglyphs (e.g. "𝓅𝒽𝒾𝓈𝒽𝒾𝓃𝑔")
│   ├── Use URL shorteners + redirect chains
│   └── Split scam indicators across multiple messages
├── OR 3: Exploit pipeline ordering
│   ├── First message passes as safe, second contains scam
│   └── Use context from prior messages to confuse scoring
├── OR 4: Denial of Service
│   ├── Send large request to /analyze/image
│   └── Send regex-crafted input to text endpoint
└── OR 5: Manipulate response
    ├── API returns "safe" before all pipeline steps complete
    └── Exploit race condition in assessment (unlikely - synchronous)
```

## 7. Risk Assessment Summary

| Risk | Likelihood | Impact | Risk Level |
|---|---|---|---|
| JWT secret compromise | Low | Critical | **High** |
| Model poisoning | Low | High | **Medium** |
| ReDoS via crafted input | Medium | Medium | **Medium** |
| OCR resource exhaustion | Medium | Medium | **Medium** |
| Role escalation via forged JWT | Low | High | **Medium** |
| PII leakage in responses | Medium | Medium | **Medium** |
| Admin token abuse | Low | Critical | **High** |
