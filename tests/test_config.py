from pathlib import Path

from django_doctor.core.config import DEFAULT_EXCLUDES, load_config, project_name_from_pyproject
from django_doctor.core.files import discover_files


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
