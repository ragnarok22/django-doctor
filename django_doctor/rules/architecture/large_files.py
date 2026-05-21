from __future__ import annotations

from pathlib import Path

from django_doctor.core.context import ScanContext
from django_doctor.core.diagnostics import Diagnostic
from django_doctor.rules.base import Rule


class LargeFileRule(Rule):
    id = "django/architecture/large-file"
    title = "Large Django module"
    category = "architecture"
    default_severity = "warning"
    tags = ["maintainability", "architecture"]

    def check(self, context: ScanContext) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        thresholds = {
            "views.py": int(context.rule_setting("max_views_file_lines", 400)),
            "models.py": int(context.rule_setting("max_models_file_lines", 500)),
            "serializers.py": int(context.rule_setting("max_serializers_file_lines", 400)),
        }
        for file in context.python_files():
            name = Path(file).name
            threshold = thresholds.get(name)
            if threshold is None:
                continue
            content = context.read_file(file)
            if content is None:
                continue
            line_count = len(content.splitlines())
            if line_count > threshold:
                message = (
                    f"{name} has {line_count} lines, above the configured limit of {threshold}."
                )
                diagnostics.append(
                    self.diagnostic(
                        message=message,
                        file=file,
                        line=threshold + 1,
                        recommendation="Split large modules by responsibility.",
                        why=(
                            "Very large Django modules are harder to review, "
                            "test, and safely change."
                        ),
                        confidence="high",
                    )
                )
        return diagnostics
