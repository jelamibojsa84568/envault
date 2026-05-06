"""Pre/post hook support for push and pull operations."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional

HOOKS_FILENAME = ".envault-hooks.json"


class HookError(Exception):
    """Raised when a hook script exits with a non-zero status."""


def _hooks_path(vault_dir: Path) -> Path:
    return vault_dir / HOOKS_FILENAME


def _load(vault_dir: Path) -> dict:
    path = _hooks_path(vault_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise HookError(f"Hooks file is corrupted: {exc}") from exc


def _save(vault_dir: Path, data: dict) -> None:
    _hooks_path(vault_dir).write_text(json.dumps(data, indent=2))


def set_hook(vault_dir: Path, event: str, command: str) -> None:
    """Register *command* for *event* (e.g. 'pre-push', 'post-pull')."""
    valid_events = {"pre-push", "post-push", "pre-pull", "post-pull"}
    if event not in valid_events:
        raise HookError(f"Unknown event '{event}'. Valid events: {sorted(valid_events)}")
    data = _load(vault_dir)
    data[event] = command
    _save(vault_dir, data)


def remove_hook(vault_dir: Path, event: str) -> bool:
    """Remove hook for *event*. Returns True if it existed."""
    data = _load(vault_dir)
    if event not in data:
        return False
    del data[event]
    _save(vault_dir, data)
    return True


def get_hooks(vault_dir: Path) -> dict:
    """Return all registered hooks as {event: command}."""
    return _load(vault_dir)


def run_hook(vault_dir: Path, event: str) -> Optional[str]:
    """Run the hook for *event* if one is registered.

    Returns the combined stdout+stderr output, or None if no hook is set.
    Raises HookError if the command exits non-zero.
    """
    data = _load(vault_dir)
    command = data.get(event)
    if command is None:
        return None
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(vault_dir),
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise HookError(
            f"Hook '{event}' failed (exit {result.returncode}): {output}"
        )
    return output
