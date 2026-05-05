"""CLI commands for verifying and signing encrypted .env files."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envault.verify import VerifyError, sign_file, verify_signature


def cmd_verify(args: Namespace) -> None:
    """Verify the GPG signature of an encrypted file."""
    encrypted = Path(args.file)
    sig = Path(args.signature) if args.signature else None

    try:
        result = verify_signature(encrypted, sig)
    except VerifyError as exc:
        print(f"[envault] verify error: {exc}", file=sys.stderr)
        sys.exit(1)

    if result["valid"]:
        signer = result["signer"] or "unknown"
        fp = result["fingerprint"] or "n/a"
        print(f"[envault] signature valid — signer: {signer} (fingerprint: {fp})")
    else:
        print("[envault] signature INVALID or missing", file=sys.stderr)
        if result["message"]:
            print(result["message"], file=sys.stderr)
        sys.exit(2)


def cmd_sign(args: Namespace) -> None:
    """Create a detached GPG signature for an encrypted file."""
    source = Path(args.file)
    output = Path(args.output) if args.output else None

    try:
        sig_path = sign_file(source, output)
    except VerifyError as exc:
        print(f"[envault] sign error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[envault] signed: {sig_path}")


def register_verify_subcommands(sub: ArgumentParser) -> None:  # type: ignore[type-arg]
    """Attach *verify* and *sign* sub-commands to *sub*."""
    p_verify = sub.add_parser("verify", help="verify GPG signature of an encrypted file")
    p_verify.add_argument("file", help="path to the encrypted .env file")
    p_verify.add_argument("--signature", "-s", default=None, help="path to detached .sig file")
    p_verify.set_defaults(func=cmd_verify)

    p_sign = sub.add_parser("sign", help="create a detached GPG signature for an encrypted file")
    p_sign.add_argument("file", help="path to the encrypted .env file")
    p_sign.add_argument("--output", "-o", default=None, help="path for the output .sig file")
    p_sign.set_defaults(func=cmd_sign)
