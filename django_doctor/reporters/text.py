from __future__ import annotations

from collections import defaultdict

from django_doctor.core.diagnostics import Diagnostic, DoctorResult

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
RED = "\x1b[31m"
CYAN = "\x1b[36m"
GRAY = "\x1b[90m"


def render_text(
    result: DoctorResult,
    *,
    verbose: bool = False,
    ignored_count: int = 0,
    explain: str | None = None,
) -> str:
    if verbose or explain is not None:
        return _render_verbose_text(result, ignored_count=ignored_count, explain=explain)

    lines = [
        "Django Doctor Report",
        "",
        f"Project: {result.project.name}",
        f"Root: {result.project.root}",
        f"Mode: {_mode_line(result)}",
        f"Score: {result.score.value}/100 - {result.score.label}",
        "",
        "Summary:",
        f"  Errors: {result.summary.get('error', 0)}",
        f"  Warnings: {result.summary.get('warning', 0)}",
        f"  Info: {result.summary.get('info', 0)}",
    ]

    selected = _filter_explain(result.diagnostics, explain)
    if explain is not None and not selected:
        lines.extend(["", f"No diagnostic applies at {explain}."])
        return "\n".join(lines) + "\n"

    lines.extend(["", "Diagnostics:"])
    if not selected:
        lines.append("  No diagnostics found.")
    for diagnostic in selected:
        lines.extend(_compact_diagnostic(diagnostic))

    if explain is None and selected:
        lines.extend(["", "Run with --verbose for detailed explanations."])
    return "\n".join(lines) + "\n"


def _render_verbose_text(
    result: DoctorResult, *, ignored_count: int = 0, explain: str | None = None
) -> str:
    selected = _filter_explain(result.diagnostics, explain)
    lines = [
        _style("✓", GREEN) + " Running django-doctor checks.",
        _style(
            f"Project: {result.project.name}  "
            f"Mode: {_mode_line(result)}  "
            f"Score: {result.score.value}/100 ({result.score.label})",
            DIM,
        ),
        _style(
            f"Files: {result.scan.files_scanned}  "
            f"Rules: {result.scan.rules_enabled}  "
            f"Ignores: {ignored_count}",
            DIM,
        ),
        "",
    ]

    if explain is not None and not selected:
        lines.append(f"No diagnostic applies at {explain}.")
        return "\n".join(lines) + "\n"

    if not selected:
        lines.append(_style("✓", GREEN) + " No diagnostics found.")
        return "\n".join(lines) + "\n"

    for group in _group_diagnostics(selected):
        lines.extend(_verbose_group(group))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _mode_line(result: DoctorResult) -> str:
    if result.scan.mode == "diff":
        return f"diff ({result.scan.base})"
    return result.scan.mode


def _compact_diagnostic(diagnostic: Diagnostic) -> list[str]:
    location = _location(diagnostic)
    lines = [
        f"  [{diagnostic.severity}] {diagnostic.id}",
        f"  {diagnostic.title}",
    ]
    if location:
        lines.append(f"  {location}")
    if diagnostic.recommendation:
        lines.append(f"  {diagnostic.recommendation}")
    lines.append("")
    return lines


def _verbose_group(diagnostics: list[Diagnostic]) -> list[str]:
    first = diagnostics[0]
    severity_color = _severity_color(first.severity)
    count = f" ×{len(diagnostics)}" if len(diagnostics) > 1 else ""
    lines = [
        f"  {_style('▲', severity_color)} "
        f"{_style(first.id, severity_color + BOLD)}{_style(count, GRAY)}",
        _style(f"     {first.title}", DIM),
        _style(f"     {first.message}", DIM),
    ]
    if first.recommendation:
        lines.append(_style(f"     → {first.recommendation}", DIM))
    if first.why:
        lines.append(_style(f"     Why: {first.why}", DIM))

    meta = f"severity: {first.severity}  category: {first.category}"
    if first.confidence:
        meta += f"  confidence: {first.confidence}"
    if first.tags:
        meta += f"  tags: {', '.join(first.tags)}"
    lines.append(_style(f"     {meta}", GRAY))

    for diagnostic in diagnostics:
        location = _location(diagnostic)
        if location:
            lines.append(_style(f"     {location}", GRAY))
    return lines


def _group_diagnostics(diagnostics: list[Diagnostic]) -> list[list[Diagnostic]]:
    grouped: dict[str, list[Diagnostic]] = defaultdict(list)
    for diagnostic in diagnostics:
        grouped[diagnostic.id].append(diagnostic)
    return list(grouped.values())


def _severity_color(severity: str) -> str:
    if severity == "error":
        return RED
    if severity == "warning":
        return YELLOW
    return CYAN


def _style(text: str, code: str) -> str:
    return f"{code}{text}{RESET}"


def _location(diagnostic: Diagnostic) -> str | None:
    if diagnostic.file is None:
        return None
    if diagnostic.line is None:
        return diagnostic.file
    return f"{diagnostic.file}:{diagnostic.line}"


def _filter_explain(diagnostics: list[Diagnostic], explain: str | None) -> list[Diagnostic]:
    if explain is None:
        return diagnostics
    if ":" not in explain:
        return []
    file, raw_line = explain.rsplit(":", maxsplit=1)
    try:
        line = int(raw_line)
    except ValueError:
        return []
    return [
        diagnostic
        for diagnostic in diagnostics
        if diagnostic.file == file and diagnostic.line == line
    ]
