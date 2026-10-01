# WhatsApp Bot (scaffold)

**Status: not implemented.** This directory contains no code, only the contract a future implementation must follow.
See `docs/REPORT_08_THINGS_NOT_TO_BUILD.md` (Mobile App, item 9): a WhatsApp bot is one of the validation steps to run
before investing in a native app.

## What it would do

1. Receive an inbound message through the Meta WhatsApp Cloud API webhook.
2. Send the message text to `POST {SCAMSHIELD_API_BASE}/analyze/text`.
3. Reply with `prediction`, `risk_level`, `scam_category`, and `recommended_actions`, plus a **Report** action that
   calls `POST /feedback`.

## Contract

Defined in `docs/CHANNEL_CONTRACTS.md`:

- Analysis: `POST /analyze/text` with `{"text": "..."}` → `AnalysisResponse`.
- Feedback: `POST /feedback` with `{"analysis_id", "verdict", "corrected_label", "note"}` → `202`.
- Auth: optional `Authorization: Bearer <access_token>`; required when `AUTH_ENABLED=true`.
- Errors: `{"detail": "..."}`; `422` returns a `detail` array.
- Rate limits: read `X-RateLimit-Remaining`; on `429` wait `Retry-After` and reply later instead of failing loudly.
- Idempotency: both POSTs are non-idempotent — WhatsApp redelivers webhook events, so de-duplicate on `message.id`.

## Platform constraints that shape the code

| Constraint | Consequence |
| --- | --- |
| Webhook `GET` verification | Answer the `hub.challenge` echo with `hub.verify_token` validation before any analysis code runs. |
| Webhook `POST` timeout | Return `200` immediately, analyse asynchronously, then send a separate outbound message. |
| 24-hour customer-service window | Free-form replies are only allowed inside the window; outside it use a pre-approved template. |
| Inbound spam | Apply your own per-user throttle (e.g. 10 messages / 10 min) before touching the API. |
| Signature verification | Verify `X-Hub-Signature-256` (HMAC-SHA256 with the app secret) on every webhook — never trust the URL alone. |

## Suggested implementation

```
scaffolds/whatsapp-bot/
  README.md            <- this file
  app.py               <- HTTP server: webhook verify + receive
  worker.py            <- analysis queue (inbound → API → outbound)
  client.py            <- thin wrapper around POST /analyze/text, /feedback
  requirements.txt     <- fastapi/uvicorn (or flask), httpx, pydantic
```

Environment:

| Variable | Example | Purpose |
| --- | --- | --- |
| `WHATSAPP_VERIFY_TOKEN` | `random-string` | Echoed back on webhook verification. |
| `WHATSAPP_APP_SECRET` | `…` | For `X-Hub-Signature-256`. |
| `WHATSAPP_ACCESS_TOKEN` | `…` | Meta Graph API token for outbound messages. |
| `SCAMSHIELD_API_BASE` | `https://api.example.com` | Backend origin, no `/api` suffix. |
| `SCAMSHIELD_BOT_API_KEY` | `…` | Sent as `Authorization: Bearer` when auth is enabled. |

Implementation checklist:

- [ ] `GET /webhook` verification (`hub.mode`, `hub.verify_token`, `hub.challenge`).
- [ ] `POST /webhook` signature check → `200` → queue → analyse → reply.
- [ ] Per-sender de-duplication of `message.id`.
- [ ] Template message for the outside-window case.
- [ ] `/privacy` and `/stop` handlers; `/stop` cancels further forwarding for that sender.
- [ ] Backoff on `429`, single retry at most on network errors for `/feedback`.

## Design rules

- **Consent first.** The bot analyses messages a user sends it. It must never request read access to a user's chat
  history.
- **No raw message retention** on the bot side; the API stores the analysis, not the conversation.
- **No LLM calls in the bot** (`REPORT_08` item 7): analysis is server-side only.
- **Unofficial companion**: state that the bot is repo-local and not an official ScamShield distribution channel, and
  comply with Meta's platform policy before any public deployment.

## Why it is not built yet

Per `docs/REPORT_08_THINGS_NOT_TO_BUILD.md`: build it only when there is evidence users want a WhatsApp interface.
When implementing it, replace this README with real usage docs in the same PR that adds `app.py`.
