from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from django_doctor.api import diagnose
from django_doctor.cli import app, install_command

runner = CliRunner()


def test_cli_default_scan_works(tmp_path: Path) -> None:
    _write_settings(tmp_path, "DEBUG = False\n")

    result = runner.invoke(app, [str(tmp_path)])

    assert result.exit_code == 0
    assert "Django Doctor Report" in result.stdout
    assert "Score:" in result.stdout


def test_json_returns_valid_json(tmp_path: Path) -> None:
    _write_settings(tmp_path, "DEBUG = True\n")

    result = runner.invoke(app, [str(tmp_path), "--json"])

    data = json.loads(result.stdout)

    assert result.exit_code == 0
    assert data["ok"] is True
    assert data["summary"]["error"] == 1


def test_json_compact_returns_valid_json_without_pretty_indentation(tmp_path: Path) -> None:
    _write_settings(tmp_path, "DEBUG = False\n")

    result = runner.invoke(app, [str(tmp_path), "--json-compact"])

    data = json.loads(result.stdout)

    assert result.exit_code == 0
    assert data["ok"] is True
    assert "\n  " not in result.stdout


def test_score_prints_only_integer(tmp_path: Path) -> None:
    _write_settings(tmp_path, "DEBUG = False\n")

    result = runner.invoke(app, [str(tmp_path), "--score"])

    assert result.exit_code == 0
    assert result.stdout.strip().isdigit()


def test_verbose_output_groups_diagnostics_with_color(tmp_path: Path) -> None:
    _write_settings(tmp_path, "DEBUG = True\n")
    (tmp_path / "config" / "production_settings.py").write_text(
        "DEBUG = True\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, [str(tmp_path), "--verbose"])

    assert result.exit_code == 0
    assert "\x1b[32m✓\x1b[0m Running django-doctor checks." in result.stdout
    assert "django/security/debug-true" in result.stdout
    assert "×2" in result.stdout
    assert "→ Use an environment variable and default DEBUG to False." in result.stdout
    assert "config/settings.py:1" in result.stdout
    assert "config/production_settings.py:1" in result.stdout


def test_diff_and_staged_conflict(tmp_path: Path) -> None:
    result = runner.invoke(app, [str(tmp_path), "--diff", "main", "--staged"])

    assert result.exit_code == 2
    assert "--diff and --staged" in result.stderr


def test_full_and_diff_conflict(tmp_path: Path) -> None:
    result = runner.invoke(app, [str(tmp_path), "--full", "--diff", "main"])

    assert result.exit_code == 2
    assert "--full and --diff" in result.stderr


def test_fail_on_error_exits_one_when_error_diagnostic_exists(tmp_path: Path) -> None:
    _write_settings(tmp_path, "DEBUG = True\n")

    result = runner.invoke(app, [str(tmp_path), "--fail-on", "error"])

    assert result.exit_code == 1


def test_fail_on_none_exits_zero_even_with_diagnostics(tmp_path: Path) -> None:
    _write_settings(tmp_path, "DEBUG = True\n")

    result = runner.invoke(app, [str(tmp_path), "--fail-on", "none"])

    assert result.exit_code == 0


def test_ignore_suppresses_rule_diagnostics(tmp_path: Path) -> None:
    _write_settings(tmp_path, "DEBUG = True\n")

    result = runner.invoke(
        app,
        [str(tmp_path), "--json", "--ignore", "django/security/debug-true"],
    )
    data = json.loads(result.stdout)

    assert data["summary"]["error"] == 0
    assert data["diagnostics"] == []


def test_annotations_with_json_write_annotations_to_stderr(tmp_path: Path) -> None:
    _write_settings(tmp_path, "DEBUG = True\n")

    result = runner.invoke(app, [str(tmp_path), "--json", "--annotations"])
    data = json.loads(result.stdout)

    assert result.exit_code == 0
    assert data["summary"]["error"] == 1
    assert "::error" in result.stderr
    assert "::error" not in result.stdout


def test_debug_true_rule_detects_debug_true(tmp_path: Path) -> None:
    _write_settings(tmp_path, "DEBUG = True\n")

    result = diagnose(path=str(tmp_path), categories=["security"])

    assert [diagnostic.id for diagnostic in result.diagnostics] == ["django/security/debug-true"]


def test_secret_key_rule_does_not_flag_os_environ(tmp_path: Path) -> None:
    _write_settings(tmp_path, "import os\nSECRET_KEY = os.environ['SECRET_KEY']\n")

    result = diagnose(path=str(tmp_path), categories=["security"])

    ids = [diagnostic.id for diagnostic in result.diagnostics]

    assert "django/security/secret-key-hardcoded" not in ids


def test_serializer_fields_all_rule_detects_all_fields(tmp_path: Path) -> None:
    serializers = tmp_path / "users" / "serializers.py"
    serializers.parent.mkdir()
    serializers.write_text(
        """
class UserSerializer:
    class Meta:
        fields = "__all__"
""".strip(),
        encoding="utf-8",
    )

    result = diagnose(path=str(tmp_path), categories=["drf"])

    assert [diagnostic.id for diagnostic in result.diagnostics] == [
        "django/drf/serializer-fields-all"
    ]


def test_allow_any_permission_rule_detects_permission_classes(tmp_path: Path) -> None:
    views = tmp_path / "users" / "views.py"
    views.parent.mkdir()
    views.write_text(
        """
from rest_framework.permissions import AllowAny

class UserView:
    permission_classes = [AllowAny]
""".strip(),
        encoding="utf-8",
    )

    result = diagnose(path=str(tmp_path), categories=["drf"])

    assert [diagnostic.id for diagnostic in result.diagnostics] == [
        "django/drf/allow-any-permission"
    ]


def test_install_command_creates_files(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.chdir(tmp_path)

    assert install_command() == 0

    assert (tmp_path / ".django-doctor" / "AGENTS.md").exists()
    assert (tmp_path / ".django-doctor" / "rules.md").exists()
    assert (tmp_path / ".django-doctor" / "usage.md").exists()


def _write_settings(tmp_path: Path, content: str) -> None:
    settings = tmp_path / "config" / "settings.py"
    settings.parent.mkdir()
    settings.write_text(content, encoding="utf-8")
