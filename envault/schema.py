"""Schema validation for .env variable definitions.

Allows teams to declare expected types, patterns, and requirements
for environment variables, then validate an env dict against them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class SchemaNotFoundError(FileNotFoundError):
    pass


class SchemaCorruptedError(ValueError):
    pass


@dataclass
class FieldSchema:
    required: bool = True
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    description: str = ""


@dataclass
class ValidationIssue:
    key: str
    message: str
    level: str  # "error" | "warning"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]


def _schema_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "schema.json"


def _load(vault_dir: Path) -> Dict[str, FieldSchema]:
    path = _schema_path(vault_dir)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
        return {
            k: FieldSchema(**{fk: fv for fk, fv in v.items() if fk in FieldSchema.__dataclass_fields__})
            for k, v in raw.items()
        }
    except Exception as exc:
        raise SchemaCorruptedError(f"schema.json is corrupted: {exc}") from exc


def _save(vault_dir: Path, schema: Dict[str, FieldSchema]) -> None:
    path = _schema_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialised = {
        k: {
            "required": v.required,
            "pattern": v.pattern,
            "allowed_values": v.allowed_values,
            "description": v.description,
        }
        for k, v in schema.items()
    }
    path.write_text(json.dumps(serialised, indent=2))


def set_field(vault_dir: Path, key: str, **kwargs) -> FieldSchema:
    schema = _load(vault_dir)
    existing = schema.get(key, FieldSchema())
    for attr, val in kwargs.items():
        if hasattr(existing, attr):
            setattr(existing, attr, val)
    schema[key] = existing
    _save(vault_dir, schema)
    return existing


def remove_field(vault_dir: Path, key: str) -> bool:
    schema = _load(vault_dir)
    if key not in schema:
        return False
    del schema[key]
    _save(vault_dir, schema)
    return True


def get_schema(vault_dir: Path) -> Dict[str, FieldSchema]:
    return _load(vault_dir)


def validate(vault_dir: Path, env: Dict[str, str]) -> ValidationResult:
    schema = _load(vault_dir)
    result = ValidationResult()
    for key, field_schema in schema.items():
        if field_schema.required and key not in env:
            result.issues.append(ValidationIssue(key, f"Required variable '{key}' is missing.", "error"))
            continue
        if key not in env:
            continue
        value = env[key]
        if field_schema.pattern and not re.fullmatch(field_schema.pattern, value):
            result.issues.append(ValidationIssue(key, f"Value for '{key}' does not match pattern '{field_schema.pattern}'.", "error"))
        if field_schema.allowed_values is not None and value not in field_schema.allowed_values:
            result.issues.append(ValidationIssue(key, f"Value '{value}' for '{key}' is not in allowed values.", "error"))
    return result
