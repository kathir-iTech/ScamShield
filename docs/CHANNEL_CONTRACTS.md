# Channel Contracts

One API, many channels. Every channel (web app, browser extension, and the scaffolded bots / SMS forwarder) talks to
the same backend through the same request, auth, error, and rate-limit contract described here. Read this before
writing a new channel.

Status legend: **live** = implemented and reachable today; **contract** = the shape the web client is already coded
against, not yet implemented server-side; **scaffold** = documented but deliberately not built (see
`docs/REPORT_08_THINGS_NOT_TO_BUILD.md`).

---

## 1. Base URL and routing

| Channel | Base URL | Notes |
| --- | --- | --- |
| Web app (dev) | `/api` on `http://localhost:5173` | Vite dev server proxies `/api/*` to the backend and strips the prefix. |
| Web app (prod) | `VITE_API_BASE_URL` or `/api` | Set `VITE_API_BASE_URL` to the backend origin when the SPA and API are on different hosts. |
| Backend | `http://localhost:8000` | `uvicorn backend.main:app`. Interactive docs at `/docs`, `/redoc`. |
| Browser extension | user-configured API base, default `http://localhost:8000` | Stored in `chrome.storage.sync`. No `/api` prefix — call the backend origin directly. |
| Bots / SMS forwarder (scaffold) | full backend origin | Server-to-server; no CORS applies, but the same auth, error, and rate-limit rules do. |

CORS: the backend allows only the origins in `SCAMSHIELD_CORS_ORIGINS` (comma separated). The development profile
defaults to `http://localhost:3000`, `http://localhost:5173`, `http://localhost`. Allowed request headers are
`Authorization`, `Content-Type`, `X-Request-ID`, `X-Admin-Key`; allowed methods are `GET`, `POST`, `OPTIONS`.
**A new browser-based channel must have its origin added before it can call the API.**

---

## 2. Endpoint inventory

| Method | Path | Auth | Rate limit | Status |
| --- | --- | --- | --- | --- |
| POST | `/analyze/text` | optional Bearer | global | live |
| POST | `/analyze/image` | optional Bearer | global | live |
| POST | `/analyze/investigation` | optional Bearer | global | live |
| POST | `/auth/token` | `X-Admin-Key` = `CLIENT_API_KEY` | 20 / 60 s / IP | live |
| POST | `/auth/token/admin` | `X-Admin-Key` = `ADMIN_API_KEY` | 10 / 60 s / IP | live |
| POST | `/auth/refresh` | body `refresh_token` | 20 / 60 s / IP | live |
| POST | `/auth/logout` | body `refresh_token` | 20 / 60 s / IP | live |
| POST | `/auth/revoke` | Bearer | 20 / 60 s / IP | live |
| POST | `/auth/verify` | body token | 20 / 60 s / IP | live |
| POST | `/auth/register` | none | 20 / 60 s / IP | contract |
| POST | `/auth/login` | none | 20 / 60 s / IP | contract |
| GET | `/auth/me` | Bearer required | 20 / 60 s / IP | contract |
| POST | `/feedback` | optional Bearer | 30 / 60 s / IP | live (router) |
| GET | `/health`, `/ready`, `/live`, `/model/info`, `/version` | none | global | live |
| GET | `/metrics` | none | excluded from counting | live |

`/analyze/*` requests are capped at `MAX_TEXT_LENGTH` (default 10000 characters) and `MAX_FILE_SIZE_MB` (default 10,
types: jpeg / png / webp / bmp).

A router is only reachable after it is included in `backend/main.py`. `routers/feedback.py` exists and imports
cleanly; mounting it is the orchestrator's step.

### Analysis request and response

```jsonc
// POST /analyze/text
{ "text": "Your Aadhaar KYC is expiring. Click https://fake-kyc.com to update." }
```

The response is `AnalysisResponse` (`backend/schemas/responses.py`): `prediction`, `confidence`, `risk_level`,
`scam_category`, `detected_indicators`, `recommended_actions`, `summary`, `reasons`, entity and evidence blocks, and
the decision / assessment / investigation blocks. Channels should treat unknown fields as additive — never switch on
them exhaustively.

### Feedback request and response

```jsonc
// POST /feedback  → 202 Accepted
{
  "analysis_id": "7f3c…",          // optional, default ""
  "verdict": "correct",            // required: "correct" | "incorrect" | "unsure"
  "corrected_label": "Job Scam",   // optional, ≤120 chars
  "note": "The payout promise is the tell."  // optional, ≤4000 chars, PII-masked on store
}
// 202 { "detail": "Feedback accepted", "id": "<server generated id>" }
```

`verdict` is validated server-side; anything else is a `422`.

---

## 3. Authentication and roles

- Roles: `guest`, `authenticated`, `admin`.
- Auth is off by default (`AUTH_ENABLED = false`); when off, `/auth/token`, `/auth/token/admin` return **404**.
- Tokens are JWTs: `POST /auth/token` (client key) or `POST /auth/token/admin` (admin key) →
  `{access_token, refresh_token, token_type: "bearer", expires_in}`; access TTL 3600 s, refresh TTL 30 days.
- Send `Authorization: Bearer <access_token>`.
- Web client session: `{access_token, refresh_token, token_type, expires_in, role}`; a failed `GET /auth/me` during
  boot clears the local session.
- On `401` the web client performs **one** `POST /auth/refresh` and replays the original request; if the refresh fails
  the session is cleared and the user is redirected to `/login`. Channels should copy this single-flight behaviour —
  never fire parallel refreshes.

---

## 4. Error shape

Every error body is JSON with a human-readable `detail`:

```jsonc
{ "detail": "Invalid client API key" }
```

Validation failures use FastAPI's default `422` payload, where `detail` is an **array** of
`{loc, msg, type}` objects. Clients must handle both shapes:

- `typeof detail === "string"` → show it.
- `Array.isArray(detail)` → show `detail.map(d => d.msg).join("; ")`.

| Status | Meaning | Channel guidance |
| --- | --- | --- |
| 400 | masked / handled server error | show `detail` |
| 401 | missing or invalid credentials | refresh once, then re-authenticate |
| 403 | key present but not authorised | show `detail`, do not retry |
| 404 | unknown route, or auth disabled | check base URL / path |
| 413 | body over `MAX_REQUEST_BODY_SIZE` | shrink the payload |
| 422 | request failed validation | show `detail` list |
| 429 | rate limited | honour `Retry-After`, back off |
| 500 | server error | retry with backoff only on idempotent calls |

---

## 5. Rate limiting

Applied per client IP in two layers:

1. **Global middleware** — `SCAMSHIELD_RATE_LIMIT_MAX` / `SCAMSHIELD_RATE_LIMIT_WINDOW` (dev profile: 200 / 60 s).
   Adds `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` to every response and returns `429` with
   `Retry-After` when exceeded.
2. **Per-endpoint limiters** — auth endpoints (20 or 10 / 60 s), `/feedback` (30 / 60 s, overridable with
   `SCAMSHIELD_FEEDBACK_RATE_LIMIT_MAX` and `SCAMSHIELD_FEEDBACK_RATE_LIMIT_WINDOW`). These also emit the three
   `X-RateLimit-*` headers; a `429` from `/feedback` carries `Retry-After`.

Header semantics:

| Header | Meaning |
| --- | --- |
| `X-RateLimit-Limit` | Requests allowed in the current window. |
| `X-RateLimit-Remaining` | Requests left in the current window. |
| `X-RateLimit-Reset` | Unix time (seconds) when the window resets. |
| `Retry-After` | Seconds to wait after a `429`. |

Channels must throttle themselves using `X-RateLimit-Remaining` before they are forced to handle `429`.

---

## 6. Idempotency

- **Idempotent:** `GET` endpoints, `/auth/verify`, `/auth/logout` (revoking twice is safe).
- **Not idempotent:** `POST /feedback` generates a fresh `id` per call, and `POST /analyze/*` creates a new analysis
  each time. **There is no `Idempotency-Key` header today.** Do not blindly retry these on `5xx` — retry only on
  network errors where no response was received, with exponential backoff, and never more than once.
- Channels that need dedupe (a bot receiving the same message twice) must key on their own message identifier and
  skip submissions they have already made.

---

## 7. Versioning and compatibility

- The API is **unversioned**: no `/v1` prefix. The version is reported by `GET /version` (`core.constants.API_VERSION`)
  and by the OpenAPI document at `/docs`.
- Compatibility rules for channels:
  - Ignore fields you do not recognise; never send unknown fields (request bodies use `extra: "forbid"` where
    defined).
  - Additive response fields, new endpoints, and new optional request fields are non-breaking.
  - Renaming/removing a field, changing a status code, or tightening validation is breaking and requires a coordinated
    client update.
- A breaking change must land with a channel-major bump, not silently.

---

## 8. Channel-specific contracts

### Web app

Spa routes: `/dashboard`, `/recovery`, `/upi`, `/feedback`, `/login`, `/register`, catch-all `/`. Auth state lives in
`frontend/src/features/auth`; API access in `frontend/src/services/api.ts`.

### Browser extension (`extension/`)

Unofficial MV3 companion. POSTs the selected (or visible page) text to `{apiBase}/analyze/text`, optionally with
`Authorization: Bearer <token>` from `chrome.storage.sync`. Handles 401/403/404/429/5xx/network failures explicitly;
never retries `429` without `Retry-After`.

### Telegram bot (scaffold — not implemented)

Accepts inbound updates, extracts message text, calls `POST /analyze/text`, replies with
`prediction` + `risk_level` + `recommended_actions`. Must throttle: one outbound API call per inbound message, respect
`X-RateLimit-Remaining`, and never store raw user messages.

### WhatsApp bot (scaffold — not implemented)

Same contract as the Telegram bot, over the WhatsApp Business webhook. Must verify the webhook signature, answer
`GET` verification challenges, and answer webhook callbacks within the platform timeout (send `200` first, analyse
asynchronously if needed).

### Android SMS forwarder (scaffold — not implemented)

A user-installed app that forwards SMS text to `POST /analyze/text` and surfaces the verdict as a notification. The
forwarder is the consent boundary: it must forward only messages the user explicitly opted in to share, must send a
Bearer token, and must drop messages locally if the API returns `429`.

---

## 9. Shared rules for every channel

1. One analysis per request; never batch unrelated users' content into a single call.
2. Do not log or transmit raw message content beyond the API call itself.
3. Show `risk_level` and `recommended_actions` — not just `prediction` — to users.
4. Attach the analysis id to any feedback you submit.
5. Treat `429` as a normal, expected condition, not an error to surface as a failure.
