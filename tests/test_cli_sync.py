"""Integration-style tests for the push/pull CLI commands."""

import argparse
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from envault.cli import cmd_push, cmd_pull


def _ns(**kwargs):
    defaults = {"file": ".env", "remote": None, "filename": None, "output": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# cmd_push
# ---------------------------------------------------------------------------

class TestCmdPush:
    def test_push_success(self, tmp_path, capsys):
        encrypted = tmp_path / ".env.gpg"
        encrypted.write_bytes(b"enc")
        dest = tmp_path / "remote" / ".env.gpg"

        with patch("envault.cli.load_config", return_value={"remote": str(tmp_path / "remote")}), \
             patch("envault.cli.get_recipients", return_value=["alice@example.com"]), \
             patch("envault.cli.encrypt_file", return_value=encrypted), \
             patch("envault.cli.push", return_value=dest) as mock_push:

            cmd_push(_ns())
            mock_push.assert_called_once_with(encrypted, str(tmp_path / "remote"))

        out = capsys.readouterr().out
        assert "Pushed" in out

    def test_push_exits_when_no_remote(self, capsys):
        with patch("envault.cli.load_config", return_value={}), \
             patch("envault.cli.get_recipients", return_value=["alice@example.com"]), \
             pytest.raises(SystemExit) as exc_info:
            cmd_push(_ns())
        assert exc_info.value.code == 1

    def test_push_exits_on_sync_error(self, tmp_path, capsys):
        from envault.sync import SyncError
        encrypted = tmp_path / ".env.gpg"
        encrypted.write_bytes(b"enc")

        with patch("envault.cli.load_config", return_value={"remote": "/remote"}), \
             patch("envault.cli.get_recipients", return_value=["alice"]), \
             patch("envault.cli.encrypt_file", return_value=encrypted), \
             patch("envault.cli.push", side_effect=SyncError("boom")), \
             pytest.raises(SystemExit) as exc_info:
            cmd_push(_ns())
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# cmd_pull
# ---------------------------------------------------------------------------

class TestCmdPull:
    def test_pull_success(self, tmp_path, capsys):
        local_enc = tmp_path / ".env.gpg"
        decrypted = tmp_path / ".env"

        with patch("envault.cli.load_config", return_value={"remote": "/remote"}), \
             patch("envault.cli.pull", return_value=local_enc), \
             patch("envault.cli.decrypt_file", return_value=decrypted):

            cmd_pull(_ns())

        out = capsys.readouterr().out
        assert "decrypted" in out.lower()

    def test_pull_exits_when_no_remote(self, capsys):
        with patch("envault.cli.load_config", return_value={}), \
             pytest.raises(SystemExit) as exc_info:
            cmd_pull(_ns())
        assert exc_info.value.code == 1

    def test_pull_uses_custom_filename(self, tmp_path):
        local_enc = tmp_path / "prod.env.gpg"
        with patch("envault.cli.load_config", return_value={"remote": "/r"}), \
             patch("envault.cli.pull", return_value=local_enc) as mock_pull, \
             patch("envault.cli.decrypt_file", return_value=tmp_path / ".env"):
            cmd_pull(_ns(filename="prod.env.gpg"))
        mock_pull.assert_called_once_with("/r", "prod.env.gpg", local_dir=Path("."))
