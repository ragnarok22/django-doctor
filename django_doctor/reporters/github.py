from __future__ import annotations

from django_doctor.core.diagnostics import Diagnostic

ANNOTATION_COMMANDS = {"error": "error", "warning": "warning", "info": "notice"}


def render_annotations(diagnostics: list[Diagnostic]) -> str:
    lines = []
    for diagnostic in diagnostics:
        command = ANNOTATION_COMMANDS[diagnostic.severity]
        properties = []
        if diagnostic.file:
            properties.append(f"file={_escape(diagnostic.file)}")
        if diagnostic.line:
            properties.append(f"line={diagnostic.line}")
        prop_text = f" {','.join(properties)}" if properties else ""
        lines.append(f"::{command}{prop_text}::{_escape(diagnostic.message)}")
    return "\n".join(lines) + ("\n" if lines else "")


def _escape(value: str) -> str:
    return (
        value.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )
