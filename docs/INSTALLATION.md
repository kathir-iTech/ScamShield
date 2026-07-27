# Installation Guide

## Prerequisites

- Python 3.12+
- Node.js 20+
- Tesseract OCR 5.x (for image analysis)
- Docker (optional, for containerized deployment)

## Docker Deployment (Recommended)

```bash
git clone https://github.com/scamshield/scamshield.git
cd scamshield
cp .env.example .env
docker compose up -d
```

ScamShield will be available at:
- Frontend: http://localhost
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Manual Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### Configure Environment

```bash
cp ../.env.example ../.env
# Edit .env as needed
```

### Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download installer from https://github.com/UB-Mannheim/tesseract/wiki
Add Tesseract to PATH.

### Run Backend

```bash
uvicorn main:app --reload --port 8000
```

## Manual Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Verify Installation

```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Frontend type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| OCR not working | Verify Tesseract is installed: `tesseract --version` |
| Port conflict | Change port in `.env` or use `--port` flag |
| Module not found | Ensure virtual environment is activated and `pip install -r requirements.txt` ran |
| CORS errors | Check `CORS_ORIGINS` in `.env` matches your frontend URL |
