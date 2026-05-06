"""Tag management for vault variables — group and filter env vars by tag."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set


class TagNotFoundError(Exception):
    """Raised when a referenced tag does not exist."""


class TagsCorruptedError(Exception):
    """Raised when the tags file cannot be parsed."""


def _tags_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "tags.json"


def _load(vault_dir: Path) -> Dict[str, List[str]]:
    """Return mapping of tag -> list of variable names."""
    path = _tags_path(vault_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise TagsCorruptedError(f"tags file is not valid JSON: {exc}") from exc


def _save(vault_dir: Path, data: Dict[str, List[str]]) -> None:
    path = _tags_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def add_tag(vault_dir: Path, tag: str, variables: List[str]) -> None:
    """Add *variables* to *tag*, creating the tag if necessary."""
    data = _load(vault_dir)
    existing: Set[str] = set(data.get(tag, []))
    existing.update(variables)
    data[tag] = sorted(existing)
    _save(vault_dir, data)


def remove_tag(vault_dir: Path, tag: str, variables: List[str]) -> List[str]:
    """Remove *variables* from *tag*. Returns variables that were actually removed."""
    data = _load(vault_dir)
    if tag not in data:
        raise TagNotFoundError(f"tag '{tag}' does not exist")
    before: Set[str] = set(data[tag])
    removed = list(before & set(variables))
    data[tag] = sorted(before - set(variables))
    if not data[tag]:
        del data[tag]
    _save(vault_dir, data)
    return removed


def list_tags(vault_dir: Path) -> Dict[str, List[str]]:
    """Return all tags and their associated variables."""
    return _load(vault_dir)


def variables_for_tag(vault_dir: Path, tag: str) -> List[str]:
    """Return variables associated with *tag*."""
    data = _load(vault_dir)
    if tag not in data:
        raise TagNotFoundError(f"tag '{tag}' does not exist")
    return data[tag]


def delete_tag(vault_dir: Path, tag: str) -> None:
    """Delete an entire tag entry."""
    data = _load(vault_dir)
    if tag not in data:
        raise TagNotFoundError(f"tag '{tag}' does not exist")
    del data[tag]
    _save(vault_dir, data)
