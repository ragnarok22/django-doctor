from __future__ import annotations

import re

from django_doctor.core.context import ScanContext
from django_doctor.core.diagnostics import Diagnostic
from django_doctor.rules.base import Rule


class AllowedHostsWildcardRule(Rule):
    id = "django/security/allowed-hosts-wildcard"
    title = "ALLOWED_HOSTS allows all hosts"
    category = "security"
    default_severity = "warning"
    tags = ["security", "deployment"]

    def check(self, context: ScanContext) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        pattern = re.compile(r"^\s*ALLOWED_HOSTS\s*=.*['\"]\*['\"]")
        for file in context.settings_files():
            content = context.read_file(file)
            if content is None:
                continue
            for line_number, line in enumerate(content.splitlines(), start=1):
                if pattern.search(line):
                    diagnostics.append(
                        self.diagnostic(
                            message="ALLOWED_HOSTS contains a wildcard entry.",
                            file=file,
                            line=line_number,
                            recommendation="Restrict ALLOWED_HOSTS to known domains.",
                            why="Wildcard hosts weaken host header protections in production.",
                            confidence="high",
                        )
                    )
        return diagnostics
