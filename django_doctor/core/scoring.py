from __future__ import annotations

from django_doctor.core.diagnostics import Diagnostic, Score


def calculate_score(diagnostics: list[Diagnostic]) -> Score:
    severities_by_rule: dict[str, str] = {}
    for diagnostic in diagnostics:
        severities_by_rule.setdefault(diagnostic.id, diagnostic.severity)

    value = 100.0
    for severity in severities_by_rule.values():
        if severity == "error":
            value -= 2
        elif severity == "warning":
            value -= 1
        else:
            value -= 0.25

    rounded = round(max(0, min(100, value)))
    if rounded >= 85:
        label = "excellent"
    elif rounded >= 75:
        label = "good"
    elif rounded >= 50:
        label = "needs_work"
    else:
        label = "critical"
    return Score(value=rounded, label=label)


def summarize(diagnostics: list[Diagnostic]) -> dict[str, int]:
    return {
        "error": sum(1 for diagnostic in diagnostics if diagnostic.severity == "error"),
        "warning": sum(1 for diagnostic in diagnostics if diagnostic.severity == "warning"),
        "info": sum(1 for diagnostic in diagnostics if diagnostic.severity == "info"),
    }
