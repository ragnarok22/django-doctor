from __future__ import annotations

from pathlib import Path

from django_doctor.core.config import DoctorConfig, project_name_from_pyproject
from django_doctor.core.context import ScanContext
from django_doctor.core.diagnostics import (
    DoctorResult,
    ProjectInfo,
    ScanInfo,
    ScanMode,
    diagnostic_sort_key,
)
from django_doctor.core.files import discover_files
from django_doctor.core.git import autodetect_base, changed_files, staged_files
from django_doctor.core.scoring import calculate_score, summarize
from django_doctor.rules.registry import get_rules


def run_scan(
    root: Path,
    config: DoctorConfig,
    mode: ScanMode = "full",
    base: str | None = None,
    categories: list[str] | None = None,
    ignored_rules: list[str] | None = None,
    project_name: str | None = None,
) -> DoctorResult:
    root = root.resolve()
    ignored = set(config.ignore) | set(ignored_rules or [])
    selected_base = base

    if mode == "diff":
        if selected_base is None:
            selected_base = autodetect_base(root)
        files = changed_files(root, selected_base, config.exclude)
    elif mode == "staged":
        files = staged_files(root, config.exclude)
    else:
        files = discover_files(root, config.exclude)

    rules = [rule for rule in get_rules(categories) if rule.id not in ignored]
    context = ScanContext(root=root, files=files, config=config)
    diagnostics = []
    for rule in rules:
        diagnostics.extend(rule.check(context))
    diagnostics = [diagnostic for diagnostic in diagnostics if diagnostic.id not in ignored]
    diagnostics.sort(key=diagnostic_sort_key)

    score = calculate_score(diagnostics)
    summary = summarize(diagnostics)
    name = project_name or project_name_from_pyproject(root) or root.name

    return DoctorResult(
        ok=True,
        project=ProjectInfo(name=name, root=str(root)),
        scan=ScanInfo(
            mode=mode,
            base=selected_base if mode == "diff" else None,
            staged=mode == "staged",
            files_scanned=len(files),
            rules_enabled=len(rules),
        ),
        score=score,
        summary=summary,
        diagnostics=diagnostics,
    )
