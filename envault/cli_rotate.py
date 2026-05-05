"""CLI sub-commands for key rotation."""

from __future__ import annotations

import sys
from pathlib import Path

from .rotate import rotate, RotateError
from .audit import record_event


def cmd_rotate(args) -> None:  # pragma: no cover – thin CLI glue
    """Re-encrypt the vault file for a new recipient list."""
    encrypted = Path(args.file)
    recipients: list[str] = args.recipients

    if not recipients:
        print("error: at least one recipient fingerprint is required", file=sys.stderr)
        sys.exit(1)

    try:
        out = rotate(encrypted, recipients)
    except RotateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    record_event(
        "rotate",
        file=str(out),
        recipients=recipients,
    )
    print(f"Rotated: {out}")


def register_rotate_subcommands(subparsers) -> None:
    """Attach the *rotate* sub-command to *subparsers*."""
    p = subparsers.add_parser(
        "rotate",
        help="Re-encrypt vault file for a new set of GPG recipients",
    )
    p.add_argument(
        "file",
        help="Path to the encrypted vault file (e.g. .env.gpg)",
    )
    p.add_argument(
        "recipients",
        nargs="+",
        metavar="FINGERPRINT",
        help="GPG fingerprint(s) of the new recipients",
    )
    p.set_defaults(func=cmd_rotate)
