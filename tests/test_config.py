from pathlib import Path

import pytest

from django_doctor.core.config import (
    DEFAULT_EXCLUDES,
    ConfigError,
    DoctorConfig,
    load_config,
    project_name_from_pyproject,
)
from django_doctor.core.context import ScanContext
from django_doctor.core.files import (
    discover_files,
    filter_selected_files,
    is_relevant_file,
    looks_text,
)


def test_config_loads_from_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "example-project"

[tool.django-doctor]
diff = "main"
fail_on = "error"
exclude = ["*/migrations/*"]
ignore = ["django/architecture/large-file"]

[tool.django-doctor.rules]
max_views_file_lines = 10
""".strip(),
        encoding="utf-8",
    )

    config = load_config(tmp_path)

    assert config.diff == "main"
    assert config.fail_on == "error"
    assert "*/migrations/*" in config.exclude
    assert ".git" in config.exclude
    assert config.ignore == ["django/architecture/large-file"]
    assert config.rules["max_views_file_lines"] == 10
    assert project_name_from_pyproject(tmp_path) == "example-project"


def test_default_excludes_are_respected(tmp_path: Path) -> None:
    excluded = tmp_path / ".venv"
    excluded.mkdir()
    (excluded / "settings.py").write_text("DEBUG = True\n", encoding="utf-8")
    (tmp_path / "settings.py").write_text("DEBUG = False\n", encoding="utf-8")

    files = discover_files(tmp_path, list(DEFAULT_EXCLUDES))

    assert "settings.py" in files
    assert ".venv/settings.py" not in files


def test_config_loads_from_json_fallback(tmp_path: Path) -> None:
    (tmp_path / "django-doctor.config.json").write_text(
        '{"fail_on": "warning", "exclude": ["custom"]}',
        encoding="utf-8",
    )

    config = load_config(tmp_path)

    assert config.fail_on == "warning"
    assert "custom" in config.exclude


def test_explicit_toml_config_can_be_plain_object(tmp_path: Path) -> None:
    (tmp_path / "doctor.toml").write_text('fail_on = "warning"\n', encoding="utf-8")

    config = load_config(tmp_path, Path("doctor.toml"))

    assert config.fail_on == "warning"


def test_explicit_config_file_errors(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Config file not found"):
        load_config(tmp_path, Path("missing.toml"))

    (tmp_path / "config.yaml").write_text("fail_on: error", encoding="utf-8")
    with pytest.raises(ConfigError, match="must be .toml or .json"):
        load_config(tmp_path, Path("config.yaml"))


def test_invalid_config_errors(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid JSON"):
        load_config(tmp_path, Path("bad.json"))

    (tmp_path / "bad.toml").write_text("[tool.django-doctor", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_config(tmp_path, Path("bad.toml"))

    (tmp_path / "not-object.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ConfigError, match="table/object"):
        load_config(tmp_path, Path("not-object.json"))

    (tmp_path / "bad-exclude.json").write_text('{"exclude": "venv"}', encoding="utf-8")
    with pytest.raises(ConfigError, match="exclude must be"):
        load_config(tmp_path, Path("bad-exclude.json"))


def test_file_filtering_handles_irrelevant_binary_missing_and_duplicates(tmp_path: Path) -> None:
    (tmp_path / "settings.py").write_text("DEBUG = False\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("ignore me\n", encoding="utf-8")
    (tmp_path / "binary.py").write_bytes(b"abc\0def")
    (tmp_path / "requirements.txt").write_text("django\n", encoding="utf-8")

    files = filter_selected_files(
        tmp_path,
        ["settings.py", "settings.py", "notes.md", "binary.py", "missing.py", "requirements.txt"],
        [],
    )

    assert files == ["requirements.txt", "settings.py"]
    assert is_relevant_file(".env.example")
    assert not is_relevant_file("README.md")
    assert not looks_text(tmp_path / "missing.py")


def test_discover_files_skips_symlink_and_binary_files(tmp_path: Path) -> None:
    (tmp_path / "settings.py").write_text("DEBUG = False\n", encoding="utf-8")
    (tmp_path / "binary.py").write_bytes(b"abc\0def")
    (tmp_path / "linked.py").symlink_to(tmp_path / "settings.py")

    files = discover_files(tmp_path, [])

    assert files == ["settings.py"]


def test_scan_context_helpers_handle_read_errors_and_file_categories(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings.py").write_text("DEBUG = False\n", encoding="utf-8")
    (tmp_path / "template.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "bad.py").write_bytes(b"\xff")
    context = ScanContext(
        root=tmp_path,
        files=["config/settings.py", "template.html", ".env.example"],
        config=DoctorConfig(rules={"answer": 42}),
    )

    assert context.read_file("bad.py") is None
    assert context.python_files() == ["config/settings.py"]
    assert context.django_like_files() == ["config/settings.py", "template.html", ".env.example"]
    assert context.settings_files() == ["config/settings.py"]
    assert context.rule_setting("answer", 0) == 42
    assert context.rule_setting("missing", "default") == "default"
