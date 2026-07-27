# Things Not To Build

## 1. A Mobile App (Yet)

**Why not now**: Before you have sub-20% FPR and a browser extension validated, a mobile app multiplies complexity (push notifications, SMS permissions, app store reviews, 2 platforms) without solving the core problem: detection quality.

**Build instead**: Progressive Web App (PWA) — same codebase, installable on mobile, push notifications. The frontend is already a React SPA; adding a service worker and manifest.json is 2 days of work.

**When to build it**: After FPR < 10%, browser extension validated with 1000+ real users, and you have a dedicated mobile engineer.

---

## 2. A Chrome Extension (Yet)

**Why not now**: The API doesn't support the use case. A browser extension needs real-time page analysis (check links, scan forms), not message analysis. The entire pipeline is designed for text messages, not web pages.

**Build instead**: Wait until there's a web content analysis pipeline, or build a simple "right-click → check URL" extension that uses the existing `/api/v1/analyze` endpoint.

**When to build it**: After URL-specific analysis is added to the pipeline (different from message analysis — need to check page content, not just URLs).

---

## 3. User Accounts with Social Login

**Why not now**: Persistence doesn't exist yet. Adding Google/GitHub OAuth before basic SQLite storage is backwards. You'd be storing user tokens with nowhere to put user data.

**Build instead**: Anonymous usage tracking (just a client-generated UUID in localStorage). You get usage metrics without accounts.

**When to build it**: After SQLite persistence, then add accounts with email+password first, social login later.

---

## 4. Real-Time SMS Filtering

**Why not now**: Requires OS-level integration (Android SMS Receiver API, iOS Message Filter extension), carrier partnerships, or a custom keyboard app. This is a 6-12 month project on its own.

**Build instead**: "Share to ScamShield" — let users share suspicious messages from their messaging app to ScamShield (mobile web). This is a 1-line Android intent filter.

**When to build it**: Never, unless you have carrier partnerships or a dedicated mobile OS team.

---

## 5. A Scam Reporting Community/Forum

**Why not now**: User moderation is a full-time job. Scam forums attract scammers, trolls, and legal liability. You don't want to become a platform for sharing scam techniques.

**Build instead**: Anonymized, curator-reviewed scam pattern database. Internal only, published as curated threat intelligence feeds.

**When to build it**: Never in public form. If you need community, use existing platforms (Reddit r/scams, Twitter) and aggregate data.

---

## 6. Multi-Language Support (Full i18n)

**Why not now**: The detection pipeline only supports English + Hinglish + Tamil. Full i18n (French, Spanish, Arabic, etc.) requires:
- New ML training data per language
- New rule patterns per language
- New entity extraction per language
- UI translation maintenance

**Build instead**: Expand to the top 5 Indian languages (Hindi, Bengali, Telugu, Marathi, Tamil) — largest addressable market, shared scam patterns.

**When to build it**: After the product is validated in India with < 10% FPR in supported languages.

---

## 7. Blockchain-Based Verification

**Why not now**: Blockchain adds zero value to scam detection. Scam reports don't need immutability (they're not financial transactions). Decentralization makes it harder to update detection rules and remove false reports.

**Build instead**: Content-addressed storage (IPFS) for report evidence if you need tamper-proof archiving.

**When to build it**: Never.

---

## 8. AI Chatbot for User Support

**Why not now**: An AI chatbot that answers "is this a scam?" would be answering the same question as the core product, but worse (no evidence graph, no pipeline, no connectors). It would confuse users about which tool to use.

**Build instead**: A clear FAQ page, a sample analysis gallery, and a feedback form.

**When to build it**: Never for scam analysis. You can add a general support chatbot for product questions after you have 10K+ users.

---

## 9. Premium Subscription Tiers

**Why not now**: There's nothing to charge for yet. The product is free, no accounts, no history, no batch API, no SLA. Charging for the current product would feel like a scam itself.

**Build instead**: Understand willingness to pay first. Survey users, build the features they'd pay for (batch API, SLA, priority support, audit trail), then monetize.

**When to build it**: After you have 1000+ weekly active users and features that enterprise customers will pay for.

---

## 10. A Native Desktop App (Electron/Tauri)

**Why not now**: The web app works perfectly for the current use case. A desktop app adds:
- 50+ MB download for what's currently a webpage
- Update management, crash reporting, native installer
- Split codebase (main/renderer process)

**Build instead**: PWA with desktop install support. Chrome and Edge already support "Install as app".

**When to build it**: Never. If you need native features (file system access, OS notifications), add them via the PWA.
