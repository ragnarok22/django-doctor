# django-doctor

[![CI](https://github.com/ragnarok22/django-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/ragnarok22/django-doctor/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ragnarok22/django-doctor/branch/main/graph/badge.svg)](https://codecov.io/gh/ragnarok22/django-doctor)
[![Python 3.12 | 3.13 | 3.14](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://github.com/ragnarok22/django-doctor/actions/workflows/ci.yml)
[![pytest](https://img.shields.io/badge/tests-pytest-0A9EDC.svg)](https://docs.pytest.org/)
[![Ruff](https://img.shields.io/badge/linting%20%26%20formatting-ruff-261230.svg)](https://docs.astral.sh/ruff/)
[![uv](https://img.shields.io/badge/package%20manager-uv-654FF0.svg)](https://docs.astral.sh/uv/)
[![GitHub issues](https://img.shields.io/github/issues/ragnarok22/django-doctor.svg)](https://github.com/ragnarok22/django-doctor/issues)
[![Last commit](https://img.shields.io/github/last-commit/ragnarok22/django-doctor.svg)](https://github.com/ragnarok22/django-doctor/commits/main)

`django-doctor` is a Django-aware health scanner for local development, code review, CI, and AI coding agents.

It scans a project for common Django risks, reports actionable diagnostics, produces a simple health score, and supports full, diff-only, and staged-file workflows.

## Highlights

- Django-focused rules for settings, security, DRF, architecture, and tests.
- Human-readable terminal reports plus stable JSON output.
- `--diff` and `--staged` modes for pull requests and pre-commit hooks.
- CI-friendly exit codes with `--fail-on error|warning|none`.
- GitHub Actions annotations with `--annotations`.
- Extensible rule architecture for future checks.
- Public Python API via `django_doctor.api.diagnose`.

## Requirements

- Python 3.12+
- `uv` for local development and command execution

## Installation

From this repository:

```bash
uv sync
uv run django-doctor .
```

After package publication:

```bash
uv tool install django-doctor
django-doctor .
```

Or inside a project:

```bash
uv add --dev django-doctor
uv run django-doctor .
```

## Quickstart

Run a full scan:

```bash
uv run django-doctor .
```

Show detailed explanations:

```bash
uv run django-doctor . --verbose
```

Print only the numeric score:

```bash
uv run django-doctor . --score
```

Scan only changed files against `main`:

```bash
uv run django-doctor . --diff main
```

Scan only staged files:

```bash
uv run django-doctor . --staged
```

Fail CI on warnings or errors:

```bash
uv run django-doctor . --fail-on warning
```

## Example Report

```text
✓ Running django-doctor checks.
Project: my-project  Mode: full  Score: 88/100 (good)
Errors: 1  Warnings: 4  Info: 2

  ▲ django/security/debug-true ×2
     DEBUG is enabled
     → Use an environment variable and default DEBUG to False.
     config/settings.py:12
     config/production_settings.py:8

Run with --verbose for detailed explanations.
```

## Command Reference

```bash
django-doctor [directory] [options]
```

The `directory` argument defaults to the current directory.

| Option | Description |
| --- | --- |
| `--verbose` | Show expanded diagnostic details. |
| `--json` | Print pretty machine-readable JSON. |
| `--json-compact` | Print minified JSON. |
| `--score` | Print only the numeric score. |
| `--output <file>` | Write the selected report format to a file. |
| `--diff [base]` | Scan files changed against a base branch or ref. |
| `--staged` | Scan only staged files. |
| `--full` | Force a complete project scan. |
| `--fail-on error\|warning\|none` | Control CI failure behavior. |
| `--annotations` | Print GitHub Actions annotations. |
| `--project <name>` | Override the detected project name. |
| `--category <category>` | Run only rules from a category. Can be repeated. |
| `--ignore <rule-id>` | Ignore diagnostics from a rule. Can be repeated. |
| `--config <file>` | Load a specific config file. |
| `--explain file:line` | Explain diagnostics at a specific location. |

## Output Formats

Pretty JSON:

```bash
uv run django-doctor . --json
```

Compact JSON:

```bash
uv run django-doctor . --json-compact
```

Write a text report:

```bash
uv run django-doctor . --output report.txt
```

Write a JSON report:

```bash
uv run django-doctor . --json --output report.json
```

Normal JSON output has this shape:

```json
{
  "ok": true,
  "project": {
    "name": "example-project",
    "root": "/absolute/path",
    "framework": "django",
    "django_version": null
  },
  "scan": {
    "mode": "full",
    "base": null,
    "staged": false,
    "files_scanned": 42,
    "rules_enabled": 8
  },
  "score": {
    "value": 88,
    "label": "good"
  },
  "summary": {
    "error": 1,
    "warning": 4,
    "info": 2
  },
  "diagnostics": []
}
```

## Diff Mode

Diff mode scans only files changed against a base ref:

```bash
uv run django-doctor . --diff main
```

If no base is provided, `django-doctor` tries these refs in order:

- `main`
- `master`
- `origin/main`
- `origin/master`

```bash
uv run django-doctor . --diff
```

Diff mode uses git and returns a clear usage error if the current directory is not in a git repository or the base cannot be detected.

## Staged Mode

Staged mode scans only files staged for commit:

```bash
uv run django-doctor . --staged
```

This is intended for pre-commit hooks and local commit checks.

## CI Behavior

By default, diagnostics do not fail the process. Use `--fail-on` in CI:

```bash
uv run django-doctor . --fail-on error
uv run django-doctor . --fail-on warning
uv run django-doctor . --fail-on none
```

Exit codes:

| Code | Meaning |
| --- | --- |
| `0` | Success. |
| `1` | Diagnostics met the configured failure threshold. |
| `2` | CLI usage or configuration error. |
| `3` | Runtime/internal error. |

## GitHub Actions

```yaml
name: Django Doctor

on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install django-doctor

      - run: django-doctor . --diff main --fail-on warning --annotations
```

With `--json` or `--json-compact`, annotations are written to stderr so stdout remains valid JSON.

## Pre-commit

```yaml
repos:
  - repo: local
    hooks:
      - id: django-doctor
        name: django-doctor
        entry: uv run django-doctor . --staged --fail-on warning
        language: system
        pass_filenames: false
```

## Configuration

`pyproject.toml` is preferred:

```toml
[tool.django-doctor]
diff = "main"
verbose = false
fail_on = "error"
exclude = [
  ".venv",
  "venv",
  "node_modules",
  "staticfiles",
  "media",
  "*/migrations/*",
]
ignore = [
  "django/architecture/large-file",
]

[tool.django-doctor.rules]
max_views_file_lines = 400
max_models_file_lines = 500
max_serializers_file_lines = 400
check_drf_permissions = true
check_debug_true = true
```

You can also use `django-doctor.config.json` or pass `--config <file>`.

Default excluded directories include `.git`, `.venv`, `venv`, `env`, `__pycache__`, `node_modules`, `staticfiles`, `media`, `dist`, `build`, `.mypy_cache`, `.pytest_cache`, and `.ruff_cache`.

## Categories

Supported categories are:

- `security`
- `settings`
- `database`
- `migrations`
- `performance`
- `drf`
- `architecture`
- `testing`
- `templates`
- `admin`
- `dependencies`

Not every category has active rules yet, but the scanner and config model support them.

Run only selected categories:

```bash
uv run django-doctor . --category security --category drf
```

## Current Rules

| Rule | Severity | Description |
| --- | --- | --- |
| `django/security/debug-true` | error | Detects `DEBUG = True` in likely settings files. |
| `django/security/secret-key-hardcoded` | error | Detects obvious hardcoded `SECRET_KEY` assignments. |
| `django/security/allowed-hosts-wildcard` | warning | Detects wildcard `ALLOWED_HOSTS`. |
| `django/security/cors-allow-all` | warning | Detects `CORS_ALLOW_ALL_ORIGINS = True`. |
| `django/architecture/large-file` | warning | Detects oversized `views.py`, `models.py`, and `serializers.py`. |
| `django/drf/serializer-fields-all` | warning | Detects serializers using `fields = "__all__"`. |
| `django/drf/allow-any-permission` | info | Detects DRF `permission_classes` containing `AllowAny`. |
| `django/testing/no-tests-detected` | info | Detects Django-like apps without `tests.py` or `tests/`. |

## Scoring

Scores start at `100` and are penalized by unique triggered rule IDs, not by occurrence count:

- Unique error rules: `-2` each.
- Unique warning rules: `-1` each.
- Unique info rules: `-0.25` each.

Labels:

| Score | Label |
| --- | --- |
| `85-100` | `excellent` |
| `75-84` | `good` |
| `50-74` | `needs_work` |
| `0-49` | `critical` |

## Public Python API

```python
from django_doctor.api import diagnose

result = diagnose(
    path=".",
    verbose=False,
    mode="full",
    base=None,
    staged=False,
    categories=None,
    ignored_rules=None,
)

print(result.model_dump())
```

The returned object is structured and serializable.

## Agent Install

Generate project-local instructions for AI coding agents:

```bash
uv run django-doctor install
```

This creates:

```text
.django-doctor/
  AGENTS.md
  rules.md
  usage.md
```

## Inline Ignores

Inline suppression comments are planned but not implemented yet:

```python
# django-doctor-disable-next-line django/security/debug-true
DEBUG = True
```

For now, suppress rules with `--ignore <rule-id>` or config `ignore = [...]`.

## Development

Install dependencies:

```bash
uv sync
```

Run tests:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov
```

Run linting and formatting:

```bash
uv run ruff check .
uv run ruff format .
```

Build package artifacts:

```bash
uv build
```

## Roadmap

- Inline suppression comments.
- Runtime Django checks using `manage.py check --deploy`.
- Migration analysis.
- N+1 query heuristics.
- `select_related` and `prefetch_related` suggestions.
- Admin checks.
- Template checks.
- Dependency vulnerability checks.
- PR comments.
- SARIF output.
- Baseline files.
- Rule confidence thresholds.
