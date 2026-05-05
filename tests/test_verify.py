"""Tests for envault.verify and envault.cli_verify."""

from __future__ import annotations

import types
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.verify import VerifyError, _parse_verify_output, sign_file, verify_signature
from envault.cli_verify import cmd_sign, cmd_verify


def _ns(**kwargs) -> Namespace:
    defaults = {"file": "secrets.env.gpg", "signature": None, "output": None}
    defaults.update(kwargs)
    return Namespace(**defaults)


# ---------------------------------------------------------------------------
# _parse_verify_output
# ---------------------------------------------------------------------------

def _make_proc(returncode: int, stderr: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(returncode=returncode, stderr=stderr)


def test_parse_valid_signature():
    stderr = (
        "gpg: Good signature from \"Alice <alice@example.com>\"\n"
        "gpg: Primary key fingerprint: ABCD 1234 EF56 7890\n"
    )
    result = _parse_verify_output(_make_proc(0, stderr))
    assert result["valid"] is True
    assert result["signer"] == "Alice <alice@example.com>"
    assert result["fingerprint"] == "ABCD1234EF567890"


def test_parse_invalid_signature():
    result = _parse_verify_output(_make_proc(2, "gpg: BAD signature"))
    assert result["valid"] is False
    assert result["fingerprint"] is None
    assert result["signer"] is None


# ---------------------------------------------------------------------------
# verify_signature
# ---------------------------------------------------------------------------

def test_raises_when_encrypted_file_missing(tmp_path):
    with pytest.raises(VerifyError, match="not found"):
        verify_signature(tmp_path / "missing.gpg")


def test_uses_detached_sig_when_present(tmp_path):
    enc = tmp_path / "secrets.env.gpg"
    sig = tmp_path / "secrets.env.gpg.sig"
    enc.write_bytes(b"data")
    sig.write_bytes(b"sig")

    fake_proc = _make_proc(0, "gpg: Good signature from \"Bob <bob@example.com>\"")
    with patch("envault.verify.subprocess.run", return_value=fake_proc) as mock_run:
        result = verify_signature(enc)
    assert result["valid"] is True
    cmd = mock_run.call_args[0][0]
    assert str(sig) in cmd
    assert str(enc) in cmd


def test_falls_back_to_inline_when_no_sig_file(tmp_path):
    enc = tmp_path / "secrets.env.gpg"
    enc.write_bytes(b"data")

    fake_proc = _make_proc(1, "gpg: no signature")
    with patch("envault.verify.subprocess.run", return_value=fake_proc) as mock_run:
        result = verify_signature(enc)
    assert result["valid"] is False
    cmd = mock_run.call_args[0][0]
    assert str(enc) in cmd
    assert "--verify" in cmd


# ---------------------------------------------------------------------------
# sign_file
# ---------------------------------------------------------------------------

def test_sign_raises_when_source_missing(tmp_path):
    with pytest.raises(VerifyError, match="not found"):
        sign_file(tmp_path / "ghost.gpg")


def test_sign_raises_on_gpg_failure(tmp_path):
    src = tmp_path / "file.gpg"
    src.write_bytes(b"x")
    fake_proc = _make_proc(1, "gpg: signing failed")
    with patch("envault.verify.subprocess.run", return_value=fake_proc):
        with pytest.raises(VerifyError, match="signing failed"):
            sign_file(src)


def test_sign_returns_sig_path(tmp_path):
    src = tmp_path / "file.gpg"
    src.write_bytes(b"x")
    fake_proc = _make_proc(0, "")
    with patch("envault.verify.subprocess.run", return_value=fake_proc):
        sig = sign_file(src)
    assert str(sig).endswith(".sig")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cmd_verify_success(tmp_path, capsys):
    enc = tmp_path / "secrets.env.gpg"
    enc.write_bytes(b"x")
    ok = {"valid": True, "signer": "Alice", "fingerprint": "ABCD", "message": ""}
    with patch("envault.cli_verify.verify_signature", return_value=ok):
        cmd_verify(_ns(file=str(enc)))
    out = capsys.readouterr().out
    assert "valid" in out
    assert "Alice" in out


def test_cmd_verify_invalid_exits(tmp_path):
    enc = tmp_path / "secrets.env.gpg"
    enc.write_bytes(b"x")
    bad = {"valid": False, "signer": None, "fingerprint": None, "message": "BAD"}
    with patch("envault.cli_verify.verify_signature", return_value=bad):
        with pytest.raises(SystemExit) as exc_info:
            cmd_verify(_ns(file=str(enc)))
    assert exc_info.value.code == 2


def test_cmd_sign_success(tmp_path, capsys):
    src = tmp_path / "file.gpg"
    src.write_bytes(b"x")
    with patch("envault.cli_verify.sign_file", return_value=Path("file.gpg.sig")) as mock_sign:
        cmd_sign(_ns(file=str(src)))
    out = capsys.readouterr().out
    assert "signed" in out


def test_cmd_sign_exits_on_error(tmp_path):
    src = tmp_path / "file.gpg"
    src.write_bytes(b"x")
    with patch("envault.cli_verify.sign_file", side_effect=VerifyError("boom")):
        with pytest.raises(SystemExit) as exc_info:
            cmd_sign(_ns(file=str(src)))
    assert exc_info.value.code == 1
