# django-doctor

`django-doctor` is a Django-aware health scanner for local development, code review, and CI. It is inspired by React Doctor and focuses on fast, actionable diagnostics for common Django security, architecture, DRF, and testing issues.

This first version provides the CLI foundation, JSON reporting, scoring, diff/staged scans, GitHub Actions annotations, and an extensible rule architecture.

## Why it exists

Django projects accumulate risk in settings files, serializers, permissions, and large modules. `django-doctor` gives teams and AI coding agents a consistent command to run after changes and before commits.

## Installation

For local development from this repository:

```bash
uv sync
uv run django-doctor .
```

When published:

```bash
uv tool install django-doctor
django-doctor .
```

## Basic usage

```bash
uv run django-doctor
uv run django-doctor .
uv run django-doctor . --verbose
uv run django-doctor . --score
```

## CLI options

```bash
django-doctor [directory] [options]
```

Useful options:

- `--verbose`: show full diagnostic details.
- `--json`: print pretty JSON.
- `--json-compact`: print minified JSON.
- `--score`: print only the numeric score.
- `--output <file>`: write the selected report to a file.
- `--diff [base]`: scan files changed against a base branch.
- `--staged`: scan staged files for pre-commit hooks.
- `--full`: force a full scan.
- `--fail-on error|warning|none`: control CI failure behavior.
- `--annotations`: print GitHub Actions annotations.
- `--project <name>`: override project name.
- `--category <category>`: run only selected categories.
- `--ignore <rule-id>`: suppress a rule.
- `--config <file>`: load a specific config file.
- `--explain file:line`: explain diagnostics at one location.

## Output formats

Human report:

```bash
uv run django-doctor . --verbose
```

JSON report:

```bash
uv run django-doctor . --json
uv run django-doctor . --json-compact
```

Write reports:

```bash
uv run django-doctor . --output report.txt
uv run django-doctor . --json --output report.json
```

## Diff mode

```bash
uv run django-doctor . --diff
uv run django-doctor . --diff main
```

Without a base, `django-doctor` tries `main`, `master`, `origin/main`, then `origin/master`.

## Staged mode

```bash
uv run django-doctor . --staged
```

This is intended for pre-commit hooks and scans only staged files.

## CI usage

Fail on errors:

```bash
uv run django-doctor . --fail-on error
```

Fail on warnings or errors:

```bash
uv run django-doctor . --fail-on warning
```

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

## Public API

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

## Current rules

- `django/security/debug-true`
- `django/security/secret-key-hardcoded`
- `django/security/allowed-hosts-wildcard`
- `django/security/cors-allow-all`
- `django/architecture/large-file`
- `django/drf/serializer-fields-all`
- `django/drf/allow-any-permission`
- `django/testing/no-tests-detected`

## Inline ignores

Inline suppression comments are planned for a future version:

```python
# django-doctor-disable-next-line django/security/debug-true
DEBUG = True
```

For now, use `--ignore <rule-id>` or config `ignore = [...]`.

## Agent install

```bash
uv run django-doctor install
```

This creates `.django-doctor/AGENTS.md`, `.django-doctor/rules.md`, and `.django-doctor/usage.md`.

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
