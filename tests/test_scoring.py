from django_doctor.core.diagnostics import Diagnostic
from django_doctor.core.scoring import calculate_score


def test_scoring_uses_unique_rule_ids() -> None:
    diagnostics = [
        Diagnostic(
            id="django/security/debug-true",
            title="DEBUG is enabled",
            severity="error",
            category="security",
            message="DEBUG=True was detected.",
        ),
        Diagnostic(
            id="django/security/debug-true",
            title="DEBUG is enabled",
            severity="error",
            category="security",
            message="DEBUG=True was detected.",
        ),
        Diagnostic(
            id="django/drf/allow-any-permission",
            title="AllowAny permission used",
            severity="info",
            category="drf",
            message="permission_classes contains AllowAny.",
        ),
    ]

    score = calculate_score(diagnostics)

    assert score.value == 98
    assert score.label == "excellent"
