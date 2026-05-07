"""Sync encrypted .env files with remote storage backends."""

import os
import shutil
from pathlib import Path


class SyncError(Exception):
    """Raised when a sync operation fails."""


def push(encrypted_path: Path, remote_dir: str) -> Path:
    """Copy an encrypted file to a remote directory (local or mounted path).

    Args:
        encrypted_path: Path to the local encrypted file.
        remote_dir: Destination directory (must exist or be creatable).

    Returns:
        The destination path.

    Raises:
        SyncError: If the source file is missing or the copy fails.
    """
    encrypted_path = Path(encrypted_path)
    if not encrypted_path.is_file():
        raise SyncError(f"Encrypted file not found: {encrypted_path}")

    dest_dir = Path(remote_dir)
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SyncError(f"Cannot create remote directory '{remote_dir}': {exc}") from exc

    dest = dest_dir / encrypted_path.name
    try:
        shutil.copy2(encrypted_path, dest)
    except OSError as exc:
        raise SyncError(f"Push failed: {exc}") from exc

    return dest


def pull(remote_dir: str, filename: str, local_dir: Path) -> Path:
    """Fetch an encrypted file from a remote directory.

    Args:
        remote_dir: Source directory containing the encrypted file.
        filename: Name of the encrypted file to fetch.
        local_dir: Local directory where the file will be placed.

    Returns:
        The local path of the fetched file.

    Raises:
        SyncError: If the remote file is missing or the copy fails.
    """
    source = Path(remote_dir) / filename
    if not source.is_file():
        raise SyncError(f"Remote file not found: {source}")

    local_dir = Path(local_dir)
    try:
        local_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SyncError(f"Cannot create local directory '{local_dir}': {exc}") from exc

    dest = local_dir / filename
    try:
        shutil.copy2(source, dest)
    except OSError as exc:
        raise SyncError(f"Pull failed: {exc}") from exc

    return dest


def remote_exists(remote_dir: str, filename: str) -> bool:
    """Check whether an encrypted file exists in the remote directory."""
    return (Path(remote_dir) / filename).is_file()


def list_remote(remote_dir: str, suffix: str = ".enc") -> list[str]:
    """List encrypted files available in a remote directory.

    Args:
        remote_dir: Directory to scan for encrypted files.
        suffix: File extension to filter by (default: '.enc').

    Returns:
        A sorted list of matching filenames.

    Raises:
        SyncError: If the remote directory cannot be read.
    """
    remote_path = Path(remote_dir)
    try:
        entries = [p.name for p in remote_path.iterdir() if p.is_file() and p.suffix == suffix]
    except OSError as exc:
        raise SyncError(f"Cannot list remote directory '{remote_dir}': {exc}") from exc
    return sorted(entries)
