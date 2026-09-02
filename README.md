<div align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-emerald?style=for-the-badge" alt="Version 1.0.0" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="MIT License" />
  <img src="https://img.shields.io/badge/python-3.12+-blue?style=for-the-badge" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/react-19-61DAFB?style=for-the-badge&logo=react" alt="React 19" />
  <br />
  <img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build" />
  <img src="https://img.shields.io/badge/PRs-welcome-orange?style=flat-square" alt="PRs Welcome" />
  <img src="https://img.shields.io/badge/code%20style-black-000000?style=flat-square" alt="Code style: black" />
</div>

> **Current evaluation:** Full-pipeline gold-eval (308 samples) — **FPR 14.06% / Recall 77.2%** — see [MODEL_STATUS.md](MODEL_STATUS.md) for the sourced baseline. Do not re-tune against the 308-sample set without adding more gold data.

<h1 align="center">🛡️ Wary</h1>
<p align="center"><strong>AI-Powered Scam SMS Detection Engine</strong></p>

<p align="center">
  Wary combines machine learning classification with heuristic rule analysis to detect phishing, fraud, and scam SMS messages — fully offline capable with optional cloud threat intelligence connectors.
</p>

---

## ✨ Features

- **🤖 ML Classification** — LogisticRegression with TF-IDF vectorization, trained on SMS spam data
- **📋 Rule Engine** — 18 India-specific heuristic patterns (OTP, UPI, KYC, bank fraud, urgency/money demands)
- **📸 OCR Analysis** — Image-to-text extraction via Tesseract for screenshot analysis
- **🎯 Confidence Engine** — Multi-factor scoring combining ML, rules, entities, and explanation coherence
- **🔍 Reasoning Engine** — Transparent decision traces with evidence ranking and contradiction detection
- **🔌 Connector Framework** — Pluggable connectors (Google Safe Browsing) with multi-source fusion
- **📊 Investigation Workspace** — Interactive evidence graph, timeline, campaign analysis, and report builder
- **🌐 REST API** — FastAPI with auto-generated Swagger/ReDoc docs
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
│   ├── core/             # Core utilities (logging, metrics, middleware)
│   ├── services/         # Pipeline services (ML, rules, OCR, orchestrator)
│   ├── connectors/       # Plugin connector framework
│   ├── routers/          # API route handlers
│   ├── schemas/          # Request/response models
│   ├── models/           # Trained ML models
│   └── data/             # Training dataset
├── frontend/             # React + TypeScript frontend
│   └── src/
│       ├── pages/        # Route pages
│       ├── features/     # Feature modules (graph, timeline, report, demo)
│       ├── components/   # Shared UI components
│       └── layouts/      # App layout
├── docs/                 # Documentation
├── evaluation/           # Benchmark evaluation scripts
├── scripts/              # Utility scripts
├── docker-compose.yml    # Docker deployment
└── k8s/                  # Kubernetes manifests
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
# Backend tests (244 tests)
cd backend && python -m pytest tests/ -v

# Frontend type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build
```

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
