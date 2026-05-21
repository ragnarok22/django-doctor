from django_doctor.core.diagnostics import DoctorResult, ProjectInfo, ScanInfo, Score
from django_doctor.reporters.json import render_json


def test_json_compact_returns_minified_json() -> None:
    result = DoctorResult(
        ok=True,
        project=ProjectInfo(name="example", root="/tmp/example"),
        scan=ScanInfo(mode="full", files_scanned=0, rules_enabled=0),
        score=Score(value=100, label="excellent"),
        summary={"error": 0, "warning": 0, "info": 0},
        diagnostics=[],
    )

    output = render_json(result, compact=True)

    assert "\n" not in output
    assert output.startswith('{"ok":true')
