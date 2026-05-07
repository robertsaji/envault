"""Unit tests for envault.export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.export import ExportError, export_env

_SAMPLE = """
# database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME="mydb"
DB_PASS='s3cr3t'

# blank lines ignored
API_KEY=abc123
"""


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(_SAMPLE, encoding="utf-8")
    return p


class TestExportShell:
    def test_default_includes_export_keyword(self, env_file: Path) -> None:
        result = export_env(env_file, fmt="shell")
        assert "export DB_HOST=" in result
        assert "export API_KEY=" in result

    def test_no_export_keyword(self, env_file: Path) -> None:
        result = export_env(env_file, fmt="shell", export_keyword=False)
        assert not any(line.startswith("export ") for line in result.splitlines())

    def test_values_are_shell_quoted(self, env_file: Path) -> None:
        result = export_env(env_file, fmt="shell")
        # shlex.quote wraps values with spaces/special chars
        assert "DB_PASS=" in result

    def test_comments_excluded(self, env_file: Path) -> None:
        result = export_env(env_file, fmt="shell")
        assert "database settings" not in result


class TestExportJSON:
    def test_returns_valid_json(self, env_file: Path) -> None:
        result = export_env(env_file, fmt="json")
        data = json.loads(result)
        assert data["DB_HOST"] == "localhost"
        assert data["DB_PORT"] == "5432"
        assert data["DB_NAME"] == "mydb"
        assert data["DB_PASS"] == "s3cr3t"

    def test_api_key_present(self, env_file: Path) -> None:
        data = json.loads(export_env(env_file, fmt="json"))
        assert data["API_KEY"] == "abc123"


class TestExportDocker:
    def test_no_quotes_in_output(self, env_file: Path) -> None:
        result = export_env(env_file, fmt="docker")
        for line in result.splitlines():
            assert not line.startswith("export ")
            assert '"' not in line

    def test_key_value_format(self, env_file: Path) -> None:
        result = export_env(env_file, fmt="docker")
        assert "DB_HOST=localhost" in result


def test_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(ExportError, match="not found"):
        export_env(tmp_path / "nonexistent.env")


def test_raises_on_unknown_format(env_file: Path) -> None:
    with pytest.raises(ExportError, match="Unknown export format"):
        export_env(env_file, fmt="xml")  # type: ignore[arg-type]
