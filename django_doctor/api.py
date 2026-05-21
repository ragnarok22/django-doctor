from __future__ import annotations

from pathlib import Path

from django_doctor.core.config import load_config
from django_doctor.core.diagnostics import DoctorResult, ScanMode
from django_doctor.core.scanner import run_scan


def diagnose(
    path: str = ".",
    verbose: bool = False,
    mode: ScanMode = "full",
    base: str | None = None,
    staged: bool = False,
    categories: list[str] | None = None,
    ignored_rules: list[str] | None = None,
) -> DoctorResult:
    root = Path(path)
    config = load_config(root)
    config.verbose = verbose
    selected_mode: ScanMode = "staged" if staged else mode
    return run_scan(
        root=root,
        config=config,
        mode=selected_mode,
        base=base,
        categories=categories,
        ignored_rules=ignored_rules,
    )
