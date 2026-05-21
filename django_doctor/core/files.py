from __future__ import annotations

import fnmatch
import os
from pathlib import Path

RELEVANT_SUFFIXES = {".py", ".html", ".jinja", ".jinja2", ".toml", ".txt"}
RELEVANT_NAMES = {"requirements.txt", ".env.example"}


def discover_files(root: Path, excludes: list[str]) -> list[str]:
    root = root.resolve()
    selected: list[str] = []
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if not _is_excluded(_relative(current_path / dirname, root), excludes)
            and not (current_path / dirname).is_symlink()
        ]
        for filename in filenames:
            path = current_path / filename
            if path.is_symlink() or not path.is_file():
                continue
            relative = _relative(path, root)
            if _is_excluded(relative, excludes) or not is_relevant_file(relative):
                continue
            if not looks_text(path):
                continue
            selected.append(relative)
    return sorted(selected)


def filter_selected_files(root: Path, files: list[str], excludes: list[str]) -> list[str]:
    root = root.resolve()
    selected: list[str] = []
    for file in files:
        relative = file.replace("\\", "/")
        path = root / relative
        if not path.exists() or not path.is_file() or path.is_symlink():
            continue
        if _is_excluded(relative, excludes) or not is_relevant_file(relative):
            continue
        if not looks_text(path):
            continue
        selected.append(relative)
    return sorted(set(selected))


def is_relevant_file(relative_path: str) -> bool:
    path = Path(relative_path)
    return path.name in RELEVANT_NAMES or path.suffix in RELEVANT_SUFFIXES


def looks_text(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:2048]
    except OSError:
        return False
    return b"\0" not in chunk


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_excluded(relative_path: str, excludes: list[str]) -> bool:
    parts = relative_path.split("/")
    for pattern in excludes:
        clean = pattern.strip("/")
        if not clean:
            continue
        if clean in parts:
            return True
        if fnmatch.fnmatch(relative_path, clean) or fnmatch.fnmatch(
            relative_path, clean.rstrip("/")
        ):
            return True
    return False
