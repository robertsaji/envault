"""GPG encryption and decryption utilities for envault."""

import subprocess
import tempfile
import os
from typing import Optional


class GPGError(Exception):
    """Raised when a GPG operation fails."""
    pass


def encrypt_file(input_path: str, recipients: list[str], output_path: Optional[str] = None) -> str:
    """Encrypt a file for one or more GPG recipients.

    Args:
        input_path: Path to the plaintext file.
        recipients: List of GPG key IDs or email addresses.
        output_path: Optional path for the encrypted output file.

    Returns:
        Path to the encrypted output file.

    Raises:
        GPGError: If encryption fails.
    """
    if not recipients:
        raise GPGError("At least one recipient is required for encryption.")

    if output_path is None:
        output_path = input_path + ".gpg"

    cmd = ["gpg", "--yes", "--batch", "--output", output_path]
    for recipient in recipients:
        cmd += ["--recipient", recipient]
    cmd += ["--encrypt", input_path]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise GPGError(f"Encryption failed: {result.stderr.strip()}")

    return output_path


def decrypt_file(input_path: str, output_path: Optional[str] = None) -> str:
    """Decrypt a GPG-encrypted file.

    Args:
        input_path: Path to the encrypted .gpg file.
        output_path: Optional path for the decrypted output file.

    Returns:
        Path to the decrypted output file.

    Raises:
        GPGError: If decryption fails.
    """
    if output_path is None:
        output_path = input_path.removesuffix(".gpg")
        if output_path == input_path:
            output_path = input_path + ".decrypted"

    cmd = ["gpg", "--yes", "--batch", "--output", output_path, "--decrypt", input_path]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise GPGError(f"Decryption failed: {result.stderr.strip()}")

    return output_path


def list_keys(secret: bool = False) -> list[dict]:
    """List available GPG keys.

    Args:
        secret: If True, list secret (private) keys instead of public keys.

    Returns:
        List of dicts with 'keyid' and 'uid' fields.
    """
    flag = "--list-secret-keys" if secret else "--list-keys"
    cmd = ["gpg", "--with-colons", flag]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise GPGError(f"Failed to list keys: {result.stderr.strip()}")

    keys = []
    current_key: dict = {}
    for line in result.stdout.splitlines():
        parts = line.split(":")
        if parts[0] in ("pub", "sec"):
            current_key = {"keyid": parts[4], "uid": ""}
        elif parts[0] == "uid" and current_key:
            current_key["uid"] = parts[9]
            keys.append(current_key)
            current_key = {}
    return keys
