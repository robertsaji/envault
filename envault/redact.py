"""Redaction helpers for .env values — masks sensitive data before display."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = ["RedactError", "RedactResult", "redact_env_text", "redact_dict"]

# Keys whose values are always fully masked regardless of pattern matching
_SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth)"),
]

_MASK = "********"


class RedactError(Exception):
    """Raised when redaction cannot be performed."""


@dataclass
class RedactResult:
    original_count: int = 0
    redacted_count: int = 0
    lines: List[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def _is_sensitive(key: str) -> bool:
    return any(p.search(key) for p in _SENSITIVE_PATTERNS)


def _mask_value(value: str, reveal_chars: int = 0) -> str:
    """Return masked value, optionally revealing the last *reveal_chars* characters."""
    if not value:
        return value
    if reveal_chars <= 0 or reveal_chars >= len(value):
        return _MASK
    return _MASK + value[-reveal_chars:]


def redact_env_text(
    text: str,
    *,
    reveal_chars: int = 0,
    extra_keys: Optional[List[str]] = None,
) -> RedactResult:
    """Parse *text* as .env content and redact sensitive values.

    Parameters
    ----------
    text:
        Raw .env file contents.
    reveal_chars:
        How many trailing characters of a sensitive value to leave visible.
    extra_keys:
        Additional key names (case-insensitive) to treat as sensitive.
    """
    extra_keys_lower = {k.lower() for k in (extra_keys or [])}
    result = RedactResult()

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            result.lines.append(raw_line)
            continue

        if "=" not in stripped:
            result.lines.append(raw_line)
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        result.original_count += 1

        if _is_sensitive(key) or key.lower() in extra_keys_lower:
            result.redacted_count += 1
            result.lines.append(f"{key}={_mask_value(value, reveal_chars)}")
        else:
            result.lines.append(f"{key}={value}")

    return result


def redact_dict(
    env: Dict[str, str],
    *,
    reveal_chars: int = 0,
    extra_keys: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values masked."""
    extra_keys_lower = {k.lower() for k in (extra_keys or [])}
    out: Dict[str, str] = {}
    for key, value in env.items():
        if _is_sensitive(key) or key.lower() in extra_keys_lower:
            out[key] = _mask_value(value, reveal_chars)
        else:
            out[key] = value
    return out
