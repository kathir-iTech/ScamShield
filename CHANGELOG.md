# Changelog

## 1.1.0 (2026-10-02)

### Added
- User accounts with registration, login, session inspection, password change and logout-everywhere
- bcrypt password hashing and HS256 access tokens with persisted, revocable refresh tokens
- API keys with hashed storage and FastAPI dependencies for service access
- SQLite storage layer (WAL, thread-local connections, repository pattern) for users, sessions, audit and rate limits
- Immutable audit log covering authentication and authorization events
- Sliding-window rate limiting with per-route budgets and `X-RateLimit-*` headers
- Feedback endpoints, feedback widget and feedback page
- Login, register and UPI routes with an auth context and sidebar navigation
- Browser extension (Manifest V3): content scan, background relay, popup verdict
- Channel contract documentation with WhatsApp, Telegram and Android SMS scaffolds
- TTL cache with Redis and in-memory backends, consulted before running the pipeline
- Prometheus scrape config, alert rules, Grafana provisioning and monitoring compose overlay
- Blue-green deploy and rollback script, nginx slot routing, deploy workflow
- Production operations runbook
- Gold-set evaluation pipeline, CI regression gate, frozen thresholds and active-learning label queue
- Scheduled model evaluation, retraining workflow and multilingual (Telugu) detection
- 176 security tests, caching and load validation, frontend end-to-end tests
- Engineering decisions record and channel contracts documentation

### Changed
- CSP now includes `frame-ancestors`, `object-src`, `base-uri` and `form-action`; HSTS adds `preload`
- CORS no longer allows the `X-Admin-Key` request header
- API docs (`/docs`, `/redoc`, `/openapi.json`) are gated when the environment is `production` or `staging`
- Unicode normalization restricted to a safe-character whitelist before entity extraction
- Git ignores model artifacts, logs, local databases and test output; production env file is never committed

### Fixed
- SQLite write-lock deadlock under concurrent append/load; busy timeout tightened
- Global rate limiter overwriting per-route `X-RateLimit` headers

## 1.0.0 (2026-07-26)

### Added
- ML-based scam classification with confidence scoring (83.3% accuracy, 90.1% F1)
- Heuristic rule engine with 18 India-specific indicator patterns
- OCR-based text extraction from images via Tesseract
- REST API with FastAPI (text + image analysis endpoints)
- Multi-factor confidence engine combining ML, rules, entities, and explanation
- Reasoning engine with evidence ranking and contradiction detection
- Investigation engine with structured reports
- Knowledge engine with pattern matching against known scam patterns
- Plugin-based connector framework with auto-discovery
- Google Safe Browsing connector (v4 API, batch lookup, exponential backoff)
- Multi-source threat intelligence fusion engine
- Interactive evidence graph with SVG rendering, pan/zoom, filtering, export
- Investigation timeline with time clustering, zoom, filters, event details
- Campaign visualization with shared entities and repeated indicators
- Report builder with 4 templates (Technical, Executive, Law Enforcement, Customer)
- Copy, JSON, Markdown, and Print/PDF export for reports
- Demo mode with 7 pre-built investigation cases
- Guided walkthrough / tutorial mode
- Health diagnostics and metrics monitoring
- Production Docker deployment with Nginx reverse proxy
- Comprehensive security headers and CSP configuration
- Dark mode with persistent theme selection
- Full accessibility with ARIA labels and keyboard navigation
- Skeleton loaders and page transitions

### Infrastructure
- Docker Compose for one-command deployment
- Nginx with gzip, caching, security headers, rate limiting
- Environment-based configuration (.env)
- CORS validation and request ID tracking
- Structured JSON logging with correlation IDs
- 244 automated tests across all components
