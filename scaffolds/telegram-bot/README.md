# Telegram Bot (scaffold)

**Status: not implemented.** This directory contains no code, only the contract a future implementation must follow.
See `docs/REPORT_08_THINGS_NOT_TO_BUILD.md` (Mobile App, item 9): Telegram / WhatsApp bots and an SMS forwarder are the
validation steps to run *before* investing in a native app.

## What it would do

1. Receive a message from a user in Telegram.
2. Send the text to `POST {SCAMSHIELD_API_BASE}/analyze/text`.
3. Reply with the verdict card: `prediction`, `risk_level`, `scam_category`, `recommended_actions`, and a
   **Report** button that calls `POST /feedback`.

```
user:  +91 98765 43210 won your lottery, send KYC at http://bit.ly/xyz
bot:   SCAM - Phishing (risk HIGH, confidence 0.92)
       Recommended: Do not click the link. Block the sender.
       [Correct] [Incorrect]
```

## Contract

Everything request/response-shaped is defined in `docs/CHANNEL_CONTRACTS.md`:

- Analysis: `POST /analyze/text` with `{"text": "..."}` → `AnalysisResponse`.
- Feedback: `POST /feedback` with `{"analysis_id", "verdict", "corrected_label", "note"}` → `202`.
- Auth: optional `Authorization: Bearer <access_token>`; required if the deployment sets `AUTH_ENABLED=true`.
- Errors: `{"detail": "..."}` (string) or `{"detail": [{msg, loc, type}]}` for `422`.
- Rate limits: read `X-RateLimit-Remaining`; on `429` wait `Retry-After` seconds and do not surface a failure message.
- Idempotency: `POST /analyze/text` and `POST /feedback` are **not** idempotent — a Telegram retry (webhook redelivery)
  must be de-duplicated on the bot's own `update_id`.

## Suggested implementation

```
scaffolds/telegram-bot/
  README.md            <- this file
  bot.py               <- polling/webhook loop, command handlers
  client.py            <- thin wrapper around POST /analyze/text, /feedback
  config.py            <- env loading
  requirements.txt     <- python-telegram-bot (or aiogram), httpx, pydantic
```

Environment:

| Variable | Example | Purpose |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | `123456:ABC-…` | From `@BotFather`. |
| `SCAMSHIELD_API_BASE` | `https://api.example.com` | Backend origin, no `/api` suffix. |
| `SCAMSHIELD_BOT_API_KEY` | `…` | Sent as `Authorization: Bearer` when auth is enabled. |

Implementation checklist:

- [ ] `/start`, `/help`, `/privacy` commands.
- [ ] Text handler → `POST /analyze/text` → formatted reply.
- [ ] Inline buttons posting `callback_data` like `fb:<analysis_id>:correct`.
- [ ] Per-chat de-duplication of `update_id` (webhooks redeliver).
- [ ] Exponential backoff on `429` / network errors; never retry `5xx` for `/feedback`.
- [ ] `/privacy`: state that message text is sent to the configured API for analysis and stored only as an analysis
      record.

## Design rules

- **One message in, one analysis out.** No batching, no background crawling of a user's history.
- **Do not persist raw messages** on the bot side beyond the API call; the API already stores the analysis.
- **Rate-limit yourself before the API does** — a flood of `/analyze/text` calls burns the global per-IP budget.
- **No LLM calls in the bot** (see `REPORT_08` item 7): analysis is server-side only.
- Unofficial: state clearly that the bot is a repo-local companion, not an official ScamShield distribution channel.

## Why it is not built yet

Per `docs/REPORT_08_THINGS_NOT_TO_BUILD.md`: build the bot only when there is evidence that users want a Telegram
interface. `REPORT_07_ROADMAP.md` holds the sequencing. If you are implementing it, replace this README with real
usage docs in the same PR that adds `bot.py`.
