# Changelog

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
