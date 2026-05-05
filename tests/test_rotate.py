"""Unit tests for envault.rotate."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from envault.rotate import rotate, RotateError, rotate_from_config
from envault.crypto import GPGError


RECIPIENTS = ["AAAA1111", "BBBB2222"]


# ---------------------------------------------------------------------------
# rotate()
# ---------------------------------------------------------------------------

class TestRotate:
    def test_raises_when_encrypted_file_missing(self, tmp_path):
        with pytest.raises(RotateError, match="not found"):
            rotate(tmp_path / "missing.gpg", RECIPIENTS)

    def test_raises_when_no_recipients(self, tmp_path):
        enc = tmp_path / "vault.gpg"
        enc.write_bytes(b"data")
        with pytest.raises(RotateError, match="must not be empty"):
            rotate(enc, [])

    def test_raises_on_decrypt_failure(self, tmp_path):
        enc = tmp_path / "vault.gpg"
        enc.write_bytes(b"data")
        with patch("envault.rotate.decrypt_file", side_effect=GPGError("bad")):
            with pytest.raises(RotateError, match="Decryption failed"):
                rotate(enc, RECIPIENTS)

    def test_raises_on_encrypt_failure(self, tmp_path):
        enc = tmp_path / "vault.gpg"
        enc.write_bytes(b"data")
        with patch("envault.rotate.decrypt_file"), \
             patch("envault.rotate.encrypt_file", side_effect=GPGError("bad")):
            with pytest.raises(RotateError, match="Re-encryption failed"):
                rotate(enc, RECIPIENTS)

    def test_tmp_plain_removed_on_success(self, tmp_path):
        enc = tmp_path / "vault.gpg"
        enc.write_bytes(b"data")
        with patch("envault.rotate.decrypt_file"), \
             patch("envault.rotate.encrypt_file"):
            rotate(enc, RECIPIENTS)
        assert not (tmp_path / "vault.tmp_plain").exists()

    def test_tmp_plain_removed_on_failure(self, tmp_path):
        enc = tmp_path / "vault.gpg"
        enc.write_bytes(b"data")

        def _create_tmp(src, output_path=None):
            output_path.write_bytes(b"plain")

        with patch("envault.rotate.decrypt_file", side_effect=_create_tmp), \
             patch("envault.rotate.encrypt_file", side_effect=GPGError("x")):
            with pytest.raises(RotateError):
                rotate(enc, RECIPIENTS)
        assert not (tmp_path / "vault.tmp_plain").exists()

    def test_returns_output_path(self, tmp_path):
        enc = tmp_path / "vault.gpg"
        enc.write_bytes(b"data")
        out = tmp_path / "new.gpg"
        with patch("envault.rotate.decrypt_file"), \
             patch("envault.rotate.encrypt_file"):
            result = rotate(enc, RECIPIENTS, output_path=out)
        assert result == out

    def test_defaults_output_to_input(self, tmp_path):
        enc = tmp_path / "vault.gpg"
        enc.write_bytes(b"data")
        with patch("envault.rotate.decrypt_file"), \
             patch("envault.rotate.encrypt_file"):
            result = rotate(enc, RECIPIENTS)
        assert result == enc


# ---------------------------------------------------------------------------
# rotate_from_config()
# ---------------------------------------------------------------------------

def test_rotate_from_config_uses_config_recipients(tmp_path):
    cfg_path = tmp_path / "envault.toml"
    enc = tmp_path / ".env.gpg"
    enc.write_bytes(b"data")
    cfg = {"recipients": RECIPIENTS, "encrypted_file": str(enc)}
    with patch("envault.rotate.load_config", return_value=cfg), \
         patch("envault.rotate.get_recipients", return_value=RECIPIENTS), \
         patch("envault.rotate.rotate", return_value=enc) as mock_rot:
        rotate_from_config(cfg_path)
    mock_rot.assert_called_once()
