"""Access control: manage per-user read/write permissions for a vault."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Set

ACCESS_FILENAME = ".envault_access.json"

VALID_ROLES = {"read", "write", "admin"}


class AccessDeniedError(PermissionError):
    """Raised when a user lacks the required role."""


class InvalidRoleError(ValueError):
    """Raised when an unknown role is specified."""


def _access_path(vault_dir: Path) -> Path:
    return vault_dir / ACCESS_FILENAME


def _load(vault_dir: Path) -> Dict[str, str]:
    path = _access_path(vault_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(vault_dir: Path, data: Dict[str, str]) -> None:
    _access_path(vault_dir).write_text(
        json.dumps(data, indent=2, sort_keys=True), encoding="utf-8"
    )


def grant(vault_dir: Path, username: str, role: str) -> None:
    """Grant *username* the given *role*. Overwrites any existing role."""
    if role not in VALID_ROLES:
        raise InvalidRoleError(f"Unknown role '{role}'. Valid roles: {VALID_ROLES}")
    data = _load(vault_dir)
    data[username] = role
    _save(vault_dir, data)


def revoke(vault_dir: Path, username: str) -> bool:
    """Remove *username* from the access list. Returns True if they existed."""
    data = _load(vault_dir)
    existed = username in data
    data.pop(username, None)
    _save(vault_dir, data)
    return existed


def get_role(vault_dir: Path, username: str) -> str | None:
    """Return the role for *username*, or None if not present."""
    return _load(vault_dir).get(username)


def require_role(vault_dir: Path, username: str, required_role: str) -> None:
    """Raise AccessDeniedError if *username* does not hold *required_role*.

    Role hierarchy: admin > write > read.
    """
    hierarchy = ["read", "write", "admin"]
    role = get_role(vault_dir, username)
    if role is None or hierarchy.index(role) < hierarchy.index(required_role):
        raise AccessDeniedError(
            f"User '{username}' requires role '{required_role}' but has '{role}'."
        )


def list_users(vault_dir: Path) -> Dict[str, str]:
    """Return a mapping of username -> role for all users."""
    return dict(_load(vault_dir))
