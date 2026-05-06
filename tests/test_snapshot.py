"""Tests for envault.snapshot."""

from __future__ import annotations

import json
import time

import pytest

from envault.snapshot import (
    SnapshotCorruptedError,
    SnapshotNotFoundError,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


@pytest.fixture()
def vault_dir(tmp_path):
    return tmp_path


def test_save_creates_file(vault_dir):
    path = save_snapshot(vault_dir, "v1", "ciphertext_abc")
    assert path.exists()


def test_save_returns_correct_path(vault_dir):
    path = save_snapshot(vault_dir, "release", "ct")
    assert path.name == "release.json"


def test_save_writes_valid_json(vault_dir):
    save_snapshot(vault_dir, "v1", "ct_data")
    data = json.loads((vault_dir / ".envault_snapshots" / "v1.json").read_text())
    assert data["ciphertext"] == "ct_data"
    assert data["name"] == "v1"
    assert "created_at" in data


def test_load_returns_ciphertext(vault_dir):
    save_snapshot(vault_dir, "v1", "secret_ct")
    assert load_snapshot(vault_dir, "v1") == "secret_ct"


def test_load_raises_when_missing(vault_dir):
    with pytest.raises(SnapshotNotFoundError):
        load_snapshot(vault_dir, "nonexistent")


def test_load_raises_on_corrupted_file(vault_dir):
    snap_dir = vault_dir / ".envault_snapshots"
    snap_dir.mkdir()
    (snap_dir / "bad.json").write_text("not json", encoding="utf-8")
    with pytest.raises(SnapshotCorruptedError):
        load_snapshot(vault_dir, "bad")


def test_list_snapshots_empty_when_no_dir(vault_dir):
    assert list_snapshots(vault_dir) == []


def test_list_snapshots_returns_all(vault_dir):
    save_snapshot(vault_dir, "alpha", "ct1")
    time.sleep(0.01)
    save_snapshot(vault_dir, "beta", "ct2")
    names = [e["name"] for e in list_snapshots(vault_dir)]
    assert set(names) == {"alpha", "beta"}


def test_list_snapshots_sorted_newest_first(vault_dir):
    save_snapshot(vault_dir, "old", "ct1")
    time.sleep(0.02)
    save_snapshot(vault_dir, "new", "ct2")
    names = [e["name"] for e in list_snapshots(vault_dir)]
    assert names[0] == "new"


def test_delete_snapshot_removes_file(vault_dir):
    save_snapshot(vault_dir, "v1", "ct")
    assert delete_snapshot(vault_dir, "v1") is True
    assert list_snapshots(vault_dir) == []


def test_delete_snapshot_returns_false_when_missing(vault_dir):
    assert delete_snapshot(vault_dir, "ghost") is False
