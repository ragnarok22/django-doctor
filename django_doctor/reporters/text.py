from __future__ import annotations

from django_doctor.core.diagnostics import Diagnostic, DoctorResult


def render_text(
    result: DoctorResult,
    *,
    verbose: bool = False,
    ignored_count: int = 0,
    explain: str | None = None,
) -> str:
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

    if verbose:
        lines.extend(
            [
                "",
                "Scan:",
                f"  Files scanned: {result.scan.files_scanned}",
                f"  Rules enabled: {result.scan.rules_enabled}",
                f"  Active ignores: {ignored_count}",
            ]
        )

    selected = _filter_explain(result.diagnostics, explain)
    if explain is not None and not selected:
        lines.extend(["", f"No diagnostic applies at {explain}."])
        return "\n".join(lines) + "\n"

    lines.extend(["", "Diagnostics:"])
    if not selected:
        lines.append("  No diagnostics found.")
    for diagnostic in selected:
        if verbose or explain is not None:
            lines.extend(_verbose_diagnostic(diagnostic))
        else:
            lines.extend(_compact_diagnostic(diagnostic))

    if not verbose and explain is None and selected:
        lines.extend(["", "Run with --verbose for detailed explanations."])
    return "\n".join(lines) + "\n"


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


def _verbose_diagnostic(diagnostic: Diagnostic) -> list[str]:
    lines = [
        "",
        f"  [{diagnostic.severity}] {diagnostic.id}",
        f"  Title: {diagnostic.title}",
        f"  Category: {diagnostic.category}",
    ]
    location = _location(diagnostic)
    if location:
        lines.append(f"  Location: {location}")
    lines.append(f"  Message: {diagnostic.message}")
    if diagnostic.why:
        lines.append(f"  Why: {diagnostic.why}")
    if diagnostic.recommendation:
        lines.append(f"  Suggested fix: {diagnostic.recommendation}")
    if diagnostic.confidence:
        lines.append(f"  Confidence: {diagnostic.confidence}")
    if diagnostic.tags:
        lines.append(f"  Tags: {', '.join(diagnostic.tags)}")
    return lines


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
