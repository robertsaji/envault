"""Unit tests for envault.diff."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.diff import (
    DiffError,
    EnvDiff,
    _parse_env,
    diff_env_texts,
    diff_env_files,
    format_diff,
)


OLD_ENV = """
# database config
DB_HOST=localhost
DB_PORT=5432
DB_PASS=secret
DEBUG=true
"""

NEW_ENV = """
DB_HOST=prod.db.example.com
DB_PORT=5432
DB_PASS=newsecret
API_KEY=abc123
"""


class TestParseEnv:
    def test_parses_simple_pairs(self):
        result = _parse_env("FOO=bar\nBAZ=qux")
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_ignores_comments(self):
        result = _parse_env("# comment\nFOO=bar")
        assert "FOO" in result
        assert len(result) == 1

    def test_ignores_blank_lines(self):
        result = _parse_env("\n\nFOO=bar\n\n")
        assert result == {"FOO": "bar"}

    def test_strips_double_quotes(self):
        result = _parse_env('FOO="hello world"')
        assert result["FOO"] == "hello world"

    def test_strips_single_quotes(self):
        result = _parse_env("FOO='hello'")
        assert result["FOO"] == "hello"


class TestDiffEnvTexts:
    def test_detects_added_keys(self):
        diff = diff_env_texts(OLD_ENV, NEW_ENV)
        assert "API_KEY" in diff.added

    def test_detects_removed_keys(self):
        diff = diff_env_texts(OLD_ENV, NEW_ENV)
        assert "DEBUG" in diff.removed

    def test_detects_changed_keys(self):
        diff = diff_env_texts(OLD_ENV, NEW_ENV)
        assert "DB_HOST" in diff.changed
        assert "DB_PASS" in diff.changed

    def test_unchanged_keys_absent(self):
        diff = diff_env_texts(OLD_ENV, NEW_ENV)
        assert "DB_PORT" not in diff.added
        assert "DB_PORT" not in diff.removed
        assert "DB_PORT" not in diff.changed

    def test_empty_diff_when_identical(self):
        diff = diff_env_texts(OLD_ENV, OLD_ENV)
        assert diff.is_empty


def test_diff_env_files_raises_when_missing(tmp_path):
    with pytest.raises(DiffError, match="not found"):
        diff_env_files(tmp_path / "missing.env", tmp_path / "also_missing.env")


def test_diff_env_files_reads_from_disk(tmp_path):
    old = tmp_path / "old.env"
    new = tmp_path / "new.env"
    old.write_text("FOO=1")
    new.write_text("FOO=2")
    diff = diff_env_files(old, new)
    assert "FOO" in diff.changed


class TestFormatDiff:
    def test_redacts_values_by_default(self):
        diff = diff_env_texts(OLD_ENV, NEW_ENV)
        lines = format_diff(diff, redact=True)
        assert all("<redacted>" in l for l in lines)

    def test_shows_values_when_not_redacted(self):
        diff = diff_env_texts(OLD_ENV, NEW_ENV)
        lines = format_diff(diff, redact=False)
        assert any("prod.db.example.com" in l for l in lines)

    def test_prefix_symbols(self):
        diff = diff_env_texts(OLD_ENV, NEW_ENV)
        lines = format_diff(diff, redact=True)
        prefixes = {l[0] for l in lines}
        assert prefixes <= {"+", "-", "~"}
