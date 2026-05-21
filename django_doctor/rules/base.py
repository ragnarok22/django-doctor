from __future__ import annotations

from abc import ABC, abstractmethod

from django_doctor.core.context import ScanContext
from django_doctor.core.diagnostics import Diagnostic, Severity


class Rule(ABC):
    id: str
    title: str
    category: str
    default_severity: Severity
    tags: list[str]

    @abstractmethod
    def check(self, context: ScanContext) -> list[Diagnostic]:
        """Return diagnostics for this rule."""

    def diagnostic(
        self,
        *,
        message: str,
        file: str | None = None,
        line: int | None = None,
        column: int | None = None,
        recommendation: str | None = None,
        why: str | None = None,
        confidence: str | None = None,
    ) -> Diagnostic:
        return Diagnostic(
            id=self.id,
            title=self.title,
            severity=self.default_severity,
            category=self.category,
            message=message,
            file=file,
            line=line,
            column=column,
            recommendation=recommendation,
            why=why,
            confidence=confidence,  # type: ignore[arg-type]
            tags=self.tags,
        )
