from django_doctor.core.diagnostics import Diagnostic, DoctorResult, ProjectInfo, ScanInfo, Score
from django_doctor.reporters.text import render_text


def test_text_reporter_handles_diagnostic_without_location_and_bad_explain() -> None:
    result = DoctorResult(
        ok=True,
        project=ProjectInfo(name="example", root="/tmp/example"),
        scan=ScanInfo(mode="full", files_scanned=1, rules_enabled=1),
        score=Score(value=99, label="excellent"),
        summary={"error": 0, "warning": 0, "info": 1},
        diagnostics=[
            Diagnostic(
                id="django/info/no-location",
                title="No location",
                severity="info",
                category="testing",
                message="No file attached.",
            )
        ],
    )

    output = render_text(result)
    bad_explain = render_text(result, verbose=True, explain="file.py:not-a-line")

    assert "django/info/no-location" in output
    assert "No location" in output
    assert "No diagnostic applies" in bad_explain
