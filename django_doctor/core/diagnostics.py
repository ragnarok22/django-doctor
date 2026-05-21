from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["error", "warning", "info"]
Confidence = Literal["low", "medium", "high"]
ScanMode = Literal["full", "diff", "staged"]
ScoreLabel = Literal["excellent", "good", "needs_work", "critical"]


class Diagnostic(BaseModel):
    id: str
    title: str
    severity: Severity
    category: str
    message: str
    file: str | None = None
    line: int | None = None
    column: int | None = None
    recommendation: str | None = None
    why: str | None = None
    confidence: Confidence | None = None
    tags: list[str] = Field(default_factory=list)


class ProjectInfo(BaseModel):
    name: str
    root: str
    framework: str = "django"
    django_version: str | None = None


class ScanInfo(BaseModel):
    mode: ScanMode
    base: str | None = None
    staged: bool = False
    files_scanned: int
    rules_enabled: int


class Score(BaseModel):
    value: int
    label: ScoreLabel


class DoctorResult(BaseModel):
    ok: bool
    project: ProjectInfo
    scan: ScanInfo
    score: Score
    summary: dict[str, int]
    diagnostics: list[Diagnostic]


def diagnostic_sort_key(diagnostic: Diagnostic) -> tuple[int, str, str, int, str]:
    severity_order = {"error": 0, "warning": 1, "info": 2}
    return (
        severity_order[diagnostic.severity],
        diagnostic.category,
        diagnostic.file or "",
        diagnostic.line or 0,
        diagnostic.id,
    )
