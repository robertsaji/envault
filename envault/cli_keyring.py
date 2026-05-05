"""CLI commands for managing the envault keyring."""

from __future__ import annotations

import argparse
import sys

from envault.keyring import KeyringError, add_key, load_keyring, remove_key


def cmd_key_add(args: argparse.Namespace) -> None:
    """Add a GPG fingerprint to the trusted keyring."""
    try:
        keys = add_key(args.fingerprint)
    except KeyringError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Added {args.fingerprint.upper()} ({len(keys)} key(s) trusted)")


def cmd_key_remove(args: argparse.Namespace) -> None:
    """Remove a GPG fingerprint from the trusted keyring."""
    try:
        keys = remove_key(args.fingerprint)
    except KeyringError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Removed {args.fingerprint.upper()} ({len(keys)} key(s) remaining)")


def cmd_key_list(_args: argparse.Namespace) -> None:
    """List all trusted fingerprints in the keyring."""
    keys = load_keyring()
    if not keys:
        print("No trusted keys found. Use 'envault key add <fingerprint>' to add one.")
        return
    for fp in keys:
        print(fp)


def register_keyring_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach key sub-commands to the parent parser."""
    key_parser = subparsers.add_parser("key", help="Manage trusted GPG keys")
    key_sub = key_parser.add_subparsers(dest="key_cmd", required=True)

    p_add = key_sub.add_parser("add", help="Trust a new fingerprint")
    p_add.add_argument("fingerprint", help="40-char GPG fingerprint")
    p_add.set_defaults(func=cmd_key_add)

    p_rm = key_sub.add_parser("remove", help="Revoke trust for a fingerprint")
    p_rm.add_argument("fingerprint", help="40-char GPG fingerprint")
    p_rm.set_defaults(func=cmd_key_remove)

    p_ls = key_sub.add_parser("list", help="List trusted fingerprints")
    p_ls.set_defaults(func=cmd_key_list)
