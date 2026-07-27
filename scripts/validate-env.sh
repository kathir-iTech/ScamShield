#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env}"
errors=0

echo "🔍 ScamShield Environment Validation"
echo "====================================="

# Check .env
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found at $ENV_FILE"
    echo "   Copy .env.example to .env and configure"
    exit 1
fi
echo "✅ .env file found"

# Check tools
echo ""
echo "🔍 Required Tools:"
for cmd in python3 node npm tesseract; do
    if command -v $cmd &>/dev/null; then
        echo "  ✅ $cmd: $($cmd --version 2>&1 | head -1)"
    else
        echo "  ❌ $cmd: not found"
        ((errors++))
    fi
done

# Python deps
echo ""
echo "📦 Python Dependencies:"
if [ -f "backend/requirements.txt" ]; then
    if pip list --format=columns &>/dev/null; then
        echo "  ✅ Python packages installed"
    else
        echo "  ⚠️  Run: pip install -r backend/requirements.txt"
        ((errors++))
    fi
fi

# Node deps
echo ""
echo "📦 Node Dependencies:"
if [ -d "frontend/node_modules" ]; then
    echo "  ✅ node_modules exists"
else
    echo "  ⚠️  Run: cd frontend && npm install"
    ((errors++))
fi

# Docker
echo ""
echo "🐳 Docker:"
if command -v docker &>/dev/null; then
    echo "  ✅ Docker: $(docker --version)"
else
    echo "  ⚠️  Docker not found (optional)"
fi

# Summary
echo ""
if [ $errors -eq 0 ]; then
    echo "✅ All checks passed!"
else
    echo "⚠️  $errors issues found"
fi
