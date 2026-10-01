# ScamShield Master Audit — Report 06: Product Review

**Date:** 2026-07-26 (original audit) · **Revised:** 2026-10-02 after the security / product / ops / accuracy upgrade

---

## 1. Who Would Use It

| User Segment | Would Use? | Why |
|-------------|------------|-----|
| Indian consumers receiving scam SMS | **Maybe → Yes (web)** | Web app now has registration, login and a feedback loop; a browser extension ships in-repo. Still no Android app or SMS forwarder |
| Indian cyber crime cells (e.g., CERT-In) | **Yes** | Investigation dashboard + campaign detection, now with an audit trail and API keys for access control |
| Telecom operators (Vodafone, Airtel, Jio) | **Maybe** | Could integrate API for network-level SMS filtering; per-instance rate limiting must be solved first |
| Banks (SBI, HDFC, ICICI) | **Maybe** | API with authentication and audit logging is usable for phishing-SMS detection pilots |
| Researchers (ML/NLP security) | **Yes** | Architecture, gold-set evaluation pipeline, frozen thresholds, active-learning queue and leakage reports |
| Security product companies | **Maybe** | API could be licensed/integrated; SLA and support still absent |
| General public | **Maybe** | Browser extension + web accounts now exist; blocked mainly by FPR (14.06%) and no password recovery |

## 2. Who Would Not Use It

| User Segment | Why Not |
|-------------|---------|
| Non-Indian users | Heavy India-specific focus (Indian banks, UPI, Aadhaar, government schemes) |
| Enterprise buyers requiring SSO/SLA | No SSO, no SLA, no support docs — audit trail and API keys are now present |
| General mobile users | No mobile app; WhatsApp/Telegram/Android channels are documented contracts, not implementations |
| International organizations | India-specific scam patterns only |

## 3. Strengths

| Strength | Evidence |
|----------|----------|
| Comprehensive pipeline | 12-stage analysis is thorough — ML + rules + entities + evidence + reasoning + knowledge + connectors |
| Modular architecture | Feature-based frontend, service-based backend, repository-based storage |
| Accounts and sessions | bcrypt hashing, JWT access tokens, revocable refresh tokens, logout-everywhere, API keys |
| Auditability | Immutable audit log covering auth events, with correlation IDs |
| Abuse controls | Sliding-window rate limits with per-route budgets and `X-RateLimit-*` headers |
| Investigation engine | Multi-artefact campaign detection is unique |
| Evaluation framework | Gold-set pipeline, CI regression gate, frozen thresholds, active-learning label queue |
| Documentation | 30+ markdown files plus engineering decisions, channel contracts and an ops runbook |
| CI/CD | Workflows for lint, test, build, security, release, eval and retrain |
| Docker security hardening | read_only, cap_drop, no-new-privileges — rare in open source |
| Operations | Blue-green deploy/rollback, Prometheus/Grafana provisioning, alert rules, nginx slot routing |
| Knowledge engine | Watchlists, advisories, historical matching adds context beyond ML |
| Threat fusion | Agreement/conflict scoring across multiple intel sources |
| Response time | ~200ms average is acceptable for real-time, with a TTL cache in front of the pipeline |

## 4. Weaknesses

| Weakness | Evidence | Severity |
|----------|----------|----------|
| FPR 14.06% / Recall 77.2% on the 308-sample gold set | `MODEL_STATUS.md` | **Critical** — roughly 1 in 7 safe messages still flagged. Thresholds are frozen pending more gold data |
| Category accuracy 41% | `metrics.json:category_accuracy=0.41` | **High** — wrong scam category identified |
| Assessment accuracy 0.0% | `metrics.json:assessment_accuracy=0.0` | **High** — metric is broken or dataset mismatched |
| No password reset | `routers/accounts.py` | **High** — a forgotten password is permanent |
| No account lockout | `routers/auth.py` | **Medium** — sliding-window throttling only |
| Channels are contracts, not code | `scaffolds/` | **High** — WhatsApp, Telegram and Android forwarder ship as docs against `docs/CHANNEL_CONTRACTS.md` |
| India-only focus | All constants, banks, entities India-specific | **Medium** — not internationalizable without significant work |
| Rate limits are per-instance | `core/storage/repositories.py` | **Medium** — budgets are not global across replicas |
| Training data not reproducible | No training dataset committed, no training pipeline in CI | **High** |
| OCR is Tesseract-only | `ocr.py` depends on system Tesseract install | **Medium** |

## 5. Unique Features vs Competitors

| Feature | ScamShield | Typical SMS Filters |
|---------|-----------|-------------------|
| Campaign detection | ✅ Yes | ❌ No |
| Evidence graph/reasoning | ✅ Yes | ❌ No |
| Relationship graph visualization | ✅ Yes | ❌ No |
| Multi-artefact investigation | ✅ Yes | ❌ No |
| Threat intel fusion | ✅ Yes | ❌ No |
| Indian-specific patterns | ✅ Yes | ❌ Most filters are global |
| ML classification | ✅ Yes | ✅ Yes |
| OCR for image analysis | ✅ Yes | ⚠️ Some |
| Knowledge matching | ✅ Yes | ❌ No |
| Audit trail + API keys | ✅ Yes | ⚠️ Some |
| Gold-set CI regression gate | ✅ Yes | ❌ No |

## 6. Missing Features

| Missing Feature | Importance | Why Missing |
|----------------|-----------|-------------|
| SMS forwarding/auto-analysis | High | No integration with SMS apps; contract documented in `scaffolds/android-sms-forwarder` |
| WhatsApp/Telegram bot | High | Requires provider accounts/credentials; contracts documented in `scaffolds/` |
| Mobile app (Android/iOS) | High | No mobile client |
| Password reset | High | No email delivery channel wired up |
| Browser extension | ~~Medium~~ **Done** | `extension/` — MV3, content scan, background relay, popup verdict |
| User feedback loop | ~~Medium~~ **Done** | `routers/feedback.py`, feedback widget and page |
| Report sharing | Medium | No shareable report links |
| Multi-language NLP | ~~Medium~~ **Partially** | Telugu detection and token mapping added; Tamil range still incomplete |
| Real-time API monitoring | ~~Medium~~ **Done** | Prometheus scrape config, alert rules, Grafana provisioning |
| Rate limiting per user | ~~Medium~~ **Done** | Per-route budgets; global-across-replicas still open |
| Whitelabel/integration SDK | Low | No API SDK for other languages |

## 7. User Experience

### Public Usability
- **Rating:** 4/10 → **6/10**
- **Why:** Registration, login, feedback and a browser extension exist. Still no mobile app or SMS forward, and FPR limits trust.

### Enterprise Usability
- **Rating:** 3/10 → **6/10**
- **Why:** Auth, API keys, audit trail, abuse controls and an ops runbook are in place. No SSO, SLA or support docs.

### Hackathon Readiness
- **Rating:** 8/10
- **Why:** Docker Compose up = working system. Extensive docs. Easy to extend connectors.

### Research Readiness
- **Rating:** 8/10 → **9/10**
- **Why:** Gold-set pipeline, CI gate, frozen thresholds, active-learning queue, leakage reports.

### Commercial Readiness
- **Rating:** 2/10 → **5/10**
- **Why:** Auth, audit, monitoring and deploy/rollback remove the biggest blockers. Still gated by FPR, no password recovery, no SLA, no support or pricing model.

## 8. Product Scorecard

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Problem solved | 7/10 | Real problem (SMS scams in India), well-scoped |
| Solution quality | 6/10 | Gold-set FPR 14.06% / Recall 77.2% — usable but not production-grade; thresholds frozen pending data |
| UX | 6/10 | Login, register, feedback, UPI and dashboard; still no mobile or bot |
| Unique value | 8/10 | Campaign detection + evidence graph + investigation are unique |
| Completeness | 7/10 | Pipeline, auth, ops and feedback complete; three channels are documented contracts only |
| Market fit (India) | 6/10 | Good for India, useless elsewhere |
| Market fit (global) | 2/10 | India-specific |
| Defensibility | 7/10 | Knowledge engine + patterns create moat, but ML model is commodity |
| **Overall Product** | **6.3/10** | |

---

See `REPORT_09_PROJECT_SCORECARD.md` for the full engineering scorecard and
`TECHNICAL_DEBT.md` for what remains open.
