# Release Policy

This document is the single source of truth for merge
and publish quality gates.

## Test Policy

- `@pytest.mark.failing` tests are quarantined and non-blocking.
- Required gate command for both CI and publish validation:

```bash
uv run pytest -m "not failing" \
  --cov=claude_builder --cov-report=xml:coverage.xml -v
```

## Required Merge Gates

PRs to `main` must pass:

```bash
uv run ruff check src/claude_builder --select E9,F63,F7,F82
uv run mypy src/claude_builder --ignore-missing-imports
uv run bandit -r src/claude_builder -lll -iii
uv run pytest -m "not failing" \
  --cov=claude_builder --cov-report=xml:coverage.xml -v
```

## Required Publish Gates

The publish workflow (`.github/workflows/publish.yml`)
runs the same preflight policy via
`scripts/release_preflight.sh`.

Publish is blocked unless all of the following pass:

- Lint/type/security/test checks from the merge gates above.
- Package version consistency
  (`src/claude_builder/__init__.py` and `pyproject.toml`).
- Changelog contains a matching heading: `## [x.y.z]`.
- Trusted Publishing is configured for the repository/workflow on
  both PyPI and TestPyPI.

## Trusted Publishing Prerequisites

The release workflow now publishes with GitHub OIDC Trusted Publishing.
Do **not** configure `PYPI_API_TOKEN` or `TEST_PYPI_API_TOKEN` secrets
for normal releases. Instead:

1. Create the GitHub environments used by the workflow:
   - `test-pypi` for prereleases and manual TestPyPI uploads
   - `pypi` for production releases
2. Configure matching trusted publishers on TestPyPI/PyPI for
   `.github/workflows/publish.yml`.
3. Keep the publish job separate from the build job so the `id-token`
   permission is only granted where publishing happens.

Trusted Publishing uploads PEP 740 attestations alongside the published
distributions, providing signed provenance for each release artifact.

## Changelog Requirement

Before publishing tag `vX.Y.Z`, add a heading exactly matching:

- `## [X.Y.Z] - YYYY-MM-DD`

## Local Preflight

Run before cutting a release:

- `./scripts/release_preflight.sh X.Y.Z`

This command mirrors publish validation behavior.

## Post-Publish Verification

The workflow verifies package propagation honestly instead of using fixed
`sleep` delays:

- `scripts/wait_for_pypi_release.py --repository testpypi --package`
  `claude-builder --version X.Y.Z`
- `scripts/wait_for_pypi_release.py --repository pypi --package`
  `claude-builder --version X.Y.Z`

Once the requested version appears on the index, the workflow installs the
**exact published version** and checks the CLI before reporting success.

## Quarantine Burn-Down

- Track count of `@pytest.mark.failing` tests per sprint.
- Prioritize de-quarantining high-impact suites
  (CLI, generation, config).
- Tighten publish policy to full-suite only after
  quarantine reaches planned threshold.
