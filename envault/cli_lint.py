"""CLI commands for .env linting."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envault.lint import LintError, format_results, lint_file


def cmd_lint(args: Namespace) -> None:
    """Lint one or more .env files and report issues."""
    paths = [Path(p) for p in args.files] if args.files else [Path('.env')]
    exit_code = 0

    for path in paths:
        try:
            result = lint_file(path)
        except LintError as exc:
            print(f'envault lint: {exc}', file=sys.stderr)
            sys.exit(1)

        print(format_results(result))

        if not result.ok:
            exit_code = 1
            if args.summary:
                print(
                    f'  {len(result.issues)} issue(s) found in {path}',
                    file=sys.stderr,
                )

    sys.exit(exit_code)


def register_lint_subcommands(subparsers) -> None:  # type: ignore[type-arg]
    """Attach the *lint* subcommand to *subparsers*."""
    p: ArgumentParser = subparsers.add_parser(
        'lint',
        help='Check .env files for common issues',
    )
    p.add_argument(
        'files',
        nargs='*',
        metavar='FILE',
        help='One or more .env files to lint (default: .env)',
    )
    p.add_argument(
        '--summary',
        action='store_true',
        help='Print a summary line for each file with issues',
    )
    p.set_defaults(func=cmd_lint)
