# Wary — Operations Guide

## 1. Monitoring

### Error Tracking (Sentry)

Wary uses Sentry for server-side error aggregation and alerting. Set the `VITE_SENTRY_DSN` environment variable in the Vercel project dashboard to enable client-side error forwarding. When configured, `src/services/monitoring.ts` sends error-level log entries directly to Sentry's envelope endpoint.

### Client-Side Monitoring

The `src/services/monitoring.ts` module captures runtime events at three levels: `info`, `warn`, and `error`. It maintains an in-memory circular buffer (200 entries) and forwards error-level events to Sentry when a DSN is present.

The `src/utils/diagnostics.ts` module provides structured diagnostic counters for three failure categories:

| Category | Trigger | Method |
|---|---|---|
| API failures | HTTP errors from backend calls | `recordApiFailure(endpoint, status, message)` |
| Render errors | Uncaught exceptions in React components | `recordRenderError(error, component?)` |
| Network errors | Request timeouts, connectivity loss | `recordNetworkError(message)` |

Diagnostics expose `getSummary()` and `getRecentEvents(count)` for on-demand inspection via the browser console or a debug panel.

### Uptime Monitoring

Configure uptime checks for both endpoints using Better Uptime (or equivalent):

| Target | Check interval | Expected status |
|---|---|---|
| `https://scamshield-frontend-psi.vercel.app` | 1 minute | 200 |
| `https://scamshield-backend-rv5v.onrender.com` | 1 minute | 200 |

Each check should verify a response body that confirms the service is healthy (e.g., the frontend returns a 200 HTML page; the backend returns a valid JSON health response at `/health`).

## 2. Alerting

Configure alerts against the uptime monitor and Sentry with the following thresholds:

| Condition | Severity | Notification channel |
|---|---|---|
| Any 5xx response from frontend or backend | Critical | Email + Slack/PagerDuty |
| Response time exceeds 5 seconds for any endpoint | Warning | Slack |
| Service downtime exceeds 5 consecutive minutes | Critical | Email + Slack/PagerDuty |
| Error rate exceeds 5% of requests in a 5-minute window | Warning | Slack |

Alerts should include a direct link to the relevant Sentry issue or uptime dashboard for immediate triage.

## 3. Backup Strategy

- **Frontend (Vercel)**: Every deployment is immutable. Vercel retains all previous deployments and allows instant rollback from the dashboard. No persistent data is stored by the frontend — all state is ephemeral (React in-memory state, TanStack Query cache).
- **Backend (Render)**: Render deploys from the `main` branch of the GitHub repository automatically. The database (if any) is managed separately by the backend service and should follow its own backup schedule.
- **No persistent client data**: The frontend stores no cookies, localStorage, or IndexedDB data containing user information. Theme preference is the only local state persisted (localStorage).

## 4. Incident Response

### Triage Flow

1. Check Sentry dashboard for new error issues and event trends.
2. Check uptime monitor for current status of frontend and backend endpoints.
3. Check Render logs for backend errors or crashes.
4. Check Vercel deployment status for build failures or rollbacks.

### Severity Levels

| Level | Definition | Response time |
|---|---|---|
| P1 — Site Down | Frontend or backend completely unreachable | Immediate, < 15 min |
| P2 — Degraded | Partial outages, high error rate (>5%), slow responses | < 1 hour |
| P3 — Minor | Cosmetic bugs, low-severity errors, non-critical alerts | Next business day |

### Communication

- **Status page**: Update the public status page (Better Uptime status page) with incident description and current impact.
- **User notification**: For P1 and P2 incidents, post an update in the team's communication channel (Slack) with the ETA and ongoing actions.
- **Post-mortem**: Required within 24 hours for all P1 and P2 incidents. Document root cause, timeline, resolution steps, and preventative measures.

## 5. Logging

### Frontend

Logs are written to the browser console via `src/utils/diagnostics.ts` and `src/services/monitoring.ts`. No personally identifiable information (PII) is logged. Log entries follow this structure:

```
timestamp=<ISO-8601> level=<info|warn|error> message=<string> data=<JSON-object>
```

Example:
```
timestamp=2026-07-27T14:30:00.000Z level=error message=api_failure endpoint=/analyze/text status=500
```

### Backend

Backend logs are written to stdout/stderr in structured JSON format. Render captures all stdout and makes it available via the Render dashboard log viewer. Forward logs to a central aggregator (e.g., Logtail, Axiom, or Grafana Loki) for long-term retention and search.

## 6. Runbook

### Site Down (Frontend Unreachable)

1. Check [Vercel Dashboard](https://vercel.com) for deployment status — look for failed builds or misconfigured environment variables.
2. Verify DNS resolves correctly and SSL certificate is valid.
3. If a misconfigured deployment caused the outage, trigger a rollback to the last known-good deployment in Vercel.
4. If Vercel itself is degraded, check [Vercel Status](https://vercel-status.com).

### Site Down (Backend Unreachable)

1. Open the [Render Dashboard](https://dashboard.render.com) and check the backend service status.
2. Review Render logs for crash loops or OOM errors.
3. If the service is stuck, trigger a manual restart from the Render dashboard.
4. If caused by a bad deploy, revert the last commit and redeploy.

### API Errors

1. Check Sentry for the most frequent error issues.
2. Review Render logs around the error timestamps.
3. Check for recent deploys that may have introduced regressions.
4. If the error is related to external dependencies (e.g., database, third-party API), verify those are reachable.
5. Deploy a fix and monitor the error rate in Sentry for the next 30 minutes.

### High Error Rate

1. Open Sentry and sort issues by event count in the last hour.
2. Identify the common root cause (endpoint, error message, stack trace).
3. Create a fix branch, deploy to staging, verify the fix.
4. Merge and deploy to production.
5. Monitor Sentry error rate until it returns to baseline.

### SSL Certificate Expiry

Vercel and Render both provide automatic SSL certificate renewal via Let's Encrypt. No manual intervention is required. Monitor certificate expiry via the uptime monitor (SSL check add-on).

### Incident Post-mortem Template

```
## Incident Post-mortem

**Date**: YYYY-MM-DD
**Severity**: P1 / P2
**Duration**: HH:MM
**Impact**: <affected users / services>

### Timeline
- HH:MM — Alert triggered
- HH:MM — Triage began
- HH:MM — Root cause identified
- HH:MM — Fix deployed
- HH:MM — Service restored

### Root Cause
<description>

### Resolution
<steps taken>

### Preventative Measures
- <action item>
- <action item>
```

## 7. Performance Targets

| Metric | Target | Measurement |
|---|---|---|
| Lighthouse Performance score | ≥ 90 | Lighthouse CI / PageSpeed Insights |
| Lighthouse Accessibility score | ≥ 95 | Lighthouse CI |
| Lighthouse Best Practices score | ≥ 95 | Lighthouse CI |
| Initial JS bundle size | < 500 KB (gzipped) | Vite build report (`npx vite-bundle-analyzer`) |
| Time to Interactive | < 3 s on 3G | Lighthouse / WebPageTest |
| First Contentful Paint | < 1.5 s | Lighthouse |
| Largest Contentful Paint | < 2.5 s | Lighthouse |
| Cumulative Layout Shift | < 0.1 | Lighthouse |

Run Lighthouse CI as part of the CI/CD pipeline. Fail the build if any target score drops below the threshold. Monitor bundle size changes with every PR using a bundle size check action.
