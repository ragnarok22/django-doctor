import subprocess
from pathlib import Path

import pytest

from django_doctor.core.config import DEFAULT_EXCLUDES
from django_doctor.core.git import (
    GitError,
    _run_git,
    autodetect_base,
    changed_files,
    ensure_git_repo,
    staged_files,
)


def test_staged_files_returns_relevant_existing_files(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    (tmp_path / "settings.py").write_text("DEBUG = True\n", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"\0binary")
    _git(tmp_path, "add", "settings.py", "image.png")

    files = staged_files(tmp_path, list(DEFAULT_EXCLUDES))

    assert files == ["settings.py"]


def test_changed_files_returns_relevant_files_against_base(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "settings.py").write_text("DEBUG = False\n", encoding="utf-8")
    _git(tmp_path, "add", "settings.py")
    _git(tmp_path, "commit", "-m", "initial")
    _git(tmp_path, "checkout", "-b", "feature")

    (tmp_path / "settings.py").write_text("DEBUG = True\n", encoding="utf-8")
    (tmp_path / "ignored.png").write_bytes(b"not relevant")
    _git(tmp_path, "add", "settings.py", "ignored.png")
    _git(tmp_path, "commit", "-m", "change settings")

    assert autodetect_base(tmp_path) == "main"
    assert changed_files(tmp_path, "main", list(DEFAULT_EXCLUDES)) == ["settings.py"]


def test_git_errors_for_non_repo_and_missing_base(tmp_path: Path) -> None:
    with pytest.raises(GitError, match="Not inside a git repository"):
        ensure_git_repo(tmp_path)

    _git(tmp_path, "init")
    with pytest.raises(GitError, match="base branch"):
        autodetect_base(tmp_path)
    with pytest.raises(GitError, match="Git base ref not found"):
        changed_files(tmp_path, "missing", list(DEFAULT_EXCLUDES))


def test_run_git_raises_git_error_with_command_message(tmp_path: Path) -> None:
    with pytest.raises(GitError, match="not-a-real-git-command"):
        _run_git(tmp_path, ["not-a-real-git-command"])


def _git(path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True)
