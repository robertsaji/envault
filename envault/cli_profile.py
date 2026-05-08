"""CLI sub-commands for profile management."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envault.profile import ProfileError, delete_profile, get_profile, list_profiles, set_profile


def cmd_profile_list(args: Namespace) -> None:
    cfg = Path(args.config)
    names = list_profiles(cfg)
    if not names:
        print("No profiles defined.")
    else:
        for name in names:
            print(name)


def cmd_profile_set(args: Namespace) -> None:
    cfg = Path(args.config)
    try:
        overrides = json.loads(args.overrides)
    except json.JSONDecodeError as exc:
        print(f"error: overrides must be valid JSON — {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(overrides, dict):
        print("error: overrides must be a JSON object", file=sys.stderr)
        sys.exit(1)
    try:
        set_profile(cfg, args.name, overrides)
        print(f"Profile '{args.name}' saved.")
    except ProfileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_profile_show(args: Namespace) -> None:
    cfg = Path(args.config)
    try:
        overrides = get_profile(cfg, args.name)
        print(json.dumps(overrides, indent=2))
    except ProfileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_profile_delete(args: Namespace) -> None:
    cfg = Path(args.config)
    try:
        delete_profile(cfg, args.name)
        print(f"Profile '{args.name}' deleted.")
    except ProfileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def register_profile_subcommands(sub: ArgumentParser) -> None:
    p = sub.add_parser("profile", help="Manage named config profiles")
    ps = p.add_subparsers(dest="profile_cmd", required=True)

    ps.add_parser("list", help="List all profiles").set_defaults(func=cmd_profile_list)

    p_set = ps.add_parser("set", help="Create or update a profile")
    p_set.add_argument("name", help="Profile name")
    p_set.add_argument("overrides", help='JSON object of key/value overrides, e.g. \'{"ENV":"prod"}\'"')
    p_set.set_defaults(func=cmd_profile_set)

    p_show = ps.add_parser("show", help="Show a profile's overrides")
    p_show.add_argument("name", help="Profile name")
    p_show.set_defaults(func=cmd_profile_show)

    p_del = ps.add_parser("delete", help="Delete a profile")
    p_del.add_argument("name", help="Profile name")
    p_del.set_defaults(func=cmd_profile_delete)
