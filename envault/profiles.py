"""Profile management for envault — allows multiple named vaults (e.g. dev, staging, prod)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

PROFILES_FILENAME = ".envault_profiles.json"
DEFAULT_PROFILE = "default"


class ProfileNotFoundError(KeyError):
    """Raised when a requested profile does not exist."""


class ProfilesCorruptedError(ValueError):
    """Raised when the profiles file cannot be parsed."""


def _profiles_path(vault_dir: Path) -> Path:
    return vault_dir / PROFILES_FILENAME


def _load(vault_dir: Path) -> Dict[str, str]:
    path = _profiles_path(vault_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            raise ProfilesCorruptedError("Profiles file must contain a JSON object.")
        return data
    except json.JSONDecodeError as exc:
        raise ProfilesCorruptedError(f"Profiles file is not valid JSON: {exc}") from exc


def _save(vault_dir: Path, profiles: Dict[str, str]) -> None:
    _profiles_path(vault_dir).write_text(json.dumps(profiles, indent=2))


def set_profile(vault_dir: Path, name: str, vault_file: str) -> None:
    """Register or update a profile, mapping *name* to a vault filename."""
    profiles = _load(vault_dir)
    profiles[name] = vault_file
    _save(vault_dir, profiles)


def remove_profile(vault_dir: Path, name: str) -> bool:
    """Remove a profile by name.  Returns True if it existed, False otherwise."""
    profiles = _load(vault_dir)
    if name not in profiles:
        return False
    del profiles[name]
    _save(vault_dir, profiles)
    return True


def get_profile(vault_dir: Path, name: str) -> str:
    """Return the vault filename for *name*, raising ProfileNotFoundError if absent."""
    profiles = _load(vault_dir)
    if name not in profiles:
        raise ProfileNotFoundError(f"Profile '{name}' does not exist.")
    return profiles[name]


def list_profiles(vault_dir: Path) -> List[str]:
    """Return a sorted list of all profile names."""
    return sorted(_load(vault_dir).keys())


def active_profile(vault_dir: Path) -> Optional[str]:
    """Return the name stored in the '.active_profile' sentinel file, or None."""
    sentinel = vault_dir / ".active_profile"
    if sentinel.exists():
        return sentinel.read_text().strip() or None
    return None


def set_active_profile(vault_dir: Path, name: str) -> None:
    """Persist *name* as the currently active profile."""
    profiles = _load(vault_dir)
    if name not in profiles:
        raise ProfileNotFoundError(f"Profile '{name}' does not exist.")
    (vault_dir / ".active_profile").write_text(name)
