#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required for release preflight checks."
  echo "Install uv: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

echo "Running release preflight checks..."
echo "Supported Python policy: 3.11+ (CI target window: 3.11-3.13)"

uv run python - <<'PY'
import sys

version = sys.version_info
if version < (3, 11):
    raise SystemExit(f"release_preflight requires Python 3.11+; found {sys.version.split()[0]}")

print(f"Using Python {sys.version.split()[0]}")
PY

uv run ruff check src/claude_builder --select E9,F63,F7,F82
uv run mypy src/claude_builder --ignore-missing-imports
uv run bandit -r src/claude_builder -lll -iii
uv run pytest -m "not failing" --cov=claude_builder --cov-report=xml:coverage.xml -v

uv run python - <<'PY'
import tomllib

import claude_builder

init_version = claude_builder.__version__
with open("pyproject.toml", "rb") as f:
    pyproject = tomllib.load(f)
toml_version = pyproject["project"]["version"]

if init_version != toml_version:
    print(
        f"Version mismatch: __init__.py={init_version}, "
        f"pyproject.toml={toml_version}"
    )
    raise SystemExit(1)

print(f"Version validation passed: {init_version}")
PY

if [[ -n "$VERSION" ]]; then
  if ! grep -Eq "^## \[${VERSION}\]" CHANGELOG.md; then
    echo "No changelog entry found for version ${VERSION}"
    exit 1
  fi
  echo "Changelog entry found for version ${VERSION}"
fi

echo "Release preflight passed."
