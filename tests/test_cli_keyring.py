"""Tests for envault.cli_keyring."""

import argparse
import sys
from unittest.mock import patch, MagicMock

import pytest

from envault.cli_keyring import cmd_key_add, cmd_key_list, cmd_key_remove

FP = "AABBCCDD11223344AABBCCDD11223344AABBCCDD"


def _ns(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


class TestCmdKeyAdd:
    def test_prints_success(self, capsys):
        with patch("envault.cli_keyring.add_key", return_value=[FP]) as mock_add:
            cmd_key_add(_ns(fingerprint=FP))
            mock_add.assert_called_once_with(FP)
        out = capsys.readouterr().out
        assert "Added" in out
        assert "1 key" in out

    def test_exits_on_error(self, capsys):
        from envault.keyring import KeyringError
        with patch("envault.cli_keyring.add_key", side_effect=KeyringError("dup")):
            with pytest.raises(SystemExit) as exc_info:
                cmd_key_add(_ns(fingerprint=FP))
        assert exc_info.value.code == 1
        assert "dup" in capsys.readouterr().err


class TestCmdKeyRemove:
    def test_prints_success(self, capsys):
        with patch("envault.cli_keyring.remove_key", return_value=[]) as mock_rm:
            cmd_key_remove(_ns(fingerprint=FP))
            mock_rm.assert_called_once_with(FP)
        out = capsys.readouterr().out
        assert "Removed" in out

    def test_exits_on_error(self, capsys):
        from envault.keyring import KeyringError
        with patch("envault.cli_keyring.remove_key", side_effect=KeyringError("missing")):
            with pytest.raises(SystemExit) as exc_info:
                cmd_key_remove(_ns(fingerprint=FP))
        assert exc_info.value.code == 1


class TestCmdKeyList:
    def test_prints_keys(self, capsys):
        with patch("envault.cli_keyring.load_keyring", return_value=[FP]):
            cmd_key_list(_ns())
        assert FP in capsys.readouterr().out

    def test_prints_hint_when_empty(self, capsys):
        with patch("envault.cli_keyring.load_keyring", return_value=[]):
            cmd_key_list(_ns())
        out = capsys.readouterr().out
        assert "No trusted keys" in out
