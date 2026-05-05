"""Audit log for vault operations — records who did what and when."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

AUDIT_FILENAME = ".envault_audit.json"


def _audit_path(vault_dir: str | Path | None = None) -> Path:
    base = Path(vault_dir) if vault_dir else Path.cwd()
    return base / AUDIT_FILENAME


def _load_entries(vault_dir: str | Path | None = None) -> List[Dict[str, Any]]:
    path = _audit_path(vault_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return data
    except (json.JSONDecodeError, OSError):
        return []


def record(
    action: str,
    user: str | None = None,
    details: Dict[str, Any] | None = None,
    vault_dir: str | Path | None = None,
) -> Dict[str, Any]:
    """Append an audit entry and return it."""
    entry: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "user": user or os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
    }
    if details:
        entry["details"] = details

    entries = _load_entries(vault_dir)
    entries.append(entry)

    path = _audit_path(vault_dir)
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return entry


def get_log(vault_dir: str | Path | None = None) -> List[Dict[str, Any]]:
    """Return all audit entries, oldest first."""
    return _load_entries(vault_dir)


def clear_log(vault_dir: str | Path | None = None) -> None:
    """Remove the audit log file entirely."""
    path = _audit_path(vault_dir)
    if path.exists():
        path.unlink()
