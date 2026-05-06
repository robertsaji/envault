"""Unit tests for envault.cli_diff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.cli_diff import cmd_diff, register_diff_subcommands
from envault.diff import EnvDiff


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"old": "old.env", "new": "new.env", "show_values": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdDiff:
    def test_prints_no_differences_when_empty(self, tmp_path, capsys):
        p = tmp_path / "a.env"
        p.write_text("FOO=bar")
        args = _ns(old=str(p), new=str(p))
        cmd_diff(args)
        out = capsys.readouterr().out
        assert "No differences" in out

    def test_prints_summary_on_diff(self, tmp_path, capsys):
        old = tmp_path / "old.env"
        new = tmp_path / "new.env"
        old.write_text("FOO=1\nBAR=old")
        new.write_text("FOO=1\nBAR=new\nBAZ=added")
        args = _ns(old=str(old), new=str(new))
        cmd_diff(args)
        out = capsys.readouterr().out
        assert "+1 added" in out
        assert "~1 changed" in out

    def test_redacts_by_default(self, tmp_path, capsys):
        old = tmp_path / "old.env"
        new = tmp_path / "new.env"
        old.write_text("SECRET=old_value")
        new.write_text("SECRET=new_value")
        args = _ns(old=str(old), new=str(new), show_values=False)
        cmd_diff(args)
        out = capsys.readouterr().out
        assert "old_value" not in out
        assert "new_value" not in out
        assert "<redacted>" in out

    def test_shows_values_with_flag(self, tmp_path, capsys):
        old = tmp_path / "old.env"
        new = tmp_path / "new.env"
        old.write_text("SECRET=old_value")
        new.write_text("SECRET=new_value")
        args = _ns(old=str(old), new=str(new), show_values=True)
        cmd_diff(args)
        out = capsys.readouterr().out
        assert "old_value" in out

    def test_exits_on_missing_file(self, tmp_path):
        args = _ns(old=str(tmp_path / "ghost.env"), new=str(tmp_path / "ghost2.env"))
        with pytest.raises(SystemExit) as exc_info:
            cmd_diff(args)
        assert exc_info.value.code == 1

    def test_exits_on_missing_old_file_only(self, tmp_path):
        """Ensure exit code 1 is raised when only the old file is missing."""
        new = tmp_path / "new.env"
        new.write_text("FOO=bar")
        args = _ns(old=str(tmp_path / "ghost.env"), new=str(new))
        with pytest.raises(SystemExit) as exc_info:
            cmd_diff(args)
        assert exc_info.value.code == 1

    def test_exits_on_missing_new_file_only(self, tmp_path):
        """Ensure exit code 1 is raised when only the new file is missing."""
        old = tmp_path / "old.env"
        old.write_text("FOO=bar")
        args = _ns(old=str(old), new=str(tmp_path / "ghost.env"))
        with pytest.raises(SystemExit) as exc_info:
            cmd_diff(args)
        assert exc_info.value.code == 1


def test_register_diff_subcommands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_diff_subcommands(sub)
    args = parser.parse_args(["diff", "old.env", "new.env"])
    assert args.old == "old.env"
    assert args.new == "new.env"
    assert args.show_values is False
