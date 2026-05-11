"""Vault locking mechanism to prevent concurrent writes."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

LOCK_FILENAME = ".envault.lock"
STALE_AFTER_SECONDS = 30


class LockError(Exception):
    """Raised when a vault lock cannot be acquired."""


class LockStalledError(LockError):
    """Raised when an existing lock appears stale."""


def _lock_path(vault_dir: Path) -> Path:
    return vault_dir / LOCK_FILENAME


def _read_lock(lock_file: Path) -> Optional[dict]:
    try:
        return json.loads(lock_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def acquire(vault_dir: Path, owner: str = "", timeout: float = 5.0) -> Path:
    """Acquire a lock on *vault_dir*.

    Polls until *timeout* seconds have elapsed.  Raises *LockError* if the
    lock cannot be obtained.  Raises *LockStalledError* if the existing lock
    is older than STALE_AFTER_SECONDS.
    """
    lock_file = _lock_path(vault_dir)
    owner = owner or str(os.getpid())
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if not lock_file.exists():
            payload = {"owner": owner, "acquired_at": time.time()}
            try:
                lock_file.write_text(json.dumps(payload))
                return lock_file
            except OSError:
                pass
        else:
            info = _read_lock(lock_file)
            if info:
                age = time.time() - info.get("acquired_at", 0)
                if age > STALE_AFTER_SECONDS:
                    raise LockStalledError(
                        f"Stale lock held by '{info.get('owner')}' "
                        f"for {age:.0f}s. Remove {lock_file} to continue."
                    )
        time.sleep(0.1)

    raise LockError(
        f"Could not acquire vault lock after {timeout}s. "
        "Another envault process may be running."
    )


def release(vault_dir: Path) -> bool:
    """Release the lock.  Returns True if the file was removed."""
    lock_file = _lock_path(vault_dir)
    try:
        lock_file.unlink()
        return True
    except FileNotFoundError:
        return False


def is_locked(vault_dir: Path) -> bool:
    """Return True if a lock file is present (regardless of staleness)."""
    return _lock_path(vault_dir).exists()
