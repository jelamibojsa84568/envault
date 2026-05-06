"""Snapshot management — save and restore named snapshots of the vault state."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

SNAPSHOT_DIR = ".envault_snapshots"


class SnapshotNotFoundError(FileNotFoundError):
    """Raised when a requested snapshot does not exist."""


class SnapshotCorruptedError(ValueError):
    """Raised when a snapshot file cannot be parsed."""


def _snapshot_dir(vault_dir: str | Path) -> Path:
    return Path(vault_dir) / SNAPSHOT_DIR


def _snapshot_path(vault_dir: str | Path, name: str) -> Path:
    return _snapshot_dir(vault_dir) / f"{name}.json"


def save_snapshot(vault_dir: str | Path, name: str, ciphertext: str) -> Path:
    """Persist *ciphertext* as a named snapshot and return its path."""
    snap_dir = _snapshot_dir(vault_dir)
    snap_dir.mkdir(parents=True, exist_ok=True)
    path = _snapshot_path(vault_dir, name)
    payload = {
        "name": name,
        "ciphertext": ciphertext,
        "created_at": time.time(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_snapshot(vault_dir: str | Path, name: str) -> str:
    """Return the ciphertext stored in *name* snapshot."""
    path = _snapshot_path(vault_dir, name)
    if not path.exists():
        raise SnapshotNotFoundError(f"Snapshot '{name}' not found in {vault_dir}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["ciphertext"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise SnapshotCorruptedError(f"Snapshot '{name}' is corrupted: {exc}") from exc


def list_snapshots(vault_dir: str | Path) -> List[Dict]:
    """Return metadata for all snapshots, sorted newest-first."""
    snap_dir = _snapshot_dir(vault_dir)
    if not snap_dir.exists():
        return []
    entries = []
    for path in snap_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entries.append({"name": data["name"], "created_at": data["created_at"]})
        except (json.JSONDecodeError, KeyError):
            continue
    return sorted(entries, key=lambda e: e["created_at"], reverse=True)


def delete_snapshot(vault_dir: str | Path, name: str) -> bool:
    """Delete *name* snapshot.  Returns True if deleted, False if not found."""
    path = _snapshot_path(vault_dir, name)
    if not path.exists():
        return False
    path.unlink()
    return True
