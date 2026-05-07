"""Export decrypted .env contents to various formats (shell, JSON, Docker)."""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Dict, Literal

ExportFormat = Literal["shell", "json", "docker"]


class ExportError(Exception):
    """Raised when an export operation fails."""


def _parse_env(text: str) -> Dict[str, str]:
    """Parse key=value pairs from env text, ignoring comments and blanks."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def export_env(
    source: Path,
    fmt: ExportFormat = "shell",
    export_keyword: bool = True,
) -> str:
    """Read a plaintext .env file and render it in *fmt* format.

    Args:
        source: Path to the plaintext .env file.
        fmt: Output format — ``shell``, ``json``, or ``docker``.
        export_keyword: When ``fmt='shell'``, prefix each line with ``export``.

    Returns:
        Rendered string ready to be written or printed.

    Raises:
        ExportError: If the source file is missing or the format is unknown.
    """
    if not source.exists():
        raise ExportError(f"Source file not found: {source}")

    text = source.read_text(encoding="utf-8")
    pairs = _parse_env(text)

    if fmt == "shell":
        lines = []
        for k, v in pairs.items():
            safe_v = shlex.quote(v)
            prefix = "export " if export_keyword else ""
            lines.append(f"{prefix}{k}={safe_v}")
        return "\n".join(lines)

    if fmt == "json":
        return json.dumps(pairs, indent=2)

    if fmt == "docker":
        # Docker --env-file format: KEY=VALUE, no quoting
        return "\n".join(f"{k}={v}" for k, v in pairs.items())

    raise ExportError(f"Unknown export format: {fmt!r}")
