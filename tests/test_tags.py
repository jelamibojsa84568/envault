"""Tests for envault.tags module."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.tags import (
    add_tag,
    remove_tag,
    list_tags,
    variables_for_tag,
    delete_tag,
    TagNotFoundError,
    TagsCorruptedError,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_add_tag_creates_entry(vault_dir):
    add_tag(vault_dir, "backend", ["DB_URL", "SECRET_KEY"])
    data = list_tags(vault_dir)
    assert "backend" in data
    assert "DB_URL" in data["backend"]
    assert "SECRET_KEY" in data["backend"]


def test_add_tag_deduplicates_variables(vault_dir):
    add_tag(vault_dir, "backend", ["DB_URL"])
    add_tag(vault_dir, "backend", ["DB_URL", "PORT"])
    data = list_tags(vault_dir)
    assert data["backend"].count("DB_URL") == 1


def test_add_tag_merges_with_existing(vault_dir):
    add_tag(vault_dir, "infra", ["AWS_KEY"])
    add_tag(vault_dir, "infra", ["AWS_SECRET"])
    assert set(list_tags(vault_dir)["infra"]) == {"AWS_KEY", "AWS_SECRET"}


def test_remove_tag_returns_removed_variables(vault_dir):
    add_tag(vault_dir, "frontend", ["API_URL", "CDN_URL"])
    removed = remove_tag(vault_dir, "frontend", ["API_URL"])
    assert removed == ["API_URL"]
    assert "API_URL" not in list_tags(vault_dir)["frontend"]


def test_remove_tag_deletes_empty_tag(vault_dir):
    add_tag(vault_dir, "solo", ["ONLY_VAR"])
    remove_tag(vault_dir, "solo", ["ONLY_VAR"])
    assert "solo" not in list_tags(vault_dir)


def test_remove_tag_raises_when_tag_missing(vault_dir):
    with pytest.raises(TagNotFoundError):
        remove_tag(vault_dir, "nonexistent", ["X"])


def test_variables_for_tag_returns_list(vault_dir):
    add_tag(vault_dir, "db", ["DB_HOST", "DB_PORT"])
    result = variables_for_tag(vault_dir, "db")
    assert set(result) == {"DB_HOST", "DB_PORT"}


def test_variables_for_tag_raises_when_missing(vault_dir):
    with pytest.raises(TagNotFoundError):
        variables_for_tag(vault_dir, "missing")


def test_delete_tag_removes_entry(vault_dir):
    add_tag(vault_dir, "temp", ["FOO"])
    delete_tag(vault_dir, "temp")
    assert "temp" not in list_tags(vault_dir)


def test_delete_tag_raises_when_missing(vault_dir):
    with pytest.raises(TagNotFoundError):
        delete_tag(vault_dir, "ghost")


def test_corrupted_tags_file_raises(vault_dir):
    tags_path = vault_dir / ".envault" / "tags.json"
    tags_path.parent.mkdir(parents=True, exist_ok=True)
    tags_path.write_text("not valid json{{")
    with pytest.raises(TagsCorruptedError):
        list_tags(vault_dir)
