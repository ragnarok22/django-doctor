from __future__ import annotations

import re

from django_doctor.core.context import ScanContext
from django_doctor.core.diagnostics import Diagnostic
from django_doctor.rules.base import Rule


class CorsAllowAllRule(Rule):
    id = "django/security/cors-allow-all"
    title = "CORS allows all origins"
    category = "security"
    default_severity = "warning"
    tags = ["security", "cors", "deployment"]

    def check(self, context: ScanContext) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        pattern = re.compile(r"^\s*CORS_ALLOW_ALL_ORIGINS\s*=\s*True\b")
        for file in context.settings_files():
            content = context.read_file(file)
            if content is None:
                continue
            for line_number, line in enumerate(content.splitlines(), start=1):
                if pattern.search(line):
                    diagnostics.append(
                        self.diagnostic(
                            message="CORS_ALLOW_ALL_ORIGINS=True was detected.",
                            file=file,
                            line=line_number,
                            recommendation="Restrict CORS origins in production.",
                            why=(
                                "Permissive CORS can expose browser-accessible "
                                "endpoints to untrusted sites."
                            ),
                            confidence="high",
                        )
                    )
        return diagnostics
