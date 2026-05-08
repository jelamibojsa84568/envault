"""File-system watcher that triggers push/pull on .env changes."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Callable, Optional


class WatchError(Exception):
    """Raised when the watcher encounters an unrecoverable error."""


def _file_hash(path: Path) -> Optional[str]:
    """Return the MD5 hex-digest of *path*, or None if the file is missing."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def watch(
    env_path: Path,
    on_change: Callable[[Path], None],
    *,
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *env_path* every *interval* seconds and call *on_change* when its
    content changes.

    Parameters
    ----------
    env_path:       Path to the .env file to monitor.
    on_change:      Callback invoked with the changed path.
    interval:       Polling interval in seconds (default 1.0).
    max_iterations: Stop after this many poll cycles (None = run forever).
                    Useful for testing.
    """
    if not env_path.exists():
        raise WatchError(f"File not found: {env_path}")

    last_hash = _file_hash(env_path)
    iterations = 0

    while max_iterations is None or iterations < max_iterations:
        time.sleep(interval)
        current_hash = _file_hash(env_path)
        if current_hash != last_hash:
            last_hash = current_hash
            on_change(env_path)
        iterations += 1
