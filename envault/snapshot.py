"""Snapshot support: save and restore named .env.enc checkpoints."""

from __future__ import annotations

import shutil
from pathlib import Path
from datetime import datetime, timezone


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshot_dir(base_dir: Path) -> Path:
    return base_dir / ".envault" / "snapshots"


def _now_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def save_snapshot(
    encrypted_file: Path,
    base_dir: Path,
    name: str | None = None,
) -> Path:
    """Copy *encrypted_file* into the snapshot store and return the snapshot path."""
    if not encrypted_file.exists():
        raise SnapshotError(f"Encrypted file not found: {encrypted_file}")

    tag = name if name else _now_tag()
    # Sanitise the tag so it is safe as a filename component.
    tag = "".join(c if c.isalnum() or c in "-_." else "_" for c in tag)

    snap_dir = _snapshot_dir(base_dir)
    snap_dir.mkdir(parents=True, exist_ok=True)

    suffix = encrypted_file.suffix or ".enc"
    dest = snap_dir / f"{tag}{suffix}"
    shutil.copy2(encrypted_file, dest)
    return dest


def restore_snapshot(
    snapshot_name: str,
    base_dir: Path,
    destination: Path,
) -> Path:
    """Overwrite *destination* with the named snapshot and return *destination*."""
    snap_dir = _snapshot_dir(base_dir)
    # Allow callers to pass just the tag or the full filename.
    candidate = snap_dir / snapshot_name
    if not candidate.exists():
        # Try adding common extensions.
        for ext in (".enc", ".gpg"):
            candidate = snap_dir / f"{snapshot_name}{ext}"
            if candidate.exists():
                break
        else:
            raise SnapshotError(f"Snapshot not found: {snapshot_name!r}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidate, destination)
    return destination


def list_snapshots(base_dir: Path) -> list[str]:
    """Return snapshot filenames sorted oldest-first."""
    snap_dir = _snapshot_dir(base_dir)
    if not snap_dir.exists():
        return []
    return sorted(p.name for p in snap_dir.iterdir() if p.is_file())


def delete_snapshot(snapshot_name: str, base_dir: Path) -> None:
    """Remove a single snapshot by name (with or without extension)."""
    snap_dir = _snapshot_dir(base_dir)
    candidate = snap_dir / snapshot_name
    if not candidate.exists():
        for ext in (".enc", ".gpg"):
            candidate = snap_dir / f"{snapshot_name}{ext}"
            if candidate.exists():
                break
        else:
            raise SnapshotError(f"Snapshot not found: {snapshot_name!r}")
    candidate.unlink()
