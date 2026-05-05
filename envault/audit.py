"""Audit log for envault — records encrypt/decrypt/push/pull events."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

AUDIT_FILENAME = ".envault_audit.jsonl"


class AuditError(Exception):
    """Raised when the audit log cannot be read or written."""


def _audit_path(directory: str | Path | None = None) -> Path:
    base = Path(directory) if directory else Path.cwd()
    return base / AUDIT_FILENAME


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_event(
    action: str,
    target: str,
    actor: str | None = None,
    extra: Dict[str, Any] | None = None,
    directory: str | Path | None = None,
) -> Dict[str, Any]:
    """Append a single audit event to the JSONL log and return it."""
    entry: Dict[str, Any] = {
        "timestamp": _now_iso(),
        "action": action,
        "target": str(target),
        "actor": actor or os.environ.get("USER", "unknown"),
    }
    if extra:
        entry.update(extra)

    path = _audit_path(directory)
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError as exc:
        raise AuditError(f"Cannot write audit log '{path}': {exc}") from exc

    return entry


def load_events(
    directory: str | Path | None = None,
) -> List[Dict[str, Any]]:
    """Return all audit events from the JSONL log (oldest first)."""
    path = _audit_path(directory)
    if not path.exists():
        return []
    events: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise AuditError(
                        f"Corrupt audit log at line {lineno}: {exc}"
                    ) from exc
    except OSError as exc:
        raise AuditError(f"Cannot read audit log '{path}': {exc}") from exc
    return events
