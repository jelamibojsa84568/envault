"""Template support for envault — define required variable schemas for a vault."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class TemplateMissingVariableError(Exception):
    """Raised when required variables are absent from an env dict."""


class TemplateCorruptedError(Exception):
    """Raised when the template file cannot be parsed."""


def _template_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "template.json"


def _load(vault_dir: Path) -> Dict[str, dict]:
    path = _template_path(vault_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise TemplateCorruptedError(f"Template file is corrupted: {exc}") from exc


def _save(vault_dir: Path, data: Dict[str, dict]) -> None:
    path = _template_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def set_variable(
    vault_dir: Path,
    name: str,
    description: str = "",
    required: bool = True,
    default: Optional[str] = None,
) -> dict:
    """Add or update a variable definition in the template."""
    data = _load(vault_dir)
    entry = {"description": description, "required": required, "default": default}
    data[name] = entry
    _save(vault_dir, data)
    return entry


def remove_variable(vault_dir: Path, name: str) -> bool:
    """Remove a variable from the template. Returns True if it existed."""
    data = _load(vault_dir)
    if name not in data:
        return False
    del data[name]
    _save(vault_dir, data)
    return True


def get_template(vault_dir: Path) -> Dict[str, dict]:
    """Return the full template schema."""
    return _load(vault_dir)


def validate(vault_dir: Path, env: Dict[str, str]) -> List[str]:
    """Validate *env* against the template.

    Returns a list of missing required variable names.
    Raises TemplateMissingVariableError if any required variables are absent.
    """
    data = _load(vault_dir)
    missing = [
        name
        for name, meta in data.items()
        if meta.get("required", True) and name not in env and meta.get("default") is None
    ]
    if missing:
        raise TemplateMissingVariableError(
            "Missing required variables: " + ", ".join(sorted(missing))
        )
    return missing
