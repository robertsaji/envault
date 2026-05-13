"""Unit tests for envault.watch."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.watch import watch, WatchError, _mtime


# ---------------------------------------------------------------------------
# _mtime
# ---------------------------------------------------------------------------

def test_mtime_returns_negative_one_when_missing(tmp_path):
    assert _mtime(tmp_path / "ghost.env") == -1.0


def test_mtime_returns_float_for_existing_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("KEY=val")
    assert _mtime(f) > 0


# ---------------------------------------------------------------------------
# watch — error cases
# ---------------------------------------------------------------------------

def test_raises_when_source_missing(tmp_path):
    with pytest.raises(WatchError, match="Source file not found"):
        watch(tmp_path / "missing.env", lambda p: None, max_iterations=1)


# ---------------------------------------------------------------------------
# watch — change detection
# ---------------------------------------------------------------------------

def test_calls_on_change_when_mtime_differs(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1")

    calls = []
    mtimes = [1000.0, 1001.0]  # second poll has a newer mtime

    with patch("envault.watch.time.sleep"), \
         patch("envault.watch._mtime", side_effect=[1000.0] + mtimes):
        watch(env, calls.append, interval=0, max_iterations=2)

    assert len(calls) == 1
    assert calls[0] == env


def test_no_callback_when_mtime_unchanged(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1")

    calls = []
    with patch("envault.watch.time.sleep"), \
         patch("envault.watch._mtime", return_value=999.0):
        watch(env, calls.append, interval=0, max_iterations=3)

    assert calls == []


def test_stops_after_max_iterations(tmp_path):
    env = tmp_path / ".env"
    env.write_text("KEY=val")

    sleep_calls = []
    with patch("envault.watch.time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        watch(env, lambda p: None, interval=0.5, max_iterations=4)

    assert len(sleep_calls) == 4


def test_multiple_changes_trigger_multiple_callbacks(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1")

    calls = []
    # alternating mtime so every poll looks changed
    side = [100.0, 101.0, 100.0, 101.0, 100.0]

    with patch("envault.watch.time.sleep"), \
         patch("envault.watch._mtime", side_effect=side):
        watch(env, calls.append, interval=0, max_iterations=4)

    assert len(calls) == 4
