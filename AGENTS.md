# Agent Notes

## Commands

- Use `uv` for all project commands: `uv sync`, `uv run ...`, `uv build`.
- Before finishing code changes, run tests, formatter, and lint: `uv run pytest && uv run ruff format . && uv run ruff check .`.
- Coverage command: `uv run pytest --cov`.
- Focused test example: `uv run pytest tests/test_cli.py::test_json_returns_valid_json`.
- CLI smoke checks: `uv run django-doctor . --verbose`, `uv run django-doctor . --json`, `uv run django-doctor . --score`.
- `uv run django-doctor` only works because `pyproject.toml` has `[tool.uv] package = true` and Hatchling build metadata; keep those if editing packaging.

## Architecture

- Console entrypoint is `django_doctor.cli:main`; public API entrypoint is `django_doctor.api:diagnose`.
- `django_doctor/cli.py` should only parse options, validate conflicts, render reports, and translate exceptions to exit codes; scanner/rule logic belongs under `core/` or `rules/`.
- `django_doctor.core.scanner.run_scan` selects files, builds `ScanContext`, runs registered rules, sorts diagnostics, scores, and returns `DoctorResult`.
- Add new rules by implementing `Rule.check(context)` under `django_doctor/rules/...` and registering the class in `django_doctor/rules/registry.py`.
- Result shapes live in `django_doctor/core/diagnostics.py`; JSON output should come from Pydantic serialization, not hand-built dicts in the CLI.

## CLI Gotchas

- The scan command is a single Typer command, not a normal subcommand group; tests invoke it with `CliRunner(app, [...])`.
- `django-doctor install` is manually dispatched in `main()` before Typer runs, so test it through `install_command()` or the installed script, not `CliRunner(app, ["install"])`.
- `--diff` supports an optional base by preprocessing argv in `_preprocess_args`; direct `CliRunner(app, ["--diff"])` bypasses that wrapper.
- JSON and score output must use raw `sys.stdout.write`; Rich can wrap long JSON strings and make stdout invalid JSON.
- With `--json --annotations`, annotations must go to stderr so stdout remains parseable JSON.

## Behavior To Preserve

- Exit codes are fixed in `django_doctor/core/exit_codes.py`: `0` success, `1` fail-on threshold, `2` usage/config/git error, `3` runtime error.
- `--json`, `--json-compact`, and `--score` are mutually exclusive; `--diff`, `--staged`, and `--full` conflict as documented.
- Scoring penalizes unique triggered rule IDs, not total diagnostic occurrences.
- Diff/staged scans use subprocess git helpers in `django_doctor/core/git.py` and filter through `core/files.py` to ignore deleted, binary, symlinked, excluded, and irrelevant files.
- Diagnostics should use paths relative to the scanned root and deterministic sorting via `diagnostic_sort_key`.

## Docs

- Update `README.md` when changing CLI flags, output shape, exit codes, config keys, or implemented rules.
- Keep the generated install content in `django_doctor/cli.py` (`_agents_md`, `_usage_md`, `_rules_md`) aligned with implemented rules and recommended commands.
