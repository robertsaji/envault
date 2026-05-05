"""Verify integrity of encrypted .env files using GPG signatures."""

from __future__ import annotations

import subprocess
from pathlib import Path


class VerifyError(Exception):
    """Raised when verification fails."""


def verify_signature(encrypted_file: Path, signature_file: Path | None = None) -> dict:
    """Verify the GPG signature of an encrypted file.

    If *signature_file* is None, a detached signature at
    ``<encrypted_file>.sig`` is assumed.

    Returns a dict with keys:
        - valid (bool)
        - fingerprint (str | None)
        - signer (str | None)
        - message (str)
    """
    encrypted_file = Path(encrypted_file)
    if not encrypted_file.exists():
        raise VerifyError(f"Encrypted file not found: {encrypted_file}")

    if signature_file is None:
        signature_file = Path(str(encrypted_file) + ".sig")

    signature_file = Path(signature_file)

    if signature_file.exists():
        result = _verify_detached(encrypted_file, signature_file)
    else:
        result = _verify_inline(encrypted_file)

    return result


def sign_file(source: Path, output: Path | None = None) -> Path:
    """Create a detached GPG signature for *source*.

    Returns the path to the ``.sig`` file.
    """
    source = Path(source)
    if not source.exists():
        raise VerifyError(f"Source file not found: {source}")

    sig_path = Path(str(output) if output else str(source) + ".sig")

    cmd = ["gpg", "--batch", "--yes", "--detach-sign", "--output", str(sig_path), str(source)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise VerifyError(f"GPG signing failed: {proc.stderr.strip()}")

    return sig_path


def _verify_detached(encrypted_file: Path, signature_file: Path) -> dict:
    cmd = ["gpg", "--batch", "--verify", str(signature_file), str(encrypted_file)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return _parse_verify_output(proc)


def _verify_inline(encrypted_file: Path) -> dict:
    cmd = ["gpg", "--batch", "--verify", str(encrypted_file)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return _parse_verify_output(proc)


def _parse_verify_output(proc: subprocess.CompletedProcess) -> dict:
    stderr = proc.stderr
    valid = proc.returncode == 0

    fingerprint: str | None = None
    signer: str | None = None

    for line in stderr.splitlines():
        if "Primary key fingerprint:" in line:
            fingerprint = line.split(":", 1)[-1].strip().replace(" ", "")
        elif "Good signature from" in line:
            signer = line.split("Good signature from", 1)[-1].strip().strip('"')

    return {
        "valid": valid,
        "fingerprint": fingerprint,
        "signer": signer,
        "message": stderr.strip(),
    }
