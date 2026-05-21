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


def test_scoring_labels_lower_ranges() -> None:
    warning_diagnostics = [
        Diagnostic(
            id=f"django/warning/{index}",
            title="Warning",
            severity="warning",
            category="testing",
            message="warning",
        )
        for index in range(20)
    ]
    error_diagnostics = [
        Diagnostic(
            id=f"django/error/{index}",
            title="Error",
            severity="error",
            category="testing",
            message="error",
        )
        for index in range(20)
    ]
    many_errors = error_diagnostics + [
        Diagnostic(
            id=f"django/more-error/{index}",
            title="Error",
            severity="error",
            category="testing",
            message="error",
        )
        for index in range(10)
    ]

    assert calculate_score(warning_diagnostics).label == "good"
    assert calculate_score(error_diagnostics).label == "needs_work"
    assert calculate_score(warning_diagnostics + many_errors).label == "critical"
