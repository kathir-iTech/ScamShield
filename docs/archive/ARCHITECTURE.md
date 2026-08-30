# ScamShield Architecture

## Folder Structure

```
backend/
├── __init__.py              # Package marker
├── train.py                 # CLI training script
├── predict.py               # ML prediction module (reusable)
├── rules.py                 # Rule engine module (reusable)
├── ocr.py                   # OCR module (reusable)
├── config/
│   ├── __init__.py
│   └── settings.py          # Centralized paths and configuration
├── core/
│   ├── __init__.py          # Reserved for future DI, exceptions, app setup
├── services/
│   ├── __init__.py
│   ├── ml_service.py        # Wraps predict.py
│   ├── rules_service.py     # Wraps rules.py
│   ├── ocr_service.py       # Wraps ocr.py
│   └── orchestrator.py      # Single entry point merging ML + rules
├── routers/
│   ├── __init__.py          # Reserved for future FastAPI endpoints
├── schemas/
│   ├── __init__.py          # Reserved for future Pydantic models
├── utils/
│   ├── __init__.py
│   └── text.py              # Shared clean_text() utility
├── middleware/
│   ├── __init__.py          # Reserved for future middleware
├── data/
│   ├── __init__.py
│   └── scam_dataset.csv     # Training dataset
└── models/
    ├── model.joblib          # Trained LogisticRegression
    └── vectorizer.joblib     # Fitted TfidfVectorizer
```

## Responsibilities

| Layer | Folder | Responsibility |
|-------|--------|----------------|
| **Legacy modules** | `backend/` root | `predict.py`, `rules.py`, `ocr.py` — pure functions, no framework dependencies, fully reusable |
| **Configuration** | `config/` | Single source of truth for file paths and environment settings |
| **Services** | `services/` | Business logic wrappers; orchestrate legacy modules |
| **Utilities** | `utils/` | Shared helpers (text cleaning) |
| **Reserved** | `core/`, `routers/`, `schemas/`, `middleware/` | Empty — prepared for FastAPI migration |

## Dependency Graph

```
train.py
  └── config/settings.py
  └── utils/text.py
  └── sklearn, joblib, csv

predict.py
  └── config/settings.py
  └── utils/text.py
  └── joblib

rules.py
  └── re, urllib.parse

ocr.py
  └── utils/text.py
  └── PIL, pytesseract

services/ml_service.py
  └── predict.py

services/rules_service.py
  └── rules.py

services/ocr_service.py
  └── ocr.py

services/orchestrator.py
  └── services/ml_service.py
  └── services/rules_service.py
```

No circular dependencies. Legacy modules (`predict.py`, `rules.py`, `ocr.py`) have zero knowledge of the service layer.

## Execution Flow

```
analyze_text(text)
  │
  ├── ml_service.predict(text)
  │     └── predict.predict(text)
  │           ├── _lazy_load() → model.joblib + vectorizer.joblib
  │           ├── clean_text(text)
  │           ├── vectorizer.transform()
  │           └── model.predict_proba()
  │
  ├── rules_service.analyze_message(text)
  │     └── rules.analyze_message(text)
  │           ├── check_otp()
  │           ├── check_urgent_money()
  │           ├── check_suspicious_links()
  │           └── check_service_keywords()
  │
  └── merge → {
        prediction, confidence,
        rule_score, rule_label,
        reasons, suggested_action
      }
```
