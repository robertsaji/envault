"""CLI subcommands for the export feature."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envault.export import ExportError, export_env


def cmd_export(args: Namespace) -> None:
    """Handle the ``envault export`` subcommand."""
    source = Path(args.file)
    fmt = args.format
    no_export = getattr(args, "no_export", False)

    try:
        output = export_env(source, fmt=fmt, export_keyword=not no_export)
    except ExportError as exc:
        print(f"export error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(output + "\n", encoding="utf-8")
        print(f"Exported to {out_path}")
    else:
        print(output)


def register_export_subcommands(sub: "_SubParsersAction") -> None:  # type: ignore[name-defined]
    """Attach the export subcommand to *sub*."""
    p: ArgumentParser = sub.add_parser(
        "export",
        help="Export decrypted .env to shell, JSON, or Docker format",
    )
    p.add_argument(
        "file",
        help="Path to the plaintext .env file",
    )
    p.add_argument(
        "-f",
        "--format",
        choices=["shell", "json", "docker"],
        default="shell",
        help="Output format (default: shell)",
    )
    p.add_argument(
        "-o",
        "--output",
        default="",
        help="Write output to this file instead of stdout",
    )
    p.add_argument(
        "--no-export",
        action="store_true",
        default=False,
        help="Omit the 'export' keyword in shell format",
    )
    p.set_defaults(func=cmd_export)
