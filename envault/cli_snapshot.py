"""CLI subcommands for snapshot management."""

from __future__ import annotations

import sys
from pathlib import Path

from envault.snapshot import (
    SnapshotError,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
    save_snapshot,
)


def cmd_snapshot_save(args) -> None:
    """envault snapshot save [--name TAG] <encrypted_file>"""
    try:
        dest = save_snapshot(
            encrypted_file=Path(args.file),
            base_dir=Path(args.base_dir),
            name=getattr(args, "name", None),
        )
        print(f"Snapshot saved: {dest}")
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_snapshot_restore(args) -> None:
    """envault snapshot restore <snapshot_name> <destination>"""
    try:
        out = restore_snapshot(
            snapshot_name=args.snapshot,
            base_dir=Path(args.base_dir),
            destination=Path(args.destination),
        )
        print(f"Restored to: {out}")
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_snapshot_list(args) -> None:
    """envault snapshot list"""
    snapshots = list_snapshots(Path(args.base_dir))
    if not snapshots:
        print("No snapshots found.")
        return
    for name in snapshots:
        print(name)


def cmd_snapshot_delete(args) -> None:
    """envault snapshot delete <snapshot_name>"""
    try:
        delete_snapshot(args.snapshot, Path(args.base_dir))
        print(f"Deleted snapshot: {args.snapshot}")
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def register_snapshot_subcommands(subparsers, default_base_dir: str = ".") -> None:
    snap_parser = subparsers.add_parser("snapshot", help="Manage .env.enc snapshots")
    snap_sub = snap_parser.add_subparsers(dest="snapshot_cmd", required=True)

    # save
    p_save = snap_sub.add_parser("save", help="Save a snapshot of the encrypted file")
    p_save.add_argument("file", help="Path to the encrypted file")
    p_save.add_argument("--name", help="Optional tag for the snapshot")
    p_save.add_argument("--base-dir", default=default_base_dir, dest="base_dir")
    p_save.set_defaults(func=cmd_snapshot_save)

    # restore
    p_restore = snap_sub.add_parser("restore", help="Restore a snapshot")
    p_restore.add_argument("snapshot", help="Snapshot name")
    p_restore.add_argument("destination", help="Where to write the restored file")
    p_restore.add_argument("--base-dir", default=default_base_dir, dest="base_dir")
    p_restore.set_defaults(func=cmd_snapshot_restore)

    # list
    p_list = snap_sub.add_parser("list", help="List available snapshots")
    p_list.add_argument("--base-dir", default=default_base_dir, dest="base_dir")
    p_list.set_defaults(func=cmd_snapshot_list)

    # delete
    p_del = snap_sub.add_parser("delete", help="Delete a snapshot")
    p_del.add_argument("snapshot", help="Snapshot name")
    p_del.add_argument("--base-dir", default=default_base_dir, dest="base_dir")
    p_del.set_defaults(func=cmd_snapshot_delete)
