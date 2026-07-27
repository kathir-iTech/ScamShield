# Contributing to ScamShield

Thank you for considering contributing to ScamShield! We welcome contributions of all kinds.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/scamshield.git`
3. Set up the development environment (see [INSTALLATION.md](docs/INSTALLATION.md))
4. Create a branch: `git checkout -b feature/my-feature`

## Development Workflow

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend
cd backend && python -m pytest tests/ -v

# Frontend type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build

# Lint
cd backend && ruff check .
cd frontend && npm run lint
```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Run the linter
5. Submit the PR with a clear description

## Commit Messages

Follow conventional commits: `type(scope): description`

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code restructuring
- `test`: Test additions/changes
- `chore`: Maintenance

## Code Style

- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/), formatted with [Black](https://github.com/psf/black)
- **TypeScript**: Follow project conventions, strict mode enabled
- **CSS**: Tailwind CSS utility classes, no custom CSS unless necessary

## Questions?

Open a [GitHub Discussion](https://github.com/scamshield/scamshield/discussions) or [Issue](https://github.com/scamshield/scamshield/issues).
