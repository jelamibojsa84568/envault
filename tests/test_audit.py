"""Tests for envault.audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.audit import record, get_log, clear_log, _audit_path, AUDIT_FILENAME


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_record_creates_audit_file(vault_dir: Path) -> None:
    record("push", vault_dir=vault_dir)
    assert _audit_path(vault_dir).exists()


def test_record_returns_entry_with_expected_keys(vault_dir: Path) -> None:
    entry = record("push", user="alice", vault_dir=vault_dir)
    assert entry["action"] == "push"
    assert entry["user"] == "alice"
    assert "timestamp" in entry


def test_record_appends_multiple_entries(vault_dir: Path) -> None:
    record("init", user="alice", vault_dir=vault_dir)
    record("push", user="bob", vault_dir=vault_dir)
    entries = get_log(vault_dir)
    assert len(entries) == 2
    assert entries[0]["action"] == "init"
    assert entries[1]["action"] == "push"


def test_record_stores_details(vault_dir: Path) -> None:
    record("push", details={"keys_changed": 3}, vault_dir=vault_dir)
    entries = get_log(vault_dir)
    assert entries[0]["details"]["keys_changed"] == 3


def test_get_log_returns_empty_list_when_no_file(vault_dir: Path) -> None:
    assert get_log(vault_dir) == []


def test_get_log_returns_empty_list_on_corrupt_file(vault_dir: Path) -> None:
    _audit_path(vault_dir).write_text("not json", encoding="utf-8")
    assert get_log(vault_dir) == []


def test_clear_log_removes_file(vault_dir: Path) -> None:
    record("push", vault_dir=vault_dir)
    clear_log(vault_dir)
    assert not _audit_path(vault_dir).exists()


def test_clear_log_is_idempotent(vault_dir: Path) -> None:
    clear_log(vault_dir)  # file does not exist — should not raise


def test_audit_file_is_valid_json(vault_dir: Path) -> None:
    record("pull", user="carol", vault_dir=vault_dir)
    raw = _audit_path(vault_dir).read_text(encoding="utf-8")
    data = json.loads(raw)
    assert isinstance(data, list)
