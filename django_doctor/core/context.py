from __future__ import annotations

from pathlib import Path

from django_doctor.core.config import DoctorConfig


class ScanContext:
    def __init__(self, root: Path, files: list[str], config: DoctorConfig) -> None:
        self.root = root.resolve()
        self.files = files
        self.config = config

    def read_file(self, relative_path: str) -> str | None:
        try:
            return (self.root / relative_path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return None
        except OSError:
            return None

    def python_files(self) -> list[str]:
        return [file for file in self.files if file.endswith(".py")]

    def django_like_files(self) -> list[str]:
        suffixes = (".py", ".html", ".jinja", ".jinja2", ".toml", ".txt")
        return [file for file in self.files if file.endswith(suffixes) or file == ".env.example"]

    def settings_files(self) -> list[str]:
        return [
            file
            for file in self.python_files()
            if "settings" in Path(file).stem.lower() or "/settings/" in file.lower()
        ]

    def rule_setting(self, key: str, default: object) -> object:
        return self.config.rules.get(key, default)
