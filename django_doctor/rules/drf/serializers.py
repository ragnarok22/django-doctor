from __future__ import annotations

import re

from django_doctor.core.context import ScanContext
from django_doctor.core.diagnostics import Diagnostic
from django_doctor.rules.base import Rule


class SerializerFieldsAllRule(Rule):
    id = "django/drf/serializer-fields-all"
    title = "Serializer exposes all fields"
    category = "drf"
    default_severity = "warning"
    tags = ["drf", "security", "api"]

    def check(self, context: ScanContext) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        if context.rule_setting("check_serializer_fields_all", True) is False:
            return diagnostics
        pattern = re.compile(r"^\s*fields\s*=\s*['\"]__all__['\"]")
        for file in context.python_files():
            if "serializer" not in file.lower():
                continue
            content = context.read_file(file)
            if content is None:
                continue
            for line_number, line in enumerate(content.splitlines(), start=1):
                if pattern.search(line):
                    diagnostics.append(
                        self.diagnostic(
                            message='Serializer uses fields = "__all__".',
                            file=file,
                            line=line_number,
                            recommendation=(
                                "Explicitly list serializer fields to avoid exposing "
                                "sensitive model fields."
                            ),
                            why=(
                                "New model fields may become API-visible without an "
                                "intentional serializer change."
                            ),
                            confidence="high",
                        )
                    )
        return diagnostics
