"""Key rotation helpers: re-encrypt .env.gpg for a new set of recipients."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from .crypto import decrypt_file, encrypt_file, GPGError
from .config import load_config, get_recipients, ConfigError


class RotateError(Exception):
    """Raised when key rotation fails."""


def rotate(
    encrypted_path: Path,
    new_recipients: List[str],
    *,
    output_path: Path | None = None,
    tmp_suffix: str = ".tmp_plain",
) -> Path:
    """Decrypt *encrypted_path* then re-encrypt for *new_recipients*.

    The plaintext is written to a temporary file that is always removed,
    even on error.

    Returns the path of the newly encrypted file.
    """
    if not encrypted_path.exists():
        raise RotateError(f"Encrypted file not found: {encrypted_path}")
    if not new_recipients:
        raise RotateError("new_recipients must not be empty")

    tmp_plain = encrypted_path.with_suffix(tmp_suffix)
    try:
        try:
            decrypt_file(encrypted_path, output_path=tmp_plain)
        except GPGError as exc:
            raise RotateError(f"Decryption failed: {exc}") from exc

        out = output_path or encrypted_path
        try:
            encrypt_file(tmp_plain, recipients=new_recipients, output_path=out)
        except GPGError as exc:
            raise RotateError(f"Re-encryption failed: {exc}") from exc

        return out
    finally:
        if tmp_plain.exists():
            tmp_plain.unlink()


def rotate_from_config(config_path: Path, encrypted_path: Path | None = None) -> Path:
    """Load recipients from *config_path* and rotate *encrypted_path*."""
    try:
        cfg = load_config(config_path)
        recipients = get_recipients(cfg)
    except ConfigError as exc:
        raise RotateError(f"Config error: {exc}") from exc

    enc = encrypted_path or Path(cfg.get("encrypted_file", ".env.gpg"))
    return rotate(enc, recipients)
