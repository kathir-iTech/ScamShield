# OWASP API Top 10 — Penetration Checklist

## API1: Broken Object Level Authorization
| Check | Status | Mitigation |
|---|---|---|
| Can user access another user's investigation results? | ✅ Protected | Investigation endpoint requires admin role via `require_admin()` dependency |
| Can user enumerate artefact IDs? | ✅ Protected | No ID-based resource access pattern exists |
| Is there horizontal privilege escalation? | ✅ Mitigated | All authenticated users share same access level; admin is server-controlled |

## API2: Broken Authentication
| Check | Status | Mitigation |
|---|---|---|
| Can admin tokens be minted without auth? | **✅ FIXED** | `/auth/token/admin` now requires `AdminAuthRequest` with server-controlled `admin_key` |
| Are JWT roles client-asserted? | **✅ FIXED** | Role is set server-side via `create_access_token()` — never read from client input |
| Can refresh tokens be replayed? | **✅ FIXED** | `mark_refresh_used()` detects reuse; reused tokens are blacklisted |
| Can expired tokens be used? | **✅ FIXED** | `decode_token()` validates `exp` with configurable clock skew tolerance |
| Can forged tokens be accepted? | **✅ FIXED** | HMAC-SHA256 signature verification; tampered payloads detected |
| Is there a logout mechanism? | **✅ ADDED** | `/auth/logout` blacklists refresh tokens |
| Can tokens be revoked? | **✅ ADDED** | `/auth/revoke` endpoint blacklists any token by jti |
| Is token type enforced for refresh? | **✅ FIXED** | Refresh endpoint rejects non-refresh tokens |
| Clock skew handled? | **✅ FIXED** | 30-second configurable leeway on both `exp` and `iat` |

## API3: Broken Object Property Level Authorization
| Check | Status | Mitigation |
|---|---|---|
| Can client specify extra fields in requests? | **✅ FIXED** | All request schemas use `model_config = {"extra": "forbid"}` — unexpected fields rejected |
| Can client modify read-only properties? | ✅ N/A | No read-only/modifiable property distinction in current API |

## API4: Unconstrained Resource Consumption
| Check | Status | Mitigation |
|---|---|---|
| Is there a text length limit? | ✅ Present | `MAX_TEXT_LENGTH` enforced both at schema level (10K) and service level (`validate_text_length`) |
| Is there an image file size limit? | ✅ Present | `MAX_FILE_SIZE_MB` (10MB) enforced in analyze router |
| Is there an image dimension limit? | **✅ ADDED** | `_MAX_IMAGE_DIMENSION` (8000px) enforced via `PIL.Image.open()` check |
| Is there a request body size limit? | ✅ Present | `RequestBodySizeMiddleware` rejects bodies > `MAX_REQUEST_BODY_SIZE` |
| Is there a JSON nesting depth limit? | **✅ ADDED** | `JSONStructureValidator` middleware rejects nesting > 16 levels |
| Is there a JSON array length limit? | **✅ ADDED** | `JSONStructureValidator` rejects arrays > 500 elements |
| Is there a JSON field count limit? | **✅ ADDED** | `JSONStructureValidator` rejects objects > 200 fields |
| Is there per-IP rate limiting? | ✅ Present | `SlidingWindowRateLimitMiddleware` with graduated blocking (3 violations → 60s block) |
| Are rate limit headers returned? | ✅ Present | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` |
| Is there a request timeout? | ✅ Present | `RequestTimeoutMiddleware` (30s default) |
| Are uploaded file names sanitized? | **✅ ADDED** | `_sanitise_filename()` strips path traversal chars, restricts extensions |

## API5: Broken Function Level Authorization
| Check | Status | Mitigation |
|---|---|---|
| Can non-admin access investigation endpoint? | **✅ FIXED** | `require_admin()` dependency on `/analyze/investigation` |
| Can guest access authenticated endpoints? | ✅ Protected | `require_auth()` dependency on protected routes |
| Is role checked server-side? | **✅ FIXED** | `_build_user()` in `deps.py` validates payload role against `UserRole` enum; `_ROLE_RANK` for hierarchy |

## API6: Unrestricted Access to Sensitive Business Flows
| Check | Status | Mitigation |
|---|---|---|
| Can attacker mass-analyze messages? | ✅ Mitigated | Rate limiting by IP with graduated blocking |
| Can attacker use investigation as oracle? | ✅ Mitigated | Admin-only access to investigation endpoint |

## API7: Server Side Request Forgery
| Check | Status | Mitigation |
|---|---|---|
| Can connector URLs be manipulated? | ✅ N/A | Connector targets are hardcoded (Google Safe Browsing API); no user-supplied URLs |
| Can image paths be manipulated? | ✅ Mitigated | Uploaded files go to temp dir via `tempfile.NamedTemporaryFile`; original filename not used for path |

## API8: Security Misconfiguration
| Check | Status | Mitigation |
|---|---|---|
| Are security headers set? | ✅ Present | `SecurityHeadersMiddleware`: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, CSP (on HTML), HSTS (on HTML) |
| Is CORS properly configured? | ✅ Present | CORS middleware with configurable origins; wildcard blocked in production |
| Is debug mode disabled in production? | ✅ Verified | `validate_config()` enforces `DEBUG=False` in production |
| Is the API version exposed? | ✅ Present | Via `/version` endpoint and Swagger UI |
| Are stack traces hidden in production? | ✅ Present | `global_exception_handler` returns generic 500 |
| Is PII masked in logs? | ✅ Present | `_mask_pii()` in main.py redacts phones, emails, credit cards, Aadhaar, PAN |
| Is JWT secret validated at startup? | ✅ Present | `validate_config()` requires `AUTH_JWT_SECRET` when `AUTH_ENABLED=true` |
| Is admin API key validated at startup? | **✅ ADDED** | `validate_config()` requires `ADMIN_API_KEY` when `AUTH_ENABLED=true` |

## API9: Improper Inventory Management
| Check | Status | Mitigation |
|---|---|---|
| Are deprecated endpoints documented? | ✅ Present | Swagger/ReDoc auto-generated |
| Is the API versioned? | ⚠️ Partial | `API_VERSION` constant exists but no URL path prefix |
| Are staging/dev APIs isolated? | ✅ Present | Environment profiles with different configs |

## API10: Unsafe Consumption of APIs
| Check | Status | Mitigation |
|---|---|---|
| Are connector TLS certificates verified? | ✅ Present | httpx default verify=True |
| Do connectors have timeouts? | ✅ Present | Configurable per-connector timeout (default 10-15s) |
| Do connectors have circuit breakers? | ✅ Present | `CircuitBreaker` in core.resilience, applied to Google Safe Browsing |
| Do connectors have retry logic? | ✅ Present | `retry()` decorator with exponential backoff + jitter |

---

## Summary

| Category | Items Protected | Items Fixed This Sprint |
|---|---|---|
| Authentication | 7/7 | Admin token, role assertion, refresh rotation, logout, revocation, clock skew |
| Authorization | 3/3 | Server-side roles, RBAC on investigation, role hierarchy |
| Input Validation | 10/10 | Text length, image size, image dimensions, body size, JSON nesting, JSON array length, JSON field count, filename sanitization, MIME type, extra fields |
| Rate Limiting | 4/4 | Per-IP, graduated blocking, headers, timeout |
| Security Headers | 7/7 | CSP, HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy |
| PII Protection | 1/1 | Log masking |
| Configuration | 6/6 | Secret validation, admin key, debug mode, CORS, env profiles, startup validation |
