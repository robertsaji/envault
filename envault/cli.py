"""Command-line interface for envault."""

import argparse
import sys
import os

from envault.crypto import encrypt_file, decrypt_file, GPGError
from envault.config import (
    load_config,
    save_config,
    init_config,
    get_recipients,
    ConfigError,
    DEFAULT_CONFIG_FILE,
)


def cmd_init(args: argparse.Namespace) -> int:
    if os.path.exists(DEFAULT_CONFIG_FILE) and not args.force:
        print(f"'{DEFAULT_CONFIG_FILE}' already exists. Use --force to overwrite.")
        return 1
    config = init_config(env_file=args.env_file, recipients=args.recipients)
    save_config(config)
    print(f"Initialized envault config at '{DEFAULT_CONFIG_FILE}'.")
    return 0


def cmd_encrypt(args: argparse.Namespace) -> int:
    try:
        config = load_config()
        recipients = get_recipients(config)
        env_file = config["envault"]["env_file"]
        encrypted_file = config["envault"]["encrypted_file"]
        out = encrypt_file(env_file, recipients, encrypted_file)
        print(f"Encrypted '{env_file}' -> '{out}'")
        return 0
    except (GPGError, ConfigError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_decrypt(args: argparse.Namespace) -> int:
    try:
        config = load_config()
        encrypted_file = config["envault"]["encrypted_file"]
        env_file = config["envault"]["env_file"]
        out = decrypt_file(encrypted_file, env_file)
        print(f"Decrypted '{encrypted_file}' -> '{out}'")
        return 0
    except (GPGError, ConfigError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Encrypt and sync .env files using GPG keys.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize envault in the current directory.")
    p_init.add_argument("--env-file", default=".env", help="Path to the .env file.")
    p_init.add_argument("--recipients", nargs="*", default=[], help="GPG key IDs or emails.")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing config.")

    sub.add_parser("encrypt", help="Encrypt the .env file for all configured recipients.")
    sub.add_parser("decrypt", help="Decrypt the .env.gpg file.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handlers = {"init": cmd_init, "encrypt": cmd_encrypt, "decrypt": cmd_decrypt}
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":
    main()
