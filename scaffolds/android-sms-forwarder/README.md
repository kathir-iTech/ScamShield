# Android SMS Forwarder (scaffold)

**Status: not implemented.** This directory contains no code, only the contract a future implementation must follow.
See `docs/REPORT_08_THINGS_NOT_TO_BUILD.md` (Mobile App, item 9): an SMS forwarder is one of the validation steps to
run before investing in a native app — it is the cheapest way to learn whether users want ScamShield on their phone.

## What it would do

1. Watch for new SMS text (see "Permission strategy" below — the naive `READ_SMS` route is usually a dead end).
2. Send the text to `POST {SCAMSHIELD_API_BASE}/analyze/text` with a Bearer token.
3. Post a local notification: **SCAM - Phishing (risk HIGH)** plus `recommended_actions`.
4. Optional: user taps **Report** → `POST /feedback` with the analysis id.

## Contract

Defined in `docs/CHANNEL_CONTRACTS.md`:

- Analysis: `POST /analyze/text` with `{"text": "..."}` → `AnalysisResponse`.
- Feedback: `POST /feedback` with `{"analysis_id", "verdict", "corrected_label", "note"}` → `202`.
- Auth: `Authorization: Bearer <access_token>` from `POST /auth/token`; the app must store it in EncryptedSharedPreferences.
- Errors: `{"detail": "..."}`; `422` returns a `detail` array.
- Rate limits: read `X-RateLimit-Remaining`; on `429` back off using `Retry-After` and **do not drop the message** —
  queue it locally instead.
- Idempotency: both POSTs are non-idempotent. Key the local queue on `Sms.Message.getId()` so a process restart does
  not re-submit the same SMS.
- Network failures: exponential backoff with a bounded local queue (e.g. 100 messages), then give up and tell the user.

## Permission strategy

| Approach | Permission | Trade-off |
| --- | --- | --- |
| Default SMS handler | `READ_SMS`, `RECEIVE_SMS` | Highest trust signal, but requires becoming the user's default SMS app — far beyond a forwarder. |
| Notification listener | `BIND_NOTIFICATION_LISTENER_SERVICE` | **Recommended.** Reads the incoming-message notification rendered by the user's existing SMS app; no `READ_SMS`. |
| User-initiated share | none | Text is forwarded only when the user shares it into the app. Lowest risk, lowest coverage. |

Play Store restricts `READ_SMS`/`RECEIVE_SMS` to default-SMS-handler apps, so the notification-listener path is the one
to build unless the app is distributed outside the store. The forwarder must show, on first launch, exactly which
messages are sent where, and offer a kill switch.

## Suggested implementation

```
scaffolds/android-sms-forwarder/
  README.md                      <- this file
  app/src/main/AndroidManifest.xml
  app/src/main/java/.../MainActivity.kt      <- consent, settings, kill switch
  app/src/main/java/.../SmsListenerService.kt <- notification listener → queue
  app/src/main/java/.../AnalysisClient.kt     <- POST /analyze/text, /feedback
  app/src/main/java/.../Notifier.kt           <- local notifications
```

Environment / config (in-app, not in the repo):

| Setting | Example | Purpose |
| --- | --- | --- |
| API base URL | `https://api.example.com` | Backend origin, no `/api` suffix. |
| API token | `…` | From `POST /auth/token`; refresh with `POST /auth/refresh`. |
| Forward toggle | on / off | Global kill switch, checked before every network call. |
| Sensitive senders | `Bank`, `KYC` | Optional allow-list / block-list. |

Implementation checklist:

- [ ] First-run consent screen naming the exact data, destination, and retention.
- [ ] Notification-listener connection check with a "service disabled" prompt.
- [ ] Local queue with unique SMS id, bounded size, exponential backoff.
- [ ] `POST_NOTIFICATIONS` runtime request (Android 13+); foreground service while syncing.
- [ ] Battery optimisation exemption prompt only if the queue demonstrably misses messages.
- [ ] Local-only mode: analyse on-device via the existing rules engine when offline.
- [ ] Uninstall/kill switch that stops all forwarding immediately.

## Design rules

- **Consent is the product.** No silent forwarding; the user can see and clear the queue.
- **Never store message content beyond the queue** — the API keeps the analysis, the phone keeps nothing.
- **One SMS in, one analysis out.** No batching, no contact scraping, no location, no MMS/attachment upload in v1.
- **No LLM calls on the device** (`REPORT_08` item 7): analysis is server-side or rules-only.
- Unofficial companion: label the app as a repo-local build, not an official ScamShield distribution channel.

## Why it is not built yet

Per `docs/REPORT_08_THINGS_NOT_TO_BUILD.md`: a native app needs its own codebase, store submission, and maintenance —
prove demand with a bot/forwarder first. When implementing it, replace this README with real usage docs in the same PR
that adds the first Kotlin sources.
