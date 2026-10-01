<div align="center">
  <img src="https://img.shields.io/badge/version-1.1.0-emerald?style=for-the-badge" alt="Version 1.1.0" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="MIT License" />
  <img src="https://img.shields.io/badge/python-3.12+-blue?style=for-the-badge" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/react-19-61DAFB?style=for-the-badge&logo=react" alt="React 19" />
  <br />
  <img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build" />
  <img src="https://img.shields.io/badge/PRs-welcome-orange?style=flat-square" alt="PRs Welcome" />
  <img src="https://img.shields.io/badge/code%20style-black-000000?style=flat-square" alt="Code style: black" />
</div>

> **Current evaluation:** Full-pipeline gold-eval (308 samples) — **FPR 14.06% / Recall 77.2%** — see [MODEL_STATUS.md](MODEL_STATUS.md) for the sourced baseline. Do not re-tune against the 308-sample set without adding more gold data.

> **Deployment note:** The Render backend has not been redeployed since July 27, 2026 and does not reflect current main — the live product runs entirely client-side. The backend code remains validated and available if a server-side feature is needed later.

<h1 align="center">🛡️ Wary</h1>
<p align="center"><strong>AI-Powered Scam SMS Detection Engine</strong></p>

<p align="center">
  Wary combines machine learning classification with heuristic rule analysis to detect phishing, fraud, and scam SMS messages — fully offline capable with optional cloud threat intelligence connectors.
</p>

---

## ✨ Features

- **🤖 ML Classification** — LogisticRegression with TF-IDF vectorization, trained on SMS spam data
- **📋 Rule Engine** — 18 India-specific heuristic patterns (OTP, UPI, KYC, bank fraud, urgency/money demands)
- **🔐 Accounts & Sessions** — Registration, login, password change, logout-everywhere with bcrypt and revocable refresh tokens
- **🛡️ Abuse Controls** — Sliding-window rate limits, API keys and an immutable audit log
- **📸 OCR Analysis** — Image-to-text extraction via Tesseract for screenshot analysis
- **🎯 Confidence Engine** — Multi-factor scoring combining ML, rules, entities, and explanation coherence
- **🔍 Reasoning Engine** — Transparent decision traces with evidence ranking and contradiction detection
- **🔌 Connector Framework** — Pluggable connectors (Google Safe Browsing) with multi-source fusion
- **📊 Investigation Workspace** — Interactive evidence graph, timeline, campaign analysis, and report builder
- **💬 Feedback Loop** — "Was this a scam?" submission from every result, surfaced as a page and widget
- **🧩 Browser Extension** — Manifest V3 extension that scans page content and relays verdicts
- **🌐 REST API** — FastAPI with Swagger/ReDoc docs, gated in production
- **📈 Operations** — Blue-green deploy/rollback, Prometheus/Grafana provisioning, alert rules, TTL cache
- **📦 Fully Offline** — Core engine runs with zero external API dependencies

---

## 🚀 Quick Start

### One-command Docker

```bash
git clone https://github.com/kathir-iTech/ScamShield.git
cd ScamShield
cp .env.example .env
docker compose up -d
```

Open **http://localhost** for the frontend and **http://localhost:8000/docs** for the API.

### Manual Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

> **Note:** Tesseract OCR is required for image analysis. See [installation guide](docs/INSTALLATION.md).

### Authentication

Account features are enabled by setting `SCAMSHIELD_AUTH_ENABLED=true` plus a
non-empty `SCAMSHIELD_JWT_SECRET`. Startup validation refuses to boot in that
state without the secret, so it is best supplied through the environment:

```bash
export SCAMSHIELD_AUTH_ENABLED=true
export SCAMSHIELD_JWT_SECRET="$(python -c 'import secrets;print(secrets.token_hex(32))')"
```

With auth enabled, `POST /api/v1/accounts/register` and
`POST /api/v1/auth/login` issue access and refresh tokens; the frontend login
and register pages use them automatically. API docs are hidden whenever
`ENVIRONMENT` is `production` or `staging`.

### Manual Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🖥️ Live Demo

Explore Wary without installing anything:

- **Live App**: [https://scamshield-frontend-psi.vercel.app](https://scamshield-frontend-psi.vercel.app)
- **API Docs**: [https://scamshield-frontend-psi.vercel.app/docs](https://scamshield-frontend-psi.vercel.app/docs)
- **Demo Cases**: Pre-built investigation cases (Bank Phishing, UPI Fraud, Investment Scam, and more)

---

## 📚 Documentation

| Doc | Description |
|-----|-------------|
| [Installation Guide](docs/INSTALLATION.md) | Detailed setup instructions for all platforms |
| [Architecture](docs/ARCHITECTURE.md) | System design, pipeline flow, component diagram |
| [Engineering Decisions](backend/ENGINEERING_DECISIONS.md) | Why each technical choice was made, and what was rejected |
| [Channel Contracts](docs/CHANNEL_CONTRACTS.md) | Interfaces for web, extension, WhatsApp, Telegram and Android |
| [Production Operations](docs/PRODUCTION_OPERATIONS.md) | Runbook, deploy/rollback, monitoring and incident steps |
| [API Reference](docs/API_REFERENCE.md) | Complete API endpoints with request/response examples |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Contributing, testing, building, and extending |
| [Connector Framework](CONNECTOR_FRAMEWORK.md) | Plugin-based connector architecture |
| [Threat Intelligence Fusion](THREAT_INTELLIGENCE_FUSION.md) | Multi-source fusion engine |
| [Investigation Engine](INVESTIGATION_ENGINE.md) | Interactive investigation workspace |
| [Release Notes](RELEASE_NOTES.md) | Version history and changelog |
| [Roadmap](ROADMAP.md) | Future development plans |

---

## 📊 Benchmark

> **Sourced numbers:** See [MODEL_STATUS.md](MODEL_STATUS.md) — Full-pipeline (gold 308) FPR 14.06% / Recall 77.2% / Precision 88.5% / F1 0.825 / Accuracy 80.8% (TP=139 FP=18 FN=41 TN=110). Raw-model only: Accuracy 97.4% / F1 0.918 / ROC-AUC 0.99. Historic 162-sample table archived in [docs/archive/BENCHMARK_REPORT.md](docs/archive/BENCHMARK_REPORT.md).

---

## 🏗️ Project Structure

```
wary/
├── backend/              # FastAPI Python backend
│   ├── main.py           # Application entry point
│   ├── config/           # Settings & configuration
│   ├── core/             # auth, storage, audit, abuse, connectors, eval
│   ├── services/         # Pipeline services (ML, rules, OCR, orchestrator)
│   ├── connectors/       # Plugin connector framework
│   ├── routers/          # API route handlers
│   ├── schemas/          # Request/response models
│   ├── models/           # Trained ML models
│   └── data/             # Training dataset
├── frontend/             # React + TypeScript frontend
│   └── src/
│       ├── pages/        # Route pages
│       ├── features/     # Feature modules (auth, feedback, graph, timeline)
│       ├── components/   # Shared UI components
│       └── layouts/      # App layout
├── extension/            # Browser extension (Manifest V3)
├── scaffolds/            # WhatsApp / Telegram / Android channel contracts
├── datasets/gold/        # Gold evaluation set and labelling workflow
├── evaluation/           # Frozen thresholds, CI gate, benchmark scripts
├── docs/                 # Documentation
├── scripts/              # Utility scripts (incl. blue-green deploy)
├── nginx/                # Reverse proxy and slot routing
├── infra-future/         # Kubernetes manifests (preview)
└── docker-compose.yml    # Docker deployment
```



---

## 🔬 How It Works

1. **Input** — SMS text or image screenshot
2. **ML Classification** — TF-IDF vectorization → LogisticRegression → scam probability
3. **Rule Analysis** — 18 heuristic patterns → OTP/UPI/KYC/bank fraud detection
4. **OCR** (images) — Tesseract text extraction → pipeline re-entry
5. **Confidence Scoring** — Multi-factor aggregation (ML + rules + entities + explanation)
6. **Reasoning Engine** — Evidence ranking, contradiction detection, decision trace
7. **Connector Enrichment** (optional) — External threat intel lookups
8. **Fusion Engine** — Multi-source aggregation, conflict resolution
9. **Response** — Structured JSON with verdict, evidence, entities, risk assessment

---

## 🧪 Testing

```bash
# Backend suites (~960 tests: unit, security, integration, validation)
cd backend && python -m pytest tests/ -v

# Security suite only
cd backend && python -m pytest tests/security/ -q

# Frontend type check and build
cd frontend && npx tsc --noEmit && npm run build

# Frontend lint and tests
cd frontend && npm run lint && npm run test
```

> **Threshold freeze:** accuracy thresholds in `evaluation/thresholds.json` are
> frozen against the 308-sample gold set. `evaluation/scripts/ci_gate.py` fails
> the build on regression — see [MODEL_STATUS.md](MODEL_STATUS.md).

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- 🐛 **Report bugs** via [GitHub Issues](https://github.com/kathir-iTech/ScamShield/issues)
- 💡 **Suggest features** via [GitHub Discussions](https://github.com/kathir-iTech/ScamShield/discussions)
- 🔀 **Submit PRs** — please read the [Developer Guide](docs/DEVELOPER_GUIDE.md)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Dataset based on SMS spam collections and Indian scam reporting patterns
- Built with [FastAPI](https://fastapi.tiangolo.com/), [scikit-learn](https://scikit-learn.org/), [React](https://react.dev/), and [Tailwind CSS](https://tailwindcss.com/)
- Threat intelligence via [ThreatFox](https://threatfox.abuse.ch/), [URLScan](https://urlscan.io/), [AlienVault OTX](https://otx.alienvault.com/)

---

<p align="center">Made with ❤️ for the security community</p>
