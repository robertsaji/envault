"""CLI commands for inspecting the envault audit log."""

from __future__ import annotations

import argparse
import json
import sys

from envault.audit import AuditError, load_events


def cmd_audit_log(args: argparse.Namespace) -> None:
    """Print recent audit log entries."""
    try:
        events = load_events(directory=getattr(args, "directory", None))
    except AuditError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not events:
        print("No audit events recorded yet.")
        return

    limit = getattr(args, "last", None)
    if limit and limit > 0:
        events = events[-limit:]

    if getattr(args, "json", False):
        print(json.dumps(events, indent=2))
    else:
        for e in events:
            actor = e.get("actor", "unknown")
            print(f"{e['timestamp']}  {actor:20s}  {e['action']:12s}  {e['target']}")


def register_audit_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    log_parser = subparsers.add_parser("audit", help="Show audit log")
    log_parser.add_argument(
        "--last",
        type=int,
        default=20,
        metavar="N",
        help="Show last N entries (default: 20)",
    )
    log_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    log_parser.add_argument(
        "--directory",
        default=None,
        help="Directory containing the audit log (default: cwd)",
    )
    log_parser.set_defaults(func=cmd_audit_log)
