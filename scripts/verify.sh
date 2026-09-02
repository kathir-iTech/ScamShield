#!/usr/bin/env bash
set -euo pipefail

echo "╔═══════════════════════════════════════════════╗"
echo "║       Wary — Pre-Commit Verification        ║"
echo "╚═══════════════════════════════════════════════╝"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FAILURES=0

# ── Backend ───────────────────────────────────────────
echo ""
echo "━━━ Backend Checks ━━━"
cd "$ROOT_DIR/backend"

echo "[1/6] Python imports..."
python -c "
import importlib
modules = ['core.constants','core.exceptions','core.logger','core.metrics','core.middleware',
           'config.settings','services.orchestrator','services.ml_service','services.rules_service',
           'services.explanation_service','services.intelligence_service','services.evidence_service',
           'services.assessment_service','services.report_service','services.ocr_service',
           'routers.health','routers.analyze','schemas.requests','schemas.responses',
           'utils.validate','predict']
ok = 0
for m in modules:
    try:
        importlib.import_module(m); ok += 1
    except Exception as e:
        print(f'  FAIL: {m} — {e}')
print(f'  {ok}/{len(modules)} passed')
" || { echo "FAIL: imports"; ((FAILURES++)); }

echo "[2/6] Backend tests..."
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -5 || { echo "FAIL: backend tests"; ((FAILURES++)); }

# ── Frontend ──────────────────────────────────────────
echo ""
echo "━━━ Frontend Checks ━━━"
cd "$ROOT_DIR/frontend"

echo "[3/6] TypeScript check..."
npx tsc -b --noEmit 2>&1 || { echo "FAIL: TypeScript"; ((FAILURES++)); }

echo "[4/6] Lint..."
npm run lint 2>&1 || { echo "FAIL: lint"; ((FAILURES++)); }

echo "[5/6] Frontend tests..."
npm test 2>&1 | tail -10 || { echo "FAIL: frontend tests"; ((FAILURES++)); }

echo "[6/6] Production build..."
npm run build 2>&1 | tail -5 || { echo "FAIL: build"; ((FAILURES++)); }

# ── Summary ───────────────────────────────────────────
echo ""
echo "━━━ Summary ━━━"
if [ $FAILURES -eq 0 ]; then
  echo "All checks passed."
  exit 0
else
  echo "$FAILURES check(s) failed."
  exit 1
fi
