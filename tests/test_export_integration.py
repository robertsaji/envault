"""Integration tests for the full export pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.export import export_env

_COMPLEX_ENV = """
# Production config
APP_ENV=production
SECRET_KEY="p@ss w0rd!"
EMPTY_VAL=
NUMERIC=42
QUOTED_SINGLE='hello world'
NO_SPACE=simple
"""


@pytest.fixture()
def complex_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env.production"
    p.write_text(_COMPLEX_ENV, encoding="utf-8")
    return p


def test_shell_and_json_contain_same_keys(complex_env: Path) -> None:
    shell = export_env(complex_env, fmt="shell")
    data = json.loads(export_env(complex_env, fmt="json"))
    shell_keys = {line.split("=")[0].replace("export ", "") for line in shell.splitlines()}
    assert shell_keys == set(data.keys())


def test_json_preserves_values(complex_env: Path) -> None:
    data = json.loads(export_env(complex_env, fmt="json"))
    assert data["APP_ENV"] == "production"
    assert data["NUMERIC"] == "42"
    assert data["SECRET_KEY"] == "p@ss w0rd!"
    assert data["QUOTED_SINGLE"] == "hello world"


def test_docker_format_one_line_per_key(complex_env: Path) -> None:
    result = export_env(complex_env, fmt="docker")
    lines = [l for l in result.splitlines() if l.strip()]
    keys = [l.split("=")[0] for l in lines]
    assert "APP_ENV" in keys
    assert "SECRET_KEY" in keys
    # each line must have exactly one '=' separator
    for line in lines:
        assert "=" in line


def test_roundtrip_shell_sourcing(complex_env: Path) -> None:
    """Shell output should be parseable back to the same key set."""
    shell = export_env(complex_env, fmt="shell", export_keyword=False)
    recovered: dict = {}
    for line in shell.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            recovered[k.strip()] = v.strip().strip("'")
    data = json.loads(export_env(complex_env, fmt="json"))
    assert set(recovered.keys()) == set(data.keys())


def test_empty_env_file(tmp_path: Path) -> None:
    empty = tmp_path / ".env"
    empty.write_text("# only comments\n\n", encoding="utf-8")
    assert export_env(empty, fmt="shell") == ""
    assert json.loads(export_env(empty, fmt="json")) == {}
    assert export_env(empty, fmt="docker") == ""
