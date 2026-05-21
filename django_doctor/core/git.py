from __future__ import annotations

import subprocess
from pathlib import Path

from django_doctor.core.files import filter_selected_files

BASE_CANDIDATES = ["main", "master", "origin/main", "origin/master"]


class GitError(Exception):
    """Raised when git file selection fails."""


def ensure_git_repo(root: Path) -> None:
    result = _run_git(root, ["rev-parse", "--is-inside-work-tree"], check=False)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise GitError("Not inside a git repository. Run a full scan or choose a git repository.")


def autodetect_base(root: Path) -> str:
    ensure_git_repo(root)
    for candidate in BASE_CANDIDATES:
        if _git_ref_exists(root, candidate):
            return candidate
    raise GitError(
        "Could not autodetect a base branch. Pass one explicitly, for example: --diff main."
    )


def changed_files(root: Path, base: str, excludes: list[str]) -> list[str]:
    ensure_git_repo(root)
    if not _git_ref_exists(root, base):
        raise GitError(f"Git base ref not found: {base}. Pass a valid branch or ref to --diff.")
    result = _run_git(root, ["diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD"])
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return filter_selected_files(root, files, excludes)


def staged_files(root: Path, excludes: list[str]) -> list[str]:
    ensure_git_repo(root)
    result = _run_git(root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return filter_selected_files(root, files, excludes)


def _git_ref_exists(root: Path, ref: str) -> bool:
    result = _run_git(root, ["rev-parse", "--verify", "--quiet", ref], check=False)
    return result.returncode == 0


def _run_git(root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise GitError(message)
    return result
