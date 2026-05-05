"""Diff utilities for comparing plaintext .env files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DiffError(Exception):
    """Raised when a diff operation fails."""


@dataclass
class EnvDiff:
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)


def _parse_env(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE pairs from env file text, ignoring comments and blanks."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)', line)
        if match:
            key, value = match.group(1), match.group(2)
            # Strip surrounding quotes if present
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            result[key] = value
    return result


def diff_env_texts(old_text: str, new_text: str) -> EnvDiff:
    """Return an EnvDiff comparing two env file contents."""
    old = _parse_env(old_text)
    new = _parse_env(new_text)

    result = EnvDiff()
    all_keys = set(old) | set(new)
    for key in all_keys:
        if key in new and key not in old:
            result.added[key] = new[key]
        elif key in old and key not in new:
            result.removed[key] = old[key]
        elif old[key] != new[key]:
            result.changed[key] = (old[key], new[key])
    return result


def diff_env_files(old_path: Path, new_path: Path) -> EnvDiff:
    """Return an EnvDiff comparing two env files on disk."""
    for p in (old_path, new_path):
        if not p.exists():
            raise DiffError(f"File not found: {p}")
    return diff_env_texts(old_path.read_text(), new_path.read_text())


def format_diff(diff: EnvDiff, redact: bool = True) -> List[str]:
    """Return a list of human-readable diff lines."""
    lines: List[str] = []
    for key in sorted(diff.added):
        val = "<redacted>" if redact else diff.added[key]
        lines.append(f"+ {key}={val}")
    for key in sorted(diff.removed):
        val = "<redacted>" if redact else diff.removed[key]
        lines.append(f"- {key}={val}")
    for key in sorted(diff.changed):
        old_val, new_val = diff.changed[key]
        if redact:
            lines.append(f"~ {key}: <redacted> -> <redacted>")
        else:
            lines.append(f"~ {key}: {old_val!r} -> {new_val!r}")
    return lines
