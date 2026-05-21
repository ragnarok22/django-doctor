from __future__ import annotations

from pathlib import Path

from django_doctor.core.context import ScanContext
from django_doctor.core.diagnostics import Diagnostic
from django_doctor.rules.base import Rule


class NoTestsDetectedRule(Rule):
    id = "django/testing/no-tests-detected"
    title = "No tests detected for Django app"
    category = "testing"
    default_severity = "info"
    tags = ["testing", "maintainability"]

    def check(self, context: ScanContext) -> list[Diagnostic]:
        app_dirs: set[Path] = set()
        for file in context.python_files():
            path = Path(file)
            if path.name in {"models.py", "views.py"}:
                app_dirs.add(path.parent)

        diagnostics: list[Diagnostic] = []
        for app_dir in sorted(app_dirs):
            if app_dir == Path("."):
                continue
            tests_file = context.root / app_dir / "tests.py"
            tests_dir = context.root / app_dir / "tests"
            if tests_file.exists() or tests_dir.is_dir():
                continue
            target = (app_dir / "models.py").as_posix()
            if not (context.root / target).exists():
                target = (app_dir / "views.py").as_posix()
            diagnostics.append(
                self.diagnostic(
                    message=f"{app_dir.as_posix()} appears to be a Django app without tests.",
                    file=target if (context.root / target).exists() else app_dir.as_posix(),
                    line=1,
                    recommendation="Add tests for models, views, serializers, and business logic.",
                    why=(
                        "Apps with behavior but no tests are more likely to regress "
                        "during refactors."
                    ),
                    confidence="medium",
                )
            )
        return diagnostics
