"""Tests for envault.history."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.history import (
    HistoryCorruptedError,
    MAX_HISTORY_ENTRIES,
    _history_path,
    clear_history,
    get_history,
    record,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_record_creates_history_file(vault_dir):
    record(vault_dir, "push", "alice")
    assert _history_path(vault_dir).exists()


def test_record_returns_entry_with_expected_keys(vault_dir):
    entry = record(vault_dir, "push", "alice")
    assert set(entry.keys()) == {"action", "user", "timestamp", "details"}


def test_record_stores_action_and_user(vault_dir):
    entry = record(vault_dir, "pull", "bob")
    assert entry["action"] == "pull"
    assert entry["user"] == "bob"


def test_record_stores_details(vault_dir):
    entry = record(vault_dir, "push", "alice", details={"keys_changed": 3})
    assert entry["details"]["keys_changed"] == 3


def test_record_appends_multiple_entries(vault_dir):
    record(vault_dir, "push", "alice")
    record(vault_dir, "pull", "bob")
    entries = get_history(vault_dir)
    assert len(entries) == 2


def test_record_invalid_action_raises(vault_dir):
    with pytest.raises(ValueError, match="Invalid action"):
        record(vault_dir, "delete", "alice")


def test_get_history_filter_by_action(vault_dir):
    record(vault_dir, "push", "alice")
    record(vault_dir, "pull", "bob")
    record(vault_dir, "push", "carol")
    pushes = get_history(vault_dir, action="push")
    assert all(e["action"] == "push" for e in pushes)
    assert len(pushes) == 2


def test_get_history_limit(vault_dir):
    for i in range(5):
        record(vault_dir, "push", f"user{i}")
    entries = get_history(vault_dir, limit=3)
    assert len(entries) == 3


def test_get_history_empty_returns_empty_list(vault_dir):
    assert get_history(vault_dir) == []


def test_clear_history_removes_all_entries(vault_dir):
    record(vault_dir, "push", "alice")
    record(vault_dir, "pull", "bob")
    clear_history(vault_dir)
    assert get_history(vault_dir) == []


def test_history_pruned_to_max_entries(vault_dir):
    for i in range(MAX_HISTORY_ENTRIES + 10):
        record(vault_dir, "push", f"user{i}")
    entries = get_history(vault_dir)
    assert len(entries) == MAX_HISTORY_ENTRIES


def test_corrupted_history_raises(vault_dir):
    path = _history_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not-json")
    with pytest.raises(HistoryCorruptedError):
        get_history(vault_dir)


def test_history_file_contains_valid_json(vault_dir):
    record(vault_dir, "push", "alice")
    raw = _history_path(vault_dir).read_text()
    data = json.loads(raw)
    assert isinstance(data, list)
    assert data[0]["user"] == "alice"
