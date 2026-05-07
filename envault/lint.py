"""Lint .env files for common issues."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


class LintError(Exception):
    """Raised when linting cannot be performed."""


@dataclass
class LintIssue:
    line_number: int
    code: str
    message: str


@dataclass
class LintResult:
    path: Path
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')
_PAIR_RE = re.compile(r'^([^=]+)=(.*)$')


def _check_line(lineno: int, raw: str) -> List[LintIssue]:
    issues: List[LintIssue] = []
    line = raw.rstrip('\n')

    if not line or line.lstrip().startswith('#'):
        return issues

    if line != line.rstrip():
        issues.append(LintIssue(lineno, 'W001', 'Trailing whitespace'))

    m = _PAIR_RE.match(line)
    if not m:
        issues.append(LintIssue(lineno, 'E001', f'Not a valid KEY=VALUE pair: {line!r}'))
        return issues

    key, value = m.group(1), m.group(2)

    if not _KEY_RE.match(key):
        issues.append(LintIssue(lineno, 'W002', f'Key {key!r} is not UPPER_SNAKE_CASE'))

    if value.startswith('"') and not value.endswith('"'):
        issues.append(LintIssue(lineno, 'E002', 'Unmatched double quote in value'))

    if value.startswith("'") and not value.endswith("'"):
        issues.append(LintIssue(lineno, 'E003', 'Unmatched single quote in value'))

    if not value and not value == '':
        issues.append(LintIssue(lineno, 'W003', f'Key {key!r} has an empty value'))

    return issues


def lint_file(path: Path) -> LintResult:
    """Lint *path* and return a LintResult with any discovered issues."""
    if not path.exists():
        raise LintError(f'File not found: {path}')

    result = LintResult(path=path)
    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
    for lineno, raw in enumerate(lines, start=1):
        result.issues.extend(_check_line(lineno, raw))
    return result


def format_results(result: LintResult) -> str:
    """Return a human-readable summary of *result*."""
    if result.ok:
        return f'{result.path}: no issues found'
    lines = [f'{result.path}:']
    for issue in result.issues:
        lines.append(f'  line {issue.line_number}: [{issue.code}] {issue.message}')
    return '\n'.join(lines)
