# Release Notes

## v1.0.0 — Initial Release (2026-07-26)

### New Features
- **ML Classification Engine** — LogisticRegression with TF-IDF vectorization for scam probability scoring
- **Heuristic Rule Engine** — 18 India-specific patterns for OTP, UPI, KYC, bank fraud, urgency, and money demands
- **OCR Analysis** — Tesseract-based image-to-text extraction for screenshot analysis
- **Confidence Engine** — Multi-factor scoring combining ML probability, rule matches, entity extraction, and explanation coherence
- **Reasoning Engine** — Structured decision traces with evidence ranking, contradiction detection, and confidence scaling
- **Knowledge Engine** — Pattern matching against known scam typologies with relevance scoring
- **Connector Framework** — Plugin-based architecture with auto-discovery and health checks
- **Google Safe Browsing Connector** — URL lookup with batch processing and exponential backoff
- **Threat Intelligence Fusion** — Multi-source aggregation with conflict resolution and incremental weighting
- **REST API** — Text and image analysis endpoints with structured responses
- **Investigation Engine** — Evidence graph, timeline, campaign analysis, report builder with 4 templates
- **Health & Metrics** — Diagnostics endpoint with ML health, OCR health, connector status, uptime, and latency metrics
- **Demo Mode** — 7 pre-built investigation cases for evaluation
- **Docker Deployment** — Production-ready Docker Compose with Nginx, gzip, caching, security headers

### Infrastructure
- 244 automated tests
- TypeScript strict mode with 0 errors
- Comprehensive error handling with structured error responses
- Request ID tracking for distributed tracing
- CORS configuration with whitelist support
- Rate limiting support via Nginx configuration

### Known Issues
- OCR requires Tesseract 5.x installed on the host system
- ML model trained on English SMS; non-English text may have reduced accuracy
- Image analysis limited to files under 10MB

### Contributors
- ScamShield Project Team
