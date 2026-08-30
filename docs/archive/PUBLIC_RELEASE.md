# ScamShield v1.0.0 — Public Release

## Overview

ScamShield is an AI-powered scam SMS detection engine designed for India-specific fraud patterns. Version 1.0 delivers a production-ready pipeline combining machine learning classification with heuristic rule analysis, backed by an interactive investigation workspace.

## Key Capabilities

- **Scam Detection** — ML-based (LogisticRegression + TF-IDF) with 83.3% accuracy, 90.1% F1 score
- **India-Specific Rules** — 18 heuristic patterns covering OTP fraud, UPI scams, KYC phishing, bank fraud, urgency/money demands
- **Image Analysis** — OCR extraction from screenshots via Tesseract
- **Reasoning Engine** — Transparent decision traces with evidence ranking
- **Investigation Workspace** — Evidence graph, timeline, campaign analysis, report builder
- **Connector Framework** — Plugin-based external threat intel integration
- **All Offline Capable** — Core engine runs with zero external dependencies

## What's Included

| Component | Technology |
|-----------|------------|
| Backend API | FastAPI (Python 3.12+) |
| Frontend | React 19, TypeScript, Tailwind CSS |
| ML Pipeline | scikit-learn (LogisticRegression) |
| Deployment | Docker Compose, Nginx, Gunicorn |
| Testing | 244 tests, all passing |

## Getting Started

```bash
git clone https://github.com/scamshield/scamshield.git
cd scamshield
cp .env.example .env
docker compose up -d
```

Visit http://localhost for the frontend and http://localhost:8000/docs for the API.

## Documentation

- [README](README.md)
- [Installation Guide](docs/INSTALLATION.md)
- [API Reference](docs/API_REFERENCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md)

## Support

- Report issues: https://github.com/scamshield/scamshield/issues
- Discussions: https://github.com/scamshield/scamshield/discussions

## License

MIT — see [LICENSE](LICENSE).
