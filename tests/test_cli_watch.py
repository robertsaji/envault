"""Unit tests for envault.cli_watch."""

from __future__ import annotations

import types
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from envault.cli_watch import cmd_watch, register_watch_subcommands
from envault.watch import WatchError
from envault.crypto import GPGError
from envault.config import ConfigError


def _ns(**kwargs):
    defaults = {"file": ".env", "output": None, "interval": 1.0}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# register_watch_subcommands
# ---------------------------------------------------------------------------

def test_registers_watch_subcommand():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_watch_subcommands(sub)
    ns = parser.parse_args(["watch", ".env"])
    assert ns.file == ".env"
    assert ns.interval == 1.0


# ---------------------------------------------------------------------------
# cmd_watch — config errors
# ---------------------------------------------------------------------------

def test_exits_on_config_error(tmp_path):
    with patch("envault.cli_watch.load_config", side_effect=ConfigError("bad")):
        with pytest.raises(SystemExit) as exc_info:
            cmd_watch(_ns(file=str(tmp_path / ".env")))
    assert exc_info.value.code == 1


def test_exits_when_no_recipients(tmp_path):
    with patch("envault.cli_watch.load_config", return_value={}), \
         patch("envault.cli_watch.get_recipients", return_value=[]):
        with pytest.raises(SystemExit) as exc_info:
            cmd_watch(_ns(file=str(tmp_path / ".env")))
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# cmd_watch — WatchError
# ---------------------------------------------------------------------------

def test_exits_on_watch_error(tmp_path):
    with patch("envault.cli_watch.load_config", return_value={}), \
         patch("envault.cli_watch.get_recipients", return_value=["AABBCCDD"]), \
         patch("envault.cli_watch.watch", side_effect=WatchError("gone")):
        with pytest.raises(SystemExit) as exc_info:
            cmd_watch(_ns(file=str(tmp_path / ".env")))
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# cmd_watch — on_change callback
# ---------------------------------------------------------------------------

def test_on_change_calls_encrypt_and_audit(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("K=V")

    captured_callback = {}

    def fake_watch(source, on_change, *, interval, max_iterations=None):
        captured_callback["fn"] = on_change

    with patch("envault.cli_watch.load_config", return_value={}), \
         patch("envault.cli_watch.get_recipients", return_value=["AABBCCDD"]), \
         patch("envault.cli_watch.watch", side_effect=fake_watch), \
         patch("envault.cli_watch.encrypt_file") as mock_enc, \
         patch("envault.cli_watch.record_event") as mock_rec:
        cmd_watch(_ns(file=str(env)))
        captured_callback["fn"](env)

    mock_enc.assert_called_once()
    mock_rec.assert_called_once_with("watch.encrypt", file=str(env), output=str(env.with_suffix(".env.gpg")))
    out = capsys.readouterr().out
    assert "re-encrypted" in out


def test_on_change_prints_error_on_gpg_failure(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("K=V")

    captured_callback = {}

    def fake_watch(source, on_change, *, interval, max_iterations=None):
        captured_callback["fn"] = on_change

    with patch("envault.cli_watch.load_config", return_value={}), \
         patch("envault.cli_watch.get_recipients", return_value=["AABBCCDD"]), \
         patch("envault.cli_watch.watch", side_effect=fake_watch), \
         patch("envault.cli_watch.encrypt_file", side_effect=GPGError("oops")):
        cmd_watch(_ns(file=str(env)))
        captured_callback["fn"](env)

    err = capsys.readouterr().err
    assert "encrypt failed" in err
