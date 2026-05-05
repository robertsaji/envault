"""Integration tests for the diff feature (parse -> diff -> format pipeline)."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.diff import diff_env_files, diff_env_texts, format_diff


BASE = """
# App config v1
APP_ENV=production
DB_URL=postgres://user:pass@localhost/db
SECRET_KEY=supersecret
FEATURE_X=false
"""

UPDATED = """
# App config v2
APP_ENV=production
DB_URL=postgres://user:newpass@prod-db/db
SECRET_KEY=supersecret
FEATURE_X=true
NEW_RELIC_KEY=abc
"""


def test_full_diff_pipeline():
    diff = diff_env_texts(BASE, UPDATED)

    assert "NEW_RELIC_KEY" in diff.added
    assert "DB_URL" in diff.changed
    assert "FEATURE_X" in diff.changed
    assert "APP_ENV" not in diff.changed
    assert "SECRET_KEY" not in diff.changed
    assert diff.removed == {}
    assert not diff.is_empty


def test_format_diff_line_count():
    diff = diff_env_texts(BASE, UPDATED)
    lines = format_diff(diff, redact=True)
    # 1 added + 2 changed = 3 lines
    assert len(lines) == 3


def test_roundtrip_with_files(tmp_path):
    old_file = tmp_path / ".env.old"
    new_file = tmp_path / ".env.new"
    old_file.write_text(BASE)
    new_file.write_text(UPDATED)

    diff = diff_env_files(old_file, new_file)
    lines = format_diff(diff, redact=False)

    assert any("NEW_RELIC_KEY" in l for l in lines)
    assert any("FEATURE_X" in l for l in lines)


def test_identical_files_produce_empty_diff(tmp_path):
    f = tmp_path / ".env"
    f.write_text(BASE)
    diff = diff_env_files(f, f)
    assert diff.is_empty
    assert format_diff(diff) == []


def test_completely_replaced_env():
    old = "A=1\nB=2\nC=3"
    new = "D=4\nE=5"
    diff = diff_env_texts(old, new)
    assert set(diff.added.keys()) == {"D", "E"}
    assert set(diff.removed.keys()) == {"A", "B", "C"}
    assert diff.changed == {}
