# Developer Guide

## Project Structure

```
scamshield/
├── backend/
│   ├── config/           # Environment config, settings
│   ├── main.py           # FastAPI application entry
│   ├── core/             # Logging, metrics, middleware
│   ├── services/         # Pipeline services
│   ├── connectors/       # Plugin connector framework
│   ├── routers/          # API route handlers
│   ├── schemas/          # Pydantic request/response models
│   ├── models/           # Trained ML models (pickle)
│   ├── data/             # Training dataset
│   └── tests/            # 244 test cases
├── frontend/
│   ├── src/
│   │   ├── app/          # Router, providers
│   │   ├── pages/        # Route pages
│   │   ├── features/     # Feature modules
│   │   ├── components/   # Shared UI components
│   │   ├── layouts/      # App layout
│   │   ├── hooks/        # Custom React hooks
│   │   ├── lib/          # Utilities
│   │   └── types/        # TypeScript types
│   └── index.html
├── docs/                 # Documentation
└── k8s/                  # Kubernetes manifests
```

## Development Commands

### Backend

```bash
# Run development server
uvicorn main:app --reload --port 8000

# Run tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Lint
ruff check .
ruff check . --fix

# Type check (pyright)
pyright
```

### Frontend

```bash
# Run dev server
npm run dev

# Type check
npx tsc --noEmit

# Build
npm run build

# Lint
npm run lint

# Preview production build
npx vite preview
```

## Adding a New Connector

1. Create `backend/connectors/my_connector.py`
2. Implement `ConnectorPlugin` interface with `analyze()`, `health_check()`, `name` property
3. The framework auto-discovers via `__init__.py`

## Adding a New Rule

1. Add pattern to `backend/services/rules.py` in the appropriate category
2. Add a test case in `backend/tests/`

## Frontend Feature Module Pattern

Each feature follows:
```
src/features/<name>/
├── index.ts           # Barrel exports
├── types.ts           # Feature-specific types
├── <Feature>.tsx      # Main component
└── <sub-components>.tsx  # Supporting components
```

## Testing Guidelines

- Write backend tests for all services, routers, and schemas
- Use pytest fixtures for shared setup
- Mock external dependencies (connectors, OCR)
- Frontend tests should use Vitest + React Testing Library
