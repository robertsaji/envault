"""Unit tests for envault.cli_rotate."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.cli_rotate import cmd_rotate, register_rotate_subcommands
from envault.rotate import RotateError


def _ns(**kwargs):
    defaults = {"file": ".env.gpg", "recipients": ["AAAA1111"]}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdRotate:
    def test_rotate_success(self, tmp_path, capsys):
        out_path = tmp_path / ".env.gpg"
        with patch("envault.cli_rotate.rotate", return_value=out_path) as mock_rot, \
             patch("envault.cli_rotate.record_event"):
            cmd_rotate(_ns(file=str(out_path)))
        mock_rot.assert_called_once()
        captured = capsys.readouterr()
        assert "Rotated" in captured.out

    def test_rotate_records_audit_event(self, tmp_path):
        out_path = tmp_path / ".env.gpg"
        with patch("envault.cli_rotate.rotate", return_value=out_path), \
             patch("envault.cli_rotate.record_event") as mock_rec:
            cmd_rotate(_ns(file=str(out_path)))
        mock_rec.assert_called_once()
        call_kwargs = mock_rec.call_args
        assert call_kwargs[0][0] == "rotate"

    def test_exits_on_empty_recipients(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            cmd_rotate(_ns(recipients=[]))
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "recipient" in captured.err

    def test_exits_on_rotate_error(self, capsys):
        with patch("envault.cli_rotate.rotate", side_effect=RotateError("boom")), \
             pytest.raises(SystemExit) as exc_info:
            cmd_rotate(_ns())
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "boom" in captured.err


def test_register_rotate_subcommands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_rotate_subcommands(sub)
    args = parser.parse_args(["rotate", ".env.gpg", "AAAA1111", "BBBB2222"])
    assert args.file == ".env.gpg"
    assert args.recipients == ["AAAA1111", "BBBB2222"]
