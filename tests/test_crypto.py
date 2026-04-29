"""Tests for envault.crypto module."""

import os
import subprocess
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from envault.crypto import encrypt_file, decrypt_file, list_keys, GPGError


def _make_gpg_result(returncode: int, stderr: str = "", stdout: str = "") -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stderr = stderr
    result.stdout = stdout
    return result


class TestEncryptFile:
    def test_raises_when_no_recipients(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET=abc")
        with pytest.raises(GPGError, match="At least one recipient"):
            encrypt_file(str(env_file), [])

    def test_default_output_path(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET=abc")
        with patch("subprocess.run", return_value=_make_gpg_result(0)) as mock_run:
            out = encrypt_file(str(env_file), ["user@example.com"])
        assert out == str(env_file) + ".gpg"
        mock_run.assert_called_once()

    def test_custom_output_path(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET=abc")
        custom_out = str(tmp_path / "out.gpg")
        with patch("subprocess.run", return_value=_make_gpg_result(0)):
            out = encrypt_file(str(env_file), ["user@example.com"], custom_out)
        assert out == custom_out

    def test_raises_on_gpg_failure(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET=abc")
        with patch("subprocess.run", return_value=_make_gpg_result(2, stderr="key not found")):
            with pytest.raises(GPGError, match="key not found"):
                encrypt_file(str(env_file), ["bad@key.com"])


class TestDecryptFile:
    def test_strips_gpg_extension(self, tmp_path):
        enc_file = tmp_path / ".env.gpg"
        enc_file.write_bytes(b"encrypted")
        with patch("subprocess.run", return_value=_make_gpg_result(0)) as mock_run:
            out = decrypt_file(str(enc_file))
        assert out == str(tmp_path / ".env")

    def test_fallback_suffix_when_no_gpg_ext(self, tmp_path):
        enc_file = tmp_path / "secrets"
        enc_file.write_bytes(b"encrypted")
        with patch("subprocess.run", return_value=_make_gpg_result(0)):
            out = decrypt_file(str(enc_file))
        assert out.endswith(".decrypted")

    def test_raises_on_gpg_failure(self, tmp_path):
        enc_file = tmp_path / ".env.gpg"
        enc_file.write_bytes(b"encrypted")
        with patch("subprocess.run", return_value=_make_gpg_result(2, stderr="bad passphrase")):
            with pytest.raises(GPGError, match="bad passphrase"):
                decrypt_file(str(enc_file))


class TestListKeys:
    _COLON_OUTPUT = (
        "pub:u:4096:1:ABCD1234EFGH5678:2023-01-01:::u:::scESC:\n"
        "uid:u::::2023-01-01::HASH::Alice <alice@example.com>:::::::::0:\n"
    )

    def test_parses_keys(self):
        with patch("subprocess.run", return_value=_make_gpg_result(0, stdout=self._COLON_OUTPUT)):
            keys = list_keys()
        assert len(keys) == 1
        assert keys[0]["uid"] == "Alice <alice@example.com>"

    def test_raises_on_failure(self):
        with patch("subprocess.run", return_value=_make_gpg_result(1, stderr="gpg error")):
            with pytest.raises(GPGError, match="gpg error"):
                list_keys()
