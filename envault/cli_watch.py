"""CLI subcommands for the watch feature."""

from __future__ import annotations

import sys
from pathlib import Path

from envault.config import load_config, get_recipients, ConfigError
from envault.crypto import encrypt_file, GPGError
from envault.audit import record_event
from envault.watch import watch, WatchError


def cmd_watch(args) -> None:  # pragma: no cover – thin I/O wrapper
    """Watch a .env file and re-encrypt on every save."""
    source = Path(args.file)
    output = Path(args.output) if args.output else source.with_suffix(".env.gpg")

    try:
        cfg = load_config()
        recipients = get_recipients(cfg)
    except ConfigError as exc:
        print(f"[envault] config error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not recipients:
        print("[envault] no recipients configured — aborting.", file=sys.stderr)
        sys.exit(1)

    print(f"[envault] watching {source}  (Ctrl-C to stop)")

    def _on_change(path: Path) -> None:
        try:
            encrypt_file(path, recipients, output=output)
            record_event("watch.encrypt", file=str(path), output=str(output))
            print(f"[envault] re-encrypted → {output}")
        except GPGError as exc:
            print(f"[envault] encrypt failed: {exc}", file=sys.stderr)

    try:
        watch(source, _on_change, interval=getattr(args, "interval", 1.0))
    except WatchError as exc:
        print(f"[envault] {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[envault] stopped.")


def register_watch_subcommands(subparsers) -> None:
    """Attach the *watch* subcommand to an existing argparse subparsers group."""
    p = subparsers.add_parser("watch", help="Re-encrypt .env automatically on change")
    p.add_argument("file", help="Plaintext .env file to watch")
    p.add_argument("-o", "--output", default=None, help="Encrypted output path")
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECS",
        help="Polling interval in seconds (default: 1.0)",
    )
    p.set_defaults(func=cmd_watch)
