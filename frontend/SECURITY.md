# ScamShield Frontend — Security Documentation

## 1. Security Headers

All responses from the production nginx reverse proxy include the following security headers:

| Header | Value | Purpose |
|---|---|---|
| `X-Frame-Options` | `SAMEORIGIN` | Prevents clickjacking by disallowing framing from external origins. |
| `X-Content-Type-Options` | `nosniff` | Instructs browsers to trust declared MIME types, preventing MIME-sniffing attacks. |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | Enforces HTTPS for all subdomains over a two-year period; qualifies for HSTS preload lists. |
| `Content-Security-Policy` | *(see section 2)* | Restricts resource origins to mitigate XSS and data-injection attacks. |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), interest-cohort=()` | Disables unused browser features; denies FLoC cohort tracking. |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Sends full URL as referrer on same-origin requests; strips path data on cross-origin. |

## 2. Content Security Policy

The CSP deployed via nginx (`frontend/nginx.conf:20`) is:

```
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' data: blob:;
font-src 'self' https://fonts.gstatic.com;
connect-src 'self' https://scamshield-backend-rv5v.onrender.com https://fonts.googleapis.com;
frame-ancestors 'none';
```

**Directive rationale:**

- **default-src 'self'** — Base restriction: all resources must originate from the same origin unless overridden.
- **script-src 'self'** — Only first-party scripts execute; inline scripts are blocked, preventing DOM-based XSS.
- **style-src 'self' 'unsafe-inline'** — Inline styles are required by Tailwind's JIT engine. This is an accepted trade-off; no third-party stylesheets are loaded.
- **img-src 'self' data: blob:** — Permits image upload preview via `URL.createObjectURL()` (blob:) and inline Base64 icons (data:).
- **font-src 'self' https://fonts.gstatic.com** — Google Fonts are loaded from the dedicated CDN.
- **connect-src 'self' https://scamshield-backend-rv5v.onrender.com https://fonts.googleapis.com** — API calls and Google Fonts stylesheet fetches are explicitly allowed. All other endpoints are denied.
- **frame-ancestors 'none'** — Disallows embedding the application in any `<frame>`, `<iframe>`, or `<object>`, providing defense-in-depth against clickjacking alongside `X-Frame-Options`.

## 3. Data Privacy

ScamShield is designed with privacy as a core requirement:

- **No storage of user content.** Messages and images submitted for analysis are processed in real-time by the backend and are never persisted to disk or database.
- **No account system.** The application has no authentication, no user profiles, and no session management. There is no personal identifiable information (PII) to collect or protect.
- **No cookies.** The frontend does not set or read any cookies. No tracking, no analytics cookies, no session tokens.
- **No third-party data sharing.** The application communicates exclusively with the ScamShield backend API and Google Fonts. No data is sent to advertising, analytics, or tracking networks.
- **No local storage of submissions.** Analysis results are held in React state and TanStack Query's in-memory cache only; they are lost on page refresh.

## 4. API Security

- **CORS.** The backend must restrict `Access-Control-Allow-Origin` to the frontend origin (e.g., `https://scamshield.app`). The frontend does not rely on credentials (`credentials: "omit"`).
- **Rate limiting.** Nginx enforces `limit_req zone=api burst=20 nodelay` on all `/api/` requests, returning HTTP 429 when the burst capacity is exhausted.
- **Dev endpoints blocked.** The nginx production config (`frontend/nginx.conf:86-101`) returns 404 for `/docs`, `/redoc`, `/openapi.json`, and `/metrics`, preventing exposure of API documentation and telemetry.
- **Upload validation.** The client validates image type (JPEG/PNG/WebP) and size (max 10 MB) via a Zod schema before upload.
- **Request timeouts.** Nginx sets `proxy_read_timeout 60s` on the API location for image uploads; general Axios requests use a 15-second timeout.
- **Body size limit.** Nginx limits request bodies to 12 MB (`client_max_body_size 12m`).

## 5. Dependencies

The dependency tree is intentionally minimal to reduce the attack surface:

- **Runtime:** React 19, React Router, TanStack Query, Axios, Tailwind CSS, Zod, Framer Motion, Lucide React, and utility libraries (CVA, clsx, tailwind-merge).
- **Dev:** TypeScript, Vite, Vitest, Testing Library, Oxlint.

`npm audit` **must be run before every production deploy.** Any reported vulnerabilities should be triaged and patched before deployment. Automated CI checks should enforce a zero-known-vulnerability policy on the production build.

## 6. Vulnerability Reporting

If you discover a security vulnerability in ScamShield, please do not open a public GitHub issue. Instead, report it privately to:

**security@scamshield.dev**

We will acknowledge receipt within 48 hours and work toward a resolution. Responsible disclosures are appreciated and will be acknowledged.

## 7. Pre-deployment Security Checklist

- [ ] `Content-Security-Policy` is correct and blocks all unintended origins.
- [ ] All environment variables (`VITE_API_BASE_URL`) are set for the target environment.
- [ ] Dev/debug endpoints (`/docs`, `/redoc`, `/openapi.json`, `/metrics`) return 404.
- [ ] HTTPS is enforced (HSTS preload, TLS termination at load balancer).
- [ ] No secrets, API keys, or tokens are present in client-side code or committed files.
- [ ] `npm audit` reports zero critical or high vulnerabilities.
- [ ] Production build is tree-shaken and minified (`vite build`).
- [ ] Nginx `limit_req` and `client_max_body_size` are configured appropriately.
- [ ] CORS policy on the backend allows only the known frontend origin.
