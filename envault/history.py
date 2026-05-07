"""Vault push/pull history tracking."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

MAX_HISTORY_ENTRIES = 100


class HistoryCorruptedError(Exception):
    """Raised when the history file cannot be parsed."""


def _history_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "history.json"


def _load(vault_dir: Path) -> list[dict[str, Any]]:
    path = _history_path(vault_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, list):
            raise HistoryCorruptedError("history.json must contain a JSON array")
        return data
    except json.JSONDecodeError as exc:
        raise HistoryCorruptedError(f"history.json is not valid JSON: {exc}") from exc


def _save(vault_dir: Path, entries: list[dict[str, Any]]) -> None:
    path = _history_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def record(
    vault_dir: Path,
    action: str,
    user: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a history entry and return it.

    *action* should be ``"push"`` or ``"pull"``.
    Older entries beyond MAX_HISTORY_ENTRIES are pruned automatically.
    """
    if action not in {"push", "pull"}:
        raise ValueError(f"Invalid action {action!r}; expected 'push' or 'pull'")

    entry: dict[str, Any] = {
        "action": action,
        "user": user,
        "timestamp": time.time(),
        "details": details or {},
    }
    entries = _load(vault_dir)
    entries.append(entry)
    # Keep only the most recent entries
    entries = entries[-MAX_HISTORY_ENTRIES:]
    _save(vault_dir, entries)
    return entry


def get_history(
    vault_dir: Path,
    action: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return history entries, optionally filtered by *action* and capped by *limit*."""
    entries = _load(vault_dir)
    if action is not None:
        entries = [e for e in entries if e.get("action") == action]
    if limit is not None:
        entries = entries[-limit:]
    return entries


def clear_history(vault_dir: Path) -> None:
    """Remove all history entries."""
    _save(vault_dir, [])
