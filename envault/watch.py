"""Watch a .env file for changes and re-encrypt automatically."""

from __future__ import annotations

import time
import os
from pathlib import Path
from typing import Callable, Optional


class WatchError(Exception):
    """Raised when the watcher encounters an unrecoverable error."""


def _mtime(path: Path) -> float:
    """Return the modification time of *path*, or -1 if it does not exist."""
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return -1.0


def watch(
    source: Path,
    on_change: Callable[[Path], None],
    *,
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *source* every *interval* seconds and call *on_change* when it changes.

    Parameters
    ----------
    source:
        Path to the plaintext .env file to watch.
    on_change:
        Callback invoked with *source* whenever a change is detected.
    interval:
        Polling interval in seconds.
    max_iterations:
        If set, stop after this many polling iterations (useful for tests).
    """
    if not source.exists():
        raise WatchError(f"Source file not found: {source}")

    last_mtime = _mtime(source)
    iterations = 0

    while True:
        time.sleep(interval)
        iterations += 1

        current_mtime = _mtime(source)
        if current_mtime != last_mtime:
            last_mtime = current_mtime
            on_change(source)

        if max_iterations is not None and iterations >= max_iterations:
            break
