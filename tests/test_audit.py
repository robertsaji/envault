"""Tests for envault.audit and envault.cli_audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

from envault.audit import AuditError, _audit_path, load_events, record_event
from envault.cli_audit import cmd_audit_log


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"last": 20, "json": False, "directory": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# record_event
# ---------------------------------------------------------------------------

class TestRecordEvent:
    def test_creates_log_file(self, tmp_path):
        record_event("encrypt", ".env", directory=tmp_path)
        assert _audit_path(tmp_path).exists()

    def test_entry_contains_required_fields(self, tmp_path):
        entry = record_event("decrypt", ".env.gpg", actor="alice", directory=tmp_path)
        assert entry["action"] == "decrypt"
        assert entry["target"] == ".env.gpg"
        assert entry["actor"] == "alice"
        assert "timestamp" in entry

    def test_extra_fields_merged(self, tmp_path):
        entry = record_event("push", "remote", extra={"remote": "s3://bucket"}, directory=tmp_path)
        assert entry["remote"] == "s3://bucket"

    def test_multiple_events_appended(self, tmp_path):
        for action in ("encrypt", "push", "pull"):
            record_event(action, ".env", directory=tmp_path)
        lines = _audit_path(tmp_path).read_text().strip().splitlines()
        assert len(lines) == 3

    def test_raises_on_unwritable_path(self, tmp_path):
        ro = tmp_path / "readonly"
        ro.mkdir()
        ro.chmod(0o444)
        with pytest.raises(AuditError):
            record_event("encrypt", ".env", directory=ro)


# ---------------------------------------------------------------------------
# load_events
# ---------------------------------------------------------------------------

class TestLoadEvents:
    def test_returns_empty_when_no_file(self, tmp_path):
        assert load_events(directory=tmp_path) == []

    def test_round_trips_events(self, tmp_path):
        record_event("encrypt", ".env", actor="bob", directory=tmp_path)
        events = load_events(directory=tmp_path)
        assert len(events) == 1
        assert events[0]["actor"] == "bob"

    def test_raises_on_corrupt_line(self, tmp_path):
        _audit_path(tmp_path).write_text("not-json\n")
        with pytest.raises(AuditError, match="Corrupt"):
            load_events(directory=tmp_path)

    def test_ignores_blank_lines(self, tmp_path):
        _audit_path(tmp_path).write_text(
            json.dumps({"timestamp": "t", "action": "a", "target": "f", "actor": "x"}) + "\n\n"
        )
        assert len(load_events(directory=tmp_path)) == 1


# ---------------------------------------------------------------------------
# cmd_audit_log
# ---------------------------------------------------------------------------

class TestCmdAuditLog:
    def test_prints_no_events_message(self, tmp_path, capsys):
        cmd_audit_log(_ns(directory=str(tmp_path)))
        out = capsys.readouterr().out
        assert "No audit events" in out

    def test_prints_table_by_default(self, tmp_path, capsys):
        record_event("encrypt", ".env", actor="carol", directory=tmp_path)
        cmd_audit_log(_ns(directory=str(tmp_path)))
        out = capsys.readouterr().out
        assert "encrypt" in out
        assert "carol" in out

    def test_json_flag_outputs_valid_json(self, tmp_path, capsys):
        record_event("pull", ".env.gpg", directory=tmp_path)
        cmd_audit_log(_ns(directory=str(tmp_path), json=True))
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)

    def test_last_limits_output(self, tmp_path, capsys):
        for i in range(5):
            record_event("encrypt", f".env{i}", directory=tmp_path)
        cmd_audit_log(_ns(directory=str(tmp_path), last=2, json=True))
        data = json.loads(capsys.readouterr().out)
        assert len(data) == 2

    def test_exits_on_audit_error(self, tmp_path, capsys):
        _audit_path(tmp_path).write_text("bad\n")
        with pytest.raises(SystemExit):
            cmd_audit_log(_ns(directory=str(tmp_path)))
