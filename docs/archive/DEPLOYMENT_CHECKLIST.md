# Deployment Checklist — ScamShield v1.0.0

## Pre-Deployment

- [ ] All 244 backend tests pass (`cd backend && python -m pytest tests/ -x`)
- [ ] TypeScript strict mode: 0 errors (`cd frontend && npx tsc --noEmit`)
- [ ] Production build succeeds (`cd frontend && npm run build`)
- [ ] Validation evaluation passes (>70% accuracy on 511-sample set)
- [ ] `.env` configured with production values
- [ ] `CORS_ORIGINS` set to production domain
- [ ] Google Safe Browsing API key (optional) configured
- [ ] Rate limiting settings tuned for expected traffic

## Docker Deployment

- [ ] Docker and Docker Compose installed
- [ ] Ports 80/443 available
- [ ] SSL certificates mounted (if HTTPS enabled)
- [ ] Nginx config reviewed for security headers
- [ ] `docker compose up -d` succeeds
- [ ] Health endpoint returns `{"status": "healthy"}`

## Post-Deployment Verification

- [ ] Frontend loads at `https://your-domain.com`
- [ ] API docs accessible at `https://your-domain.com/docs`
- [ ] Text analysis endpoint returns correctly (`POST /api/v1/analyze/text`)
- [ ] Image analysis endpoint works (if OCR available)
- [ ] System status page shows all components healthy
- [ ] Dark mode toggle works
- [ ] Navigation sidebar links resolve correctly
- [ ] 404 page renders for unknown routes
- [ ] CORS errors do not appear in browser console
- [ ] Security headers present (CSP, HSTS, X-Frame-Options)
- [ ] Rate limiting functions (test with rapid requests)
- [ ] Gzip compression working (verify via browser DevTools)

## Monitoring

- [ ] Health endpoint (30s interval) configured in monitoring
- [ ] Log aggregation set up (JSON structured logs)
- [ ] Uptime monitoring configured
- [ ] Error alerting threshold: <1% 5xx responses
- [ ] P95 latency alert: >500ms triggers notification

## Post-Deployment Tasks

- [ ] Run evaluation on production API (`--api https://your-domain.com`)
- [ ] Compare metrics against baseline for regression check
- [ ] Test demo cases load correctly in investigation workspace
- [ ] Verify report generation (JSON, Markdown, Print)
- [ ] Confirm demo mode walkthrough loads all 6 steps
