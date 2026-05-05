"""Manage trusted GPG key fingerprints stored in .envault-keys."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

KEYRING_FILE = ".envault-keys"
FINGERPRINT_RE = re.compile(r"^[0-9A-Fa-f]{16,40}$")


class KeyringError(Exception):
    """Raised for keyring-related failures."""


def _keyring_path(base_dir: Path | None = None) -> Path:
    root = base_dir or Path.cwd()
    return root / KEYRING_FILE


def load_keyring(base_dir: Path | None = None) -> List[str]:
    """Return list of trusted fingerprints from the keyring file."""
    path = _keyring_path(base_dir)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def save_keyring(fingerprints: List[str], base_dir: Path | None = None) -> Path:
    """Persist the list of fingerprints to the keyring file."""
    _validate_fingerprints(fingerprints)
    path = _keyring_path(base_dir)
    content = "# envault trusted key fingerprints\n" + "\n".join(fingerprints) + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def add_key(fingerprint: str, base_dir: Path | None = None) -> List[str]:
    """Add a fingerprint to the keyring if not already present."""
    _validate_fingerprints([fingerprint])
    keys = load_keyring(base_dir)
    fp = fingerprint.upper()
    normalised = [k.upper() for k in keys]
    if fp in normalised:
        raise KeyringError(f"Fingerprint already trusted: {fingerprint}")
    keys.append(fingerprint.upper())
    save_keyring(keys, base_dir)
    return keys


def remove_key(fingerprint: str, base_dir: Path | None = None) -> List[str]:
    """Remove a fingerprint from the keyring."""
    keys = load_keyring(base_dir)
    upper = [k.upper() for k in keys]
    fp = fingerprint.upper()
    if fp not in upper:
        raise KeyringError(f"Fingerprint not found in keyring: {fingerprint}")
    keys = [k for k in keys if k.upper() != fp]
    save_keyring(keys, base_dir)
    return keys


def _validate_fingerprints(fingerprints: List[str]) -> None:
    for fp in fingerprints:
        if not FINGERPRINT_RE.match(fp):
            raise KeyringError(f"Invalid fingerprint format: {fp}")
