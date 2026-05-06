"""Tests for envault.templates."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.templates import (
    set_variable,
    remove_variable,
    get_template,
    validate,
    TemplateMissingVariableError,
    TemplateCorruptedError,
    _template_path,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_set_variable_creates_file(vault_dir):
    set_variable(vault_dir, "DATABASE_URL", description="Postgres DSN", required=True)
    assert _template_path(vault_dir).exists()


def test_set_variable_stores_fields(vault_dir):
    entry = set_variable(vault_dir, "API_KEY", description="Third-party key", required=True)
    assert entry["description"] == "Third-party key"
    assert entry["required"] is True
    assert entry["default"] is None


def test_set_variable_with_default(vault_dir):
    set_variable(vault_dir, "LOG_LEVEL", description="", required=False, default="INFO")
    tmpl = get_template(vault_dir)
    assert tmpl["LOG_LEVEL"]["default"] == "INFO"


def test_set_variable_overwrites_existing(vault_dir):
    set_variable(vault_dir, "PORT", description="old", required=True)
    set_variable(vault_dir, "PORT", description="new", required=False)
    tmpl = get_template(vault_dir)
    assert tmpl["PORT"]["description"] == "new"
    assert tmpl["PORT"]["required"] is False


def test_remove_variable_returns_true(vault_dir):
    set_variable(vault_dir, "SECRET", required=True)
    assert remove_variable(vault_dir, "SECRET") is True


def test_remove_variable_absent_returns_false(vault_dir):
    assert remove_variable(vault_dir, "NONEXISTENT") is False


def test_remove_variable_deletes_entry(vault_dir):
    set_variable(vault_dir, "TOKEN", required=True)
    remove_variable(vault_dir, "TOKEN")
    assert "TOKEN" not in get_template(vault_dir)


def test_get_template_empty_when_no_file(vault_dir):
    assert get_template(vault_dir) == {}


def test_validate_passes_when_all_present(vault_dir):
    set_variable(vault_dir, "DB_URL", required=True)
    missing = validate(vault_dir, {"DB_URL": "postgres://localhost/db"})
    assert missing == []


def test_validate_raises_on_missing_required(vault_dir):
    set_variable(vault_dir, "SECRET_KEY", required=True)
    with pytest.raises(TemplateMissingVariableError, match="SECRET_KEY"):
        validate(vault_dir, {})


def test_validate_optional_variable_not_required(vault_dir):
    set_variable(vault_dir, "DEBUG", required=False)
    missing = validate(vault_dir, {})
    assert missing == []


def test_validate_default_satisfies_requirement(vault_dir):
    set_variable(vault_dir, "TIMEOUT", required=True, default="30")
    missing = validate(vault_dir, {})
    assert missing == []


def test_corrupted_template_raises(vault_dir):
    path = _template_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not valid json{{{")
    with pytest.raises(TemplateCorruptedError):
        get_template(vault_dir)
