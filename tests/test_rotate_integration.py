"""Integration tests for the rotate workflow (mocked GPG calls)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from envault.rotate import rotate, RotateError


PLAINTEXT = b"SECRET=hunter2\nAPI_KEY=abc123\n"
RECIPIENTS_OLD = ["OLD_FP_1111"]
RECIPIENTS_NEW = ["NEW_FP_AAAA", "NEW_FP_BBBB"]


def _fake_decrypt(src: Path, output_path: Path | None = None):
    """Write plaintext to output_path to simulate decryption."""
    dest = output_path or src.with_suffix("")
    dest.write_bytes(PLAINTEXT)


def _fake_encrypt(src: Path, recipients, output_path: Path | None = None):
    """Write a fake ciphertext blob to output_path."""
    dest = output_path or src.with_suffix(".gpg")
    dest.write_bytes(b"ENCRYPTED:" + src.read_bytes())


class TestRotateIntegration:
    def test_full_rotate_cycle(self, tmp_path):
        enc = tmp_path / "vault.gpg"
        enc.write_bytes(b"OLDCIPHERTEXT")

        with patch("envault.rotate.decrypt_file", side_effect=_fake_decrypt), \
             patch("envault.rotate.encrypt_file", side_effect=_fake_encrypt):
            result = rotate(enc, RECIPIENTS_NEW)

        assert result == enc
        # Temporary plain file must be gone
        assert not (tmp_path / "vault.tmp_plain").exists()

    def test_rotate_to_different_output(self, tmp_path):
        enc = tmp_path / "vault.gpg"
        enc.write_bytes(b"OLDCIPHERTEXT")
        out = tmp_path / "vault_new.gpg"

        with patch("envault.rotate.decrypt_file", side_effect=_fake_decrypt), \
             patch("envault.rotate.encrypt_file", side_effect=_fake_encrypt):
            result = rotate(enc, RECIPIENTS_NEW, output_path=out)

        assert result == out

    def test_original_preserved_when_output_differs(self, tmp_path):
        enc = tmp_path / "vault.gpg"
        original_bytes = b"OLDCIPHERTEXT"
        enc.write_bytes(original_bytes)
        out = tmp_path / "vault_new.gpg"

        with patch("envault.rotate.decrypt_file", side_effect=_fake_decrypt), \
             patch("envault.rotate.encrypt_file", side_effect=_fake_encrypt):
            rotate(enc, RECIPIENTS_NEW, output_path=out)

        assert enc.read_bytes() == original_bytes
