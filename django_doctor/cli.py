from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from django_doctor.core.config import VALID_CATEGORIES, ConfigError, DoctorConfig, load_config
from django_doctor.core.diagnostics import ScanMode
from django_doctor.core.exit_codes import DIAGNOSTICS_FAILED, RUNTIME_ERROR, SUCCESS, USAGE_ERROR
from django_doctor.core.git import GitError
from django_doctor.core.output import write_output
from django_doctor.core.scanner import run_scan
from django_doctor.reporters.github import render_annotations
from django_doctor.reporters.json import render_error, render_json
from django_doctor.reporters.text import render_text
from django_doctor.rules.registry import implemented_rule_ids

AUTO_DIFF = "__django_doctor_auto_diff__"
FAIL_LEVELS = {"error", "warning", "none"}

app = typer.Typer(add_completion=False, no_args_is_help=False)


@app.command()
def scan_command(
    directory: Annotated[Path, typer.Argument(help="Project directory to scan.")] = Path("."),
    verbose: Annotated[bool, typer.Option("--verbose", help="Show expanded details.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output pretty JSON.")] = False,
    json_compact: Annotated[
        bool, typer.Option("--json-compact", help="Output compact JSON.")
    ] = False,
    score_only: Annotated[bool, typer.Option("--score", help="Print only numeric score.")] = False,
    output: Annotated[Path | None, typer.Option("--output", help="Write report to file.")] = None,
    diff: Annotated[
        str | None, typer.Option("--diff", help="Scan files changed from base.")
    ] = None,
    staged: Annotated[bool, typer.Option("--staged", help="Scan only staged files.")] = False,
    full: Annotated[bool, typer.Option("--full", help="Force a full project scan.")] = False,
    fail_on: Annotated[
        str | None, typer.Option("--fail-on", help="Fail on error, warning, or none.")
    ] = None,
    annotations: Annotated[
        bool, typer.Option("--annotations", help="Print GitHub Actions annotations.")
    ] = False,
    project: Annotated[str | None, typer.Option("--project", help="Override project name.")] = None,
    category: Annotated[
        list[str] | None, typer.Option("--category", help="Run only a rule category.")
    ] = None,
    ignore: Annotated[list[str] | None, typer.Option("--ignore", help="Ignore a rule id.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Config file to load.")] = None,
    explain: Annotated[
        str | None, typer.Option("--explain", help="Explain diagnostics at file:line.")
    ] = None,
) -> None:
    try:
        exit_code = _run_scan_command(
            directory=directory,
            verbose=verbose,
            json_output=json_output,
            json_compact=json_compact,
            score_only=score_only,
            output=output,
            diff=diff,
            staged=staged,
            full=full,
            fail_on=fail_on,
            annotations=annotations,
            project=project,
            category=category or [],
            ignore=ignore or [],
            config=config,
            explain=explain,
        )
    except UsageFailure as exc:
        _print_error(exc, json_output=json_output, json_compact=json_compact, code=USAGE_ERROR)
    except (ConfigError, GitError, ValueError) as exc:
        _print_error(exc, json_output=json_output, json_compact=json_compact, code=USAGE_ERROR)
    except Exception as exc:  # noqa: BLE001 - CLI must convert internal errors to stable output.
        _print_error(exc, json_output=json_output, json_compact=json_compact, code=RUNTIME_ERROR)
    else:
        raise typer.Exit(exit_code)


def _run_scan_command(
    *,
    directory: Path,
    verbose: bool,
    json_output: bool,
    json_compact: bool,
    score_only: bool,
    output: Path | None,
    diff: str | None,
    staged: bool,
    full: bool,
    fail_on: str | None,
    annotations: bool,
    project: str | None,
    category: list[str],
    ignore: list[str],
    config: Path | None,
    explain: str | None,
) -> int:
    _validate_conflicts(
        json_output=json_output,
        json_compact=json_compact,
        score_only=score_only,
        diff=diff,
        staged=staged,
        full=full,
    )
    _validate_categories(category)

    root = directory.resolve()
    doctor_config = load_config(root, config)
    selected_verbose = verbose or doctor_config.verbose
    selected_fail_on = fail_on or doctor_config.fail_on
    if selected_fail_on not in FAIL_LEVELS:
        raise UsageFailure("--fail-on must be one of: error, warning, none")

    mode, base = _select_mode(diff=diff, staged=staged, full=full, config=doctor_config)
    result = run_scan(
        root=root,
        config=doctor_config,
        mode=mode,
        base=base,
        categories=category,
        ignored_rules=ignore,
        project_name=project,
    )

    if score_only:
        rendered = f"{result.score.value}\n"
    elif json_output or json_compact:
        rendered = render_json(result, compact=json_compact)
        rendered += "\n"
    else:
        rendered = render_text(
            result,
            verbose=selected_verbose,
            ignored_count=len(set(doctor_config.ignore) | set(ignore)),
            explain=explain,
        )

    if output is not None:
        write_output(output, rendered)
        if not (json_output or json_compact or score_only):
            sys.stdout.write(f"Report written to {output}\n")
    else:
        sys.stdout.write(rendered)

    if annotations:
        annotation_text = render_annotations(result.diagnostics)
        if json_output or json_compact:
            sys.stderr.write(annotation_text)
        elif annotation_text:
            sys.stdout.write(annotation_text)

    return _exit_for_fail_on(result.summary, selected_fail_on)


def install_command() -> int:
    root = Path.cwd()
    target = root / ".django-doctor"
    target.mkdir(parents=True, exist_ok=True)
    (target / "AGENTS.md").write_text(_agents_md(), encoding="utf-8")
    (target / "usage.md").write_text(_usage_md(), encoding="utf-8")
    (target / "rules.md").write_text(_rules_md(), encoding="utf-8")
    Console().print("Installed Django Doctor agent instructions in .django-doctor/")
    return SUCCESS


def _validate_conflicts(
    *,
    json_output: bool,
    json_compact: bool,
    score_only: bool,
    diff: str | None,
    staged: bool,
    full: bool,
) -> None:
    if diff is not None and staged:
        raise UsageFailure("--diff and --staged cannot be used together")
    if full and diff is not None:
        raise UsageFailure("--full and --diff cannot be used together")
    if full and staged:
        raise UsageFailure("--full and --staged cannot be used together")
    if json_output and score_only:
        raise UsageFailure("--json and --score cannot be used together")
    if json_compact and score_only:
        raise UsageFailure("--json-compact and --score cannot be used together")
    if json_output and json_compact:
        raise UsageFailure("--json and --json-compact cannot be used together")


def _validate_categories(categories: list[str]) -> None:
    unknown = sorted(set(categories) - VALID_CATEGORIES)
    if unknown:
        valid = ", ".join(sorted(VALID_CATEGORIES))
        raise UsageFailure(f"Unknown category: {', '.join(unknown)}. Valid categories: {valid}")


def _select_mode(
    *, diff: str | None, staged: bool, full: bool, config: DoctorConfig
) -> tuple[ScanMode, str | None]:
    if full:
        return "full", None
    if staged:
        return "staged", None
    if diff is not None:
        return "diff", None if diff == AUTO_DIFF else diff
    if isinstance(config.diff, str) and config.diff:
        return "diff", config.diff
    if config.diff is True:
        return "diff", None
    return "full", None


def _exit_for_fail_on(summary: dict[str, int], fail_on: str) -> int:
    if fail_on == "error" and summary.get("error", 0) > 0:
        return DIAGNOSTICS_FAILED
    if fail_on == "warning" and (summary.get("error", 0) > 0 or summary.get("warning", 0) > 0):
        return DIAGNOSTICS_FAILED
    return SUCCESS


def _print_error(exc: Exception, *, json_output: bool, json_compact: bool, code: int) -> None:
    if json_output or json_compact:
        sys.stdout.write(render_error(type(exc).__name__, str(exc), compact=json_compact) + "\n")
    else:
        Console(stderr=True).print(f"Error: {exc}")
    raise typer.Exit(code)


def _agents_md() -> str:
    return """# Django Doctor Agent Instructions

- Run `uv run django-doctor . --diff main --verbose` after making changes.
- Run `uv run django-doctor . --staged` before committing.
- Avoid introducing new warnings/errors.
- Prefer fixing diagnostics in changed files first.
- Use `--json` for machine-readable output.
- Use `--explain file:line` to understand a diagnostic.
"""


def _usage_md() -> str:
    return """# Django Doctor Usage

```bash
uv run django-doctor .
uv run django-doctor . --verbose
uv run django-doctor . --json
uv run django-doctor . --diff main
uv run django-doctor . --staged
uv run django-doctor . --fail-on warning
uv run django-doctor . --annotations
```
"""


def _rules_md() -> str:
    rules = "\n".join(f"- `{rule_id}`" for rule_id in implemented_rule_ids())
    return f"""# Django Doctor Rules

Initial implemented rules:

{rules}
"""


class UsageFailure(Exception):
    """Raised for CLI usage errors that should exit with code 2."""


def _preprocess_args(args: list[str]) -> list[str]:
    processed: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        processed.append(arg)
        if arg == "--diff":
            next_arg = args[index + 1] if index + 1 < len(args) else None
            if next_arg is None or next_arg.startswith("-"):
                processed.append(AUTO_DIFF)
        index += 1
    return processed


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "install":
        raise typer.Exit(install_command())
    sys.argv = [sys.argv[0], *_preprocess_args(args)]
    app()


if __name__ == "__main__":
    main()
