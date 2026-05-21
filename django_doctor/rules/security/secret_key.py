from __future__ import annotations

import re

from django_doctor.core.context import ScanContext
from django_doctor.core.diagnostics import Diagnostic
from django_doctor.rules.base import Rule


class SecretKeyHardcodedRule(Rule):
    id = "django/security/secret-key-hardcoded"
    title = "SECRET_KEY is hardcoded"
    category = "security"
    default_severity = "error"
    tags = ["security", "secrets", "deployment"]

    def check(self, context: ScanContext) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        assignment = re.compile(r"^\s*SECRET_KEY\s*=\s*(?P<value>.+)")
        for file in context.settings_files():
            content = context.read_file(file)
            if content is None:
                continue
            for line_number, line in enumerate(content.splitlines(), start=1):
                match = assignment.search(line)
                if not match:
                    continue
                value = match.group("value").split("#", maxsplit=1)[0].strip()
                if _looks_environment_based(value):
                    continue
                if re.match(r"^[rubfRUBF]*['\"].+['\"]$", value):
                    diagnostics.append(
                        self.diagnostic(
                            message="A hardcoded SECRET_KEY assignment was detected.",
                            file=file,
                            line=line_number,
                            recommendation=(
                                "Load SECRET_KEY from environment variables or a secret manager."
                            ),
                            why=(
                                "Hardcoded secrets can leak through source control "
                                "and build artifacts."
                            ),
                            confidence="high",
                        )
                    )
        return diagnostics


def _looks_environment_based(value: str) -> bool:
    safe_markers = [
        "os.environ",
        "environ.",
        "getenv(",
        "env(",
        "config(",
        "decouple",
        "django-environ",
    ]
    return any(marker in value for marker in safe_markers)
