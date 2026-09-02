# Kaaval Frontend — Deployment Guide

## Architecture Overview

```
User ──────► Vercel (CDN) ──────► scamshield-frontend-psi.vercel.app
                │
                │  API calls (VITE_API_BASE_URL)
                ▼
        Render (FastAPI) ──────► scamshield-backend-rv5v.onrender.com
```

Kaaval is a single-page application (SPA) built with Vite + React 19 + TypeScript + Tailwind CSS v4. The frontend is decoupled from the backend API — all communication happens at runtime via the `VITE_API_BASE_URL` environment variable. In production, the backend runs as a FastAPI service on Render, while the frontend static assets are served by Vercel's global edge network. DNS for the custom domain `scamshield-frontend-psi.vercel.app` is managed through Vercel.

A Dockerized deployment option using `nginx:1.27-alpine` is also available for self-hosted environments.

---

## Prerequisites

- **Node.js** 22+ (required for local development and builds)
- **npm** 10+ (shipped with Node.js 22)
- **Docker** 24.0+ (optional — only needed for containerized deployment)
- A **Vercel** account (for Vercel deployment)
- A **GitHub** account (for CI/CD and Vercel Git integration)

---

## Environment Variables

| Variable              | Required | Default | Description                          |
|-----------------------|----------|---------|--------------------------------------|
| `VITE_API_BASE_URL`   | Yes      | `/api`  | Backend API base URL (runtime fetch) |

`VITE_API_BASE_URL` is embedded at build time via Vite's import-meta environment variable handling. In development, it defaults to `/api` and is proxied to `localhost:8000` by Vite's dev server. In production, set it to the Render backend URL: `https://scamshield-backend-rv5v.onrender.com`.

---

## Local Development

```bash
cd frontend
npm install
npm run dev
```

This starts the Vite dev server on `http://localhost:5173`. The `vite.config.ts` proxies `/api` requests to `http://localhost:8000`, so the backend must be running locally for API-dependent features.

```ts
// vite.config.ts (proxy excerpt)
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (p) => p.replace(/^\/api/, ''),
    },
  },
},
```

---

## Build

```bash
npm run build
```

The build pipeline runs `tsc -b` for TypeScript type checking, then `vite build` to produce production-optimized assets in the `dist/` directory. Output includes fingerprinted JS/CSS bundles, precompressed assets (when configured), and the `index.html` entry point.

To preview the production build locally:

```bash
npm run preview
```

---

## Deploy to Vercel

Kaaval deploys to **Vercel** at `scamshield-frontend-psi.vercel.app`.

### Manual setup (first time)

1. Push the repository to GitHub.
2. In the Vercel dashboard, click **Add New → Project** and import the GitHub repo.
3. Configure the project:

   | Setting            | Value                              |
   |--------------------|------------------------------------|
   | Framework Preset   | Vite                               |
   | Root Directory     | `frontend`                         |
   | Build Command      | `npm run build`                    |
   | Output Directory   | `dist`                             |
   | Node.js Version    | 22.x                               |

4. Add the environment variable:

   | Name                | Value                                              |
   |---------------------|----------------------------------------------------|
   | `VITE_API_BASE_URL` | `https://scamshield-backend-rv5v.onrender.com`     |

5. Click **Deploy**. Vercel detects the Vite framework automatically, runs the build, and deploys the `dist/` folder to its global edge network.

### Automatic deploys

Once connected, every push to the `main` branch triggers an automatic production deployment. Deploy previews are generated for pull requests, allowing you to test changes before merging.

### Custom domain

In the Vercel dashboard under **Project → Domains**, add `scamshield-frontend-psi.vercel.app` and update the DNS nameservers or add the required `CNAME` and `TXT` records as instructed by Vercel. Vercel provisions a TLS certificate automatically via Let's Encrypt.

---

## Docker Deployment

A multi-stage `Dockerfile` is provided for containerized deployment:

```bash
# Build the image
docker build \
  --build-arg VITE_API_BASE_URL=https://scamshield-backend-rv5v.onrender.com \
  -t kaaval-frontend \
  ./frontend

# Run the container
docker run -d \
  --name kaaval-frontend \
  -p 80:80 \
  kaaval-frontend
```

The multi-stage build works as follows:

| Stage     | Base Image         | Purpose                                      |
|-----------|-------------------|----------------------------------------------|
| `builder` | `node:22-alpine`  | Installs dependencies, runs `npm run build`  |
| Runtime   | `nginx:1.27-alpine` | Copies `dist/` and `nginx.conf`, serves content |

The container runs as an unprivileged user (`appuser`, UID 1000) with a built-in `HEALTHCHECK` that pings `http://localhost:80/` every 30 seconds.

For docker-compose (full stack with backend), see the root `docker-compose.yml`.

---

## Nginx Configuration

The `nginx.conf` is designed for production SPA hosting with security and performance hardening:

| Feature               | Detail                                                  |
|-----------------------|---------------------------------------------------------|
| **SPA fallback**      | `try_files $uri $uri/ /index.html` — all routes serve `index.html`, enabling client-side routing |
| **CSP**               | Restricts `script-src` to `'self'`, allows `connect-src` to the Render backend and Google Fonts |
| **HSTS**              | `Strict-Transport-Security` with a 2-year max-age, `includeSubDomains`, `preload` |
| **Gzip**              | Compresses JS, CSS, JSON, SVG, and XML — minimum 256 bytes, level 5 |
| **Asset caching**     | `location /assets/` and image/font patterns set `Cache-Control: public, immutable` with a 1-year expiry |
| **API proxy**         | `/api/` routes are proxied to the upstream backend with 60s read timeouts and a 12 MB body limit |
| **Security headers**  | `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy` |
| **Rate limiting**     | API endpoints are rate-limited with a burst of 20 requests |
| **Debug blocking**    | `/docs`, `/redoc`, `/openapi.json`, `/metrics` return 404 in production |

---

## CI/CD

A GitHub Actions workflow (`.github/workflows/frontend.yml`) runs on every push to `main` and on pull requests that touch the `frontend/` directory:

```yaml
# .github/workflows/frontend.yml (abridged)
jobs:
  typecheck:   # npx tsc -b --noEmit
  lint:        # npm run lint (oxlint)
  test:        # vitest run + coverage upload
  build:       # npm run build + bundle size check (< 512 KB)
  security:    # npm audit --audit-level=high
  docker-build:# docker build --build-arg VITE_API_BASE_URL=/api
```

The `docker-build` job validates that the Docker image builds successfully without publishing. A separate `docker.yml` workflow runs Trivy vulnerability scans on the built images.

### Vercel Git Integration

Once the Vercel project is linked to the GitHub repo, Vercel handles deployments automatically — no additional CI configuration is needed. Each push to `main` triggers a production deployment, and each PR generates a preview deployment.

---

## Rollback

### Vercel (managed)

1. Go to the Vercel dashboard → **Deployments**.
2. Find the stable deployment and click the three-dot menu → **Promote to Production**.
3. Vercel instantly serves the previous build from its edge cache.

### Docker (self-hosted)

```bash
# List available images
docker images kaaval-frontend

# Roll back to a specific tag
docker stop kaaval-frontend
docker run -d --name kaaval-frontend -p 80:80 kaaval-frontend:<previous-tag>
```

If using a registry, tag images with Git SHA or semantic version to simplify rollbacks:

```bash
docker build -t kaaval-frontend:$(git rev-parse --short HEAD) ./frontend
docker tag kaaval-frontend:$(git rev-parse --short HEAD) kaaval-frontend:latest
```

---

## Troubleshooting

| Symptom                          | Likely cause                                | Fix                                                       |
|----------------------------------|---------------------------------------------|-----------------------------------------------------------|
| Blank page in production         | Missing or incorrect `VITE_API_BASE_URL`    | Rebuild with the correct env var — check Vercel dashboard |
| API calls return 502             | Backend unreachable or CORS misconfiguration| Verify Render backend is running; check CORS origins      |
| Routes fail on page refresh      | SPA fallback not configured                 | Ensure `try_files $uri $uri/ /index.html` is active in nginx or Vercel rewrites |
| CSS missing or broken            | Tailwind v4 not built properly              | Run `npm run build` locally and verify `dist/` output      |
| Docker build fails               | Missing `VITE_API_BASE_URL` build arg       | Pass `--build-arg VITE_API_BASE_URL=<url>` to `docker build` |
| TypeScript build errors in CI    | Locally installed `node_modules` mismatch   | Run `npm ci --ignore-scripts` instead of `npm install`     |
| Bundle exceeds size limit        | Large dependency or missing tree-shaking    | Run `npm run build` and inspect `dist/assets/*.js` sizes   |

For Vercel-specific issues, check the **Function Logs** and **Build Logs** in the Vercel dashboard under **Project → Deployments → [deployment] → Logs**.
