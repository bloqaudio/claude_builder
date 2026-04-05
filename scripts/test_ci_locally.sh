#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Testing CI pipeline locally..."
echo "================================="
echo "Policy: required gates target Python 3.11+; CI matrix covers 3.11, 3.12, and 3.13."

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if ! command -v uv >/dev/null 2>&1; then
    echo -e "${RED}❌ uv is required to mirror CI locally.${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Installing development dependencies...${NC}"
uv pip install -e ".[dev,test]"

echo -e "${BLUE}🔍 Verifying Python version...${NC}"
uv run python - <<'PY'
import sys

if sys.version_info < (3, 11):
    raise SystemExit(f"Local CI script requires Python 3.11+; found {sys.version.split()[0]}")

print(f"Using Python {sys.version.split()[0]}")
PY

echo -e "${BLUE}🧪 Running required CI gates...${NC}"

echo "  • Ruff correctness gate..."
uv run ruff check src/claude_builder --select E9,F63,F7,F82

echo "  • MyPy type check..."
uv run mypy src/claude_builder --ignore-missing-imports

echo "  • Bandit security gate..."
uv run bandit -r src/claude_builder -lll -iii

echo "  • Pytest required suite (excluding quarantined failing tests)..."
uv run pytest -m "not failing" \
  --cov=claude_builder \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov \
  --cov-report=term-missing \
  --junitxml=junit.xml \
  -v

echo -e "${BLUE}📊 Coverage Summary:${NC}"
uv run coverage report

echo -e "${BLUE}🔧 Testing installed CLI...${NC}"
uv run claude-builder --help > /dev/null
uv run claude-builder --version > /dev/null

echo -e "${BLUE}ℹ️  Informational workflow lint...${NC}"
if command -v actionlint >/dev/null 2>&1; then
    actionlint .github/workflows/*.yml || echo -e "${YELLOW}⚠️  actionlint reported workflow issues (informational)${NC}"
else
    echo -e "${YELLOW}⚠️  actionlint not installed; skipping informational workflow lint.${NC}"
fi

echo ""
echo "================================="
echo -e "${GREEN}🎉 Local CI Test Complete!${NC}"
echo "================================="
echo "Artifacts: coverage.xml, htmlcov/, junit.xml"
echo "Required gates mirrored: ruff E9/F63/F7/F82, mypy, bandit -lll -iii, pytest -m 'not failing'"
