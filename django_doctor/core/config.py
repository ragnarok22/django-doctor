from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

DEFAULT_EXCLUDES = [
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "staticfiles",
    "media",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
]

VALID_CATEGORIES = {
    "security",
    "settings",
    "database",
    "migrations",
    "performance",
    "drf",
    "architecture",
    "testing",
    "templates",
    "admin",
    "dependencies",
}


class ConfigError(Exception):
    """Raised when configuration cannot be loaded."""


class DoctorConfig(BaseModel):
    diff: str | bool | None = None
    verbose: bool = False
    fail_on: Literal["error", "warning", "none"] = "none"
    exclude: list[str] = Field(default_factory=lambda: list(DEFAULT_EXCLUDES))
    ignore: list[str] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)


def load_config(root: Path, config_file: Path | None = None) -> DoctorConfig:
    root = root.resolve()
    if config_file is not None:
        path = config_file if config_file.is_absolute() else root / config_file
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
        return _load_config_file(path)

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        data = _read_toml(pyproject)
        section = data.get("tool", {}).get("django-doctor")
        if section is not None:
            return _config_from_mapping(section)

    json_config = root / "django-doctor.config.json"
    if json_config.exists():
        return _load_json_config(json_config)

    return DoctorConfig()


def project_name_from_pyproject(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return None
    data = _read_toml(pyproject)
    name = data.get("project", {}).get("name")
    return name if isinstance(name, str) else None


def _load_config_file(path: Path) -> DoctorConfig:
    if path.suffix == ".toml":
        data = _read_toml(path)
        section = data.get("tool", {}).get("django-doctor", data)
        return _config_from_mapping(section)
    if path.suffix == ".json":
        return _load_json_config(path)
    raise ConfigError("Config files must be .toml or .json")


def _load_json_config(path: Path) -> DoctorConfig:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON config: {exc}") from exc
    return _config_from_mapping(data)


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            return tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML config: {exc}") from exc


def _config_from_mapping(data: Any) -> DoctorConfig:
    if not isinstance(data, dict):
        raise ConfigError("Django Doctor config must be a table/object")
    raw = dict(data)
    raw["exclude"] = _merge_excludes(raw.get("exclude"))
    return DoctorConfig.model_validate(raw)


def _merge_excludes(configured: Any) -> list[str]:
    if configured is None:
        return list(DEFAULT_EXCLUDES)
    if not isinstance(configured, list) or not all(isinstance(item, str) for item in configured):
        raise ConfigError("exclude must be a list of strings")
    merged = list(DEFAULT_EXCLUDES)
    for item in configured:
        if item not in merged:
            merged.append(item)
    return merged
