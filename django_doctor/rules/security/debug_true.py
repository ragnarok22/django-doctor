from __future__ import annotations

import re

from django_doctor.core.context import ScanContext
from django_doctor.core.diagnostics import Diagnostic
from django_doctor.rules.base import Rule


class DebugTrueRule(Rule):
    id = "django/security/debug-true"
    title = "DEBUG is enabled"
    category = "security"
    default_severity = "error"
    tags = ["security", "deployment"]

    def check(self, context: ScanContext) -> list[Diagnostic]:
        if context.rule_setting("check_debug_true", True) is False:
            return []
        diagnostics: list[Diagnostic] = []
        pattern = re.compile(r"^\s*DEBUG\s*=\s*True\b")
        for file in context.settings_files():
            content = context.read_file(file)
            if content is None:
                continue
            for line_number, line in enumerate(content.splitlines(), start=1):
                if pattern.search(line):
                    diagnostics.append(
                        self.diagnostic(
                            message="DEBUG=True was detected.",
                            file=file,
                            line=line_number,
                            recommendation=(
                                "Use an environment variable and default DEBUG to False."
                            ),
                            why=(
                                "DEBUG=True can expose sensitive error pages and "
                                "configuration details."
                            ),
                            confidence="high",
                        )
                    )
        return diagnostics
