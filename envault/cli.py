"""Command-line interface for envault."""

import argparse
import sys
from pathlib import Path

from envault.config import ConfigError, init_config, load_config, get_recipients
from envault.crypto import GPGError, encrypt_file, decrypt_file
from envault.sync import SyncError, push, pull


def cmd_init(args: argparse.Namespace) -> None:
    """Initialise a new envault configuration."""
    try:
        path = init_config(args.recipients, remote=args.remote)
        print(f"Initialised envault config at {path}")
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_encrypt(args: argparse.Namespace) -> None:
    """Encrypt the .env file."""
    try:
        cfg = load_config()
        recipients = get_recipients(cfg)
        out = encrypt_file(Path(args.file), recipients, output=args.output)
        print(f"Encrypted → {out}")
    except (ConfigError, GPGError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_decrypt(args: argparse.Namespace) -> None:
    """Decrypt the .env file."""
    try:
        out = decrypt_file(Path(args.file), output=args.output)
        print(f"Decrypted → {out}")
    except GPGError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_push(args: argparse.Namespace) -> None:
    """Encrypt and push .env to remote storage."""
    try:
        cfg = load_config()
        recipients = get_recipients(cfg)
        remote_dir = args.remote or cfg.get("remote", "")
        if not remote_dir:
            print("Error: no remote directory configured.", file=sys.stderr)
            sys.exit(1)
        encrypted = encrypt_file(Path(args.file), recipients)
        dest = push(encrypted, remote_dir)
        print(f"Pushed {encrypted.name} → {dest}")
    except (ConfigError, GPGError, SyncError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_pull(args: argparse.Namespace) -> None:
    """Pull and decrypt .env from remote storage."""
    try:
        cfg = load_config()
        remote_dir = args.remote or cfg.get("remote", "")
        if not remote_dir:
            print("Error: no remote directory configured.", file=sys.stderr)
            sys.exit(1)
        filename = args.filename or ".env.gpg"
        local = pull(remote_dir, filename, local_dir=Path("."))
        out = decrypt_file(local, output=args.output)
        print(f"Pulled and decrypted → {out}")
    except (ConfigError, GPGError, SyncError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault", description="Encrypt and sync .env files.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialise envault in this directory.")
    p_init.add_argument("recipients", nargs="+", help="GPG key IDs or emails.")
    p_init.add_argument("--remote", default="", help="Remote directory for syncing.")
    p_init.set_defaults(func=cmd_init)

    p_enc = sub.add_parser("encrypt", help="Encrypt the .env file.")
    p_enc.add_argument("file", nargs="?", default=".env")
    p_enc.add_argument("--output", default=None)
    p_enc.set_defaults(func=cmd_encrypt)

    p_dec = sub.add_parser("decrypt", help="Decrypt the .env.gpg file.")
    p_dec.add_argument("file", nargs="?", default=".env.gpg")
    p_dec.add_argument("--output", default=None)
    p_dec.set_defaults(func=cmd_decrypt)

    p_push = sub.add_parser("push", help="Encrypt and push to remote.")
    p_push.add_argument("file", nargs="?", default=".env")
    p_push.add_argument("--remote", default=None)
    p_push.set_defaults(func=cmd_push)

    p_pull = sub.add_parser("pull", help="Pull and decrypt from remote.")
    p_pull.add_argument("--filename", default=None)
    p_pull.add_argument("--remote", default=None)
    p_pull.add_argument("--output", default=None)
    p_pull.set_defaults(func=cmd_pull)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
