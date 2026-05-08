"""Tests for envault.snapshot and envault.cli_snapshot."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from envault.snapshot import (
    SnapshotError,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
    save_snapshot,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ns(**kwargs):
    ns = types.SimpleNamespace(base_dir=".", **kwargs)
    return ns


# ---------------------------------------------------------------------------
# save_snapshot
# ---------------------------------------------------------------------------

class TestSaveSnapshot:
    def test_raises_when_file_missing(self, tmp_path):
        with pytest.raises(SnapshotError, match="not found"):
            save_snapshot(tmp_path / "missing.enc", tmp_path)

    def test_creates_snapshot_dir(self, tmp_path):
        enc = tmp_path / "env.enc"
        enc.write_bytes(b"data")
        save_snapshot(enc, tmp_path)
        assert (tmp_path / ".envault" / "snapshots").is_dir()

    def test_snapshot_contains_same_bytes(self, tmp_path):
        enc = tmp_path / "env.enc"
        enc.write_bytes(b"secret bytes")
        dest = save_snapshot(enc, tmp_path)
        assert dest.read_bytes() == b"secret bytes"

    def test_custom_name_used_in_filename(self, tmp_path):
        enc = tmp_path / "env.enc"
        enc.write_bytes(b"x")
        dest = save_snapshot(enc, tmp_path, name="v1.0")
        assert "v1.0" in dest.name

    def test_unsafe_chars_sanitised_in_name(self, tmp_path):
        enc = tmp_path / "env.enc"
        enc.write_bytes(b"x")
        dest = save_snapshot(enc, tmp_path, name="my snapshot/bad")
        assert "/" not in dest.name


# ---------------------------------------------------------------------------
# list_snapshots
# ---------------------------------------------------------------------------

def test_list_returns_empty_when_no_dir(tmp_path):
    assert list_snapshots(tmp_path) == []


def test_list_returns_sorted_names(tmp_path):
    enc = tmp_path / "env.enc"
    enc.write_bytes(b"x")
    save_snapshot(enc, tmp_path, name="beta")
    save_snapshot(enc, tmp_path, name="alpha")
    names = list_snapshots(tmp_path)
    assert names == sorted(names)
    assert len(names) == 2


# ---------------------------------------------------------------------------
# restore_snapshot
# ---------------------------------------------------------------------------

class TestRestoreSnapshot:
    def test_raises_when_snapshot_missing(self, tmp_path):
        with pytest.raises(SnapshotError, match="not found"):
            restore_snapshot("ghost", tmp_path, tmp_path / "out.enc")

    def test_restores_correct_bytes(self, tmp_path):
        enc = tmp_path / "env.enc"
        enc.write_bytes(b"payload")
        snap = save_snapshot(enc, tmp_path, name="snap1")
        out = tmp_path / "restored.enc"
        restore_snapshot(snap.name, tmp_path, out)
        assert out.read_bytes() == b"payload"

    def test_accepts_name_without_extension(self, tmp_path):
        enc = tmp_path / "env.enc"
        enc.write_bytes(b"hi")
        save_snapshot(enc, tmp_path, name="mysnap")
        out = tmp_path / "out.enc"
        restore_snapshot("mysnap", tmp_path, out)
        assert out.exists()


# ---------------------------------------------------------------------------
# delete_snapshot
# ---------------------------------------------------------------------------

def test_delete_removes_file(tmp_path):
    enc = tmp_path / "env.enc"
    enc.write_bytes(b"x")
    snap = save_snapshot(enc, tmp_path, name="todel")
    delete_snapshot(snap.name, tmp_path)
    assert not snap.exists()


def test_delete_raises_when_missing(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot("nope", tmp_path)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

class TestCmdSnapshotSave:
    def test_prints_success(self, tmp_path, capsys):
        from envault.cli_snapshot import cmd_snapshot_save
        enc = tmp_path / "env.enc"
        enc.write_bytes(b"x")
        cmd_snapshot_save(_ns(file=str(enc), base_dir=str(tmp_path), name=None))
        out = capsys.readouterr().out
        assert "Snapshot saved" in out

    def test_exits_on_missing_file(self, tmp_path):
        from envault.cli_snapshot import cmd_snapshot_save
        with pytest.raises(SystemExit):
            cmd_snapshot_save(_ns(file=str(tmp_path / "x.enc"), base_dir=str(tmp_path), name=None))


def test_cmd_snapshot_list_empty(tmp_path, capsys):
    from envault.cli_snapshot import cmd_snapshot_list
    cmd_snapshot_list(_ns(base_dir=str(tmp_path)))
    assert "No snapshots" in capsys.readouterr().out


def test_cmd_snapshot_delete_exits_on_missing(tmp_path):
    from envault.cli_snapshot import cmd_snapshot_delete
    with pytest.raises(SystemExit):
        cmd_snapshot_delete(_ns(snapshot="ghost", base_dir=str(tmp_path)))
