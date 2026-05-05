"""CLI subcommand: envault diff — show changes between two .env files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .diff import DiffError, diff_env_files, format_diff


def cmd_diff(args: argparse.Namespace) -> None:
    """Compare two plaintext .env files and print a redacted diff."""
    old_path = Path(args.old)
    new_path = Path(args.new)
    redact = not args.show_values

    try:
        diff = diff_env_files(old_path, new_path)
    except DiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if diff.is_empty:
        print("No differences found.")
        return

    lines = format_diff(diff, redact=redact)
    summary = (
        f"+{len(diff.added)} added  "
        f"-{len(diff.removed)} removed  "
        f"~{len(diff.changed)} changed"
    )
    print(summary)
    for line in lines:
        print(line)


def register_diff_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "diff",
        help="Show differences between two .env files (values redacted by default)",
    )
    parser.add_argument("old", help="Path to the old/baseline .env file")
    parser.add_argument("new", help="Path to the new .env file")
    parser.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Print actual values instead of redacting them",
    )
    parser.set_defaults(func=cmd_diff)
