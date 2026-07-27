# ScamShield Architecture

## System Overview

ScamShield follows a pipeline architecture where each stage processes and enriches the analysis result before passing it to the next stage. The frontend communicates with the backend via a REST API.

```
┌──────────────────────────────────────────────────────────┐
│                        Frontend                          │
│  React 19 + TypeScript + Tailwind CSS + Framer Motion    │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐│
│  │ Landing │ │Analysis  │ │Investiga-│ │ System       ││
│  │ Page    │ │Pages     │ │tion      │ │ Status       ││
│  └─────────┘ └──────────┘ │Workspace │ └──────────────┘│
│                           │[Graph]    │                  │
│                           │[Timeline] │                  │
│                           │[Campaigns]│                  │
│                           │[Report]   │                  │
│                           └──────────┘                  │
└───────────────────────┬──────────────────────────────────┘
                        │ HTTP/REST
                        ▼
┌──────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                     │
│                                                          │
│  ┌────────────┐    ┌──────────────┐   ┌───────────────┐ │
│  │ Routers    │───▶│ Orchestrator │──▶│ Response      │ │
│  │ /analyze   │    │ Service      │   │ Builder       │ │
│  │ /investigate│   └──────┬───────┘   └───────────────┘ │
│  │ /health    │           │                              │
│  └────────────┘           ▼                              │
│                    ┌──────────────┐                       │
│                    │  Pipeline    │                       │
│                    │  ┌─────────┐ │                       │
│                    │  │ ML      │ │                       │
│                    │  │ Classif.│ │                       │
│                    │  ├─────────┤ │                       │
│                    │  │ Rule    │ │                       │
│                    │  │ Engine  │ │                       │
│                    │  ├─────────┤ │                       │
│                    │  │ OCR     │ │                       │
│                    │  │ Service │ │                       │
│                    │  ├─────────┤ │                       │
│                    │  │Confid.  │ │                       │
│                    │  │ Engine  │ │                       │
│                    │  ├─────────┤ │                       │
│                    │  │Reasoning│ │                       │
│                    │  │ Engine  │ │                       │
│                    │  ├─────────┤ │                       │
│                    │  │Connector│ │                       │
│                    │  │Framework│ │                       │
│                    │  ├─────────┤ │                       │
│                    │  │ Fusion  │ │                       │
│                    │  │ Engine  │ │                       │
│                    │  └─────────┘ │                       │
│                    └──────────────┘                       │
└──────────────────────────────────────────────────────────┘
```

## Backend Component Breakdown

### Pipeline Stages (executed in order)

1. **ML Classification** — `services/classifier.py`
   - TF-IDF vectorization → LogisticRegression → scam probability
   - Trained on UCI SMS Spam + India-specific augmentations

2. **Rule Engine** — `services/rules.py`
   - 18 heuristic patterns (regex-based) organized into 4 categories
   - Returns matched rules with confidence contributions

3. **OCR Service** — `services/ocr.py`
   - Tesseract 5.x integration for image analysis
   - Fallback handling for low-quality images

4. **Confidence Engine** — `services/confidence.py`
   - Multi-factor weighted scoring
   - Adjusts for conflicting signals

5. **Reasoning Engine** — `services/reasoning.py`
   - Evidence ranking by relevance and confidence
   - Contradiction detection between signals
   - Structured decision trace for transparency

6. **Knowledge Engine** — `services/knowledge.py`
   - Pattern matching against known scam typologies
   - Relevance scoring

7. **Connector Framework** — `connectors/`
   - Plugin-based with auto-discovery via `__init__.py`
   - Built-in: Google Safe Browsing connector
   - Community extension point

8. **Fusion Engine** — `services/fusion.py`
   - Multi-source aggregation
   - Conflict resolution with incremental weighting

### Supporting Services

- **Orchestrator** — Coordinates pipeline execution, caches results, handles errors
- **Investigation Engine** — Generates structured reports, evidence traces, graph data
- **Health Service** — Diagnostics, metrics collection, uptime tracking

## Frontend Component Breakdown

### Pages
- **Landing** — Public-facing homepage with hero, features, metrics, architecture, FAQ
- **Text Analysis** — SMS text input and analysis
- **Image Analysis** — Screenshot upload and OCR analysis
- **Analysis Result** — Detailed results with evidence breakdown
- **Investigation** — Multi-tab workspace (Graph, Timeline, Campaigns, Report)
- **Dashboard** — Metrics overview (accessible at `/dashboard`)
- **System Status** — Health metrics and diagnostics
- **Not Found** — 404 page

### Feature Modules
- **Graph** — SVG-rendered evidence graph with force-directed layout, pan/zoom, filtering, export
- **Timeline** — Vertical event timeline with time clustering, filtering, search
- **Campaigns** — Campaign card view with shared entities, repeated indicators
- **Report** — 4 templates with 10 section types, multiple export formats
- **Demo** — 7 pre-built cases, guided walkthrough, one-click loading

## Data Flow

```
User Input
    │
    ▼
Input Validation (Pydantic schemas)
    │
    ▼
Pipeline Execution (orchestrator)
    │
    ├── ▶ ML Classification ────┐
    ├── ▶ Rule Engine ──────────┤
    ├── ▶ OCR (if image) ──────┤
    ├── ▶ Confidence Engine ───┤
    ├── ▶ Reasoning Engine ────┤
    ├── ▶ Knowledge Engine ────┤
    ├── ▶ Connectors (optional) ─┤
    └── ▶ Fusion Engine ────────┘
    │
    ▼
Response Building
    │
    ▼
JSON Response → Frontend Rendering
```

## Deployment Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Browser    │────▶│   Nginx      │────▶│  FastAPI     │
│   (React)    │     │   (reverse   │     │  (Uvicorn)   │
│              │◀────│    proxy)    │◀────│              │
└──────────────┘     └──────────────┘     └──────────────┘
                           │                      │
                           │                 ┌────┴────┐
                           │                 │Tesseract│
                           │                 │  OCR    │
                           │                 └─────────┘
                           │
                    ┌──────┴──────┐
                    │  Static     │
                    │  Assets     │
                    │  (build/)   │
                    └─────────────┘
```
