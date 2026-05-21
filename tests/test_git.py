import subprocess
from pathlib import Path

from django_doctor.core.config import DEFAULT_EXCLUDES
from django_doctor.core.git import staged_files


def test_staged_files_returns_relevant_existing_files(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    (tmp_path / "settings.py").write_text("DEBUG = True\n", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"\0binary")
    _git(tmp_path, "add", "settings.py", "image.png")

    files = staged_files(tmp_path, list(DEFAULT_EXCLUDES))

    assert files == ["settings.py"]


def _git(path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True)
