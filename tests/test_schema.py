"""Tests for envault/schema.py"""

import pytest
from pathlib import Path
import json

from envault.schema import (
    set_field,
    remove_field,
    get_schema,
    validate,
    FieldSchema,
    SchemaCorruptedError,
)


@pytest.fixture
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_set_field_creates_schema_file(vault_dir):
    set_field(vault_dir, "DATABASE_URL", required=True)
    schema_file = vault_dir / ".envault" / "schema.json"
    assert schema_file.exists()


def test_set_field_stores_required_flag(vault_dir):
    set_field(vault_dir, "API_KEY", required=True)
    schema = get_schema(vault_dir)
    assert schema["API_KEY"].required is True


def test_set_field_stores_pattern(vault_dir):
    set_field(vault_dir, "PORT", pattern=r"\d+")
    schema = get_schema(vault_dir)
    assert schema["PORT"].pattern == r"\d+"


def test_set_field_stores_allowed_values(vault_dir):
    set_field(vault_dir, "ENV", allowed_values=["dev", "staging", "prod"])
    schema = get_schema(vault_dir)
    assert schema["ENV"].allowed_values == ["dev", "staging", "prod"]


def test_set_field_stores_description(vault_dir):
    set_field(vault_dir, "SECRET", description="App secret key")
    schema = get_schema(vault_dir)
    assert schema["SECRET"].description == "App secret key"


def test_set_field_overwrites_existing(vault_dir):
    set_field(vault_dir, "PORT", pattern=r"\d+")
    set_field(vault_dir, "PORT", pattern=r"[0-9]{4,5}")
    schema = get_schema(vault_dir)
    assert schema["PORT"].pattern == r"[0-9]{4,5}"


def test_remove_field_returns_true(vault_dir):
    set_field(vault_dir, "TEMP", required=False)
    assert remove_field(vault_dir, "TEMP") is True


def test_remove_field_returns_false_when_missing(vault_dir):
    assert remove_field(vault_dir, "NONEXISTENT") is False


def test_remove_field_deletes_entry(vault_dir):
    set_field(vault_dir, "GONE", required=True)
    remove_field(vault_dir, "GONE")
    schema = get_schema(vault_dir)
    assert "GONE" not in schema


def test_validate_passes_clean_env(vault_dir):
    set_field(vault_dir, "DB_URL", required=True)
    result = validate(vault_dir, {"DB_URL": "postgres://localhost/db"})
    assert result.ok
    assert result.errors() == []


def test_validate_missing_required_key_is_error(vault_dir):
    set_field(vault_dir, "API_KEY", required=True)
    result = validate(vault_dir, {})
    assert not result.ok
    assert any(i.key == "API_KEY" for i in result.errors())


def test_validate_pattern_mismatch_is_error(vault_dir):
    set_field(vault_dir, "PORT", pattern=r"\d+")
    result = validate(vault_dir, {"PORT": "not-a-number"})
    assert not result.ok


def test_validate_pattern_match_passes(vault_dir):
    set_field(vault_dir, "PORT", pattern=r"\d+")
    result = validate(vault_dir, {"PORT": "8080"})
    assert result.ok


def test_validate_allowed_values_violation_is_error(vault_dir):
    set_field(vault_dir, "ENV", allowed_values=["dev", "prod"])
    result = validate(vault_dir, {"ENV": "test"})
    assert not result.ok
    assert any(i.key == "ENV" for i in result.errors())


def test_validate_allowed_values_passes(vault_dir):
    set_field(vault_dir, "ENV", allowed_values=["dev", "prod"])
    result = validate(vault_dir, {"ENV": "prod"})
    assert result.ok


def test_corrupted_schema_raises(vault_dir):
    schema_file = vault_dir / ".envault" / "schema.json"
    schema_file.parent.mkdir(parents=True, exist_ok=True)
    schema_file.write_text("{invalid json")
    with pytest.raises(SchemaCorruptedError):
        get_schema(vault_dir)


def test_get_schema_empty_when_no_file(vault_dir):
    schema = get_schema(vault_dir)
    assert schema == {}
