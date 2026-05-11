"""Tests for envault.lock."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envault import lock as _lock
from envault.lock import LockError, LockStalledError


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_acquire_creates_lock_file(vault_dir: Path) -> None:
    path = _lock.acquire(vault_dir, owner="test")
    assert path.exists()


def test_acquire_returns_lock_path(vault_dir: Path) -> None:
    path = _lock.acquire(vault_dir, owner="test")
    assert path == _lock._lock_path(vault_dir)


def test_lock_file_contains_owner(vault_dir: Path) -> None:
    _lock.acquire(vault_dir, owner="alice")
    info = json.loads(_lock._lock_path(vault_dir).read_text())
    assert info["owner"] == "alice"


def test_lock_file_contains_timestamp(vault_dir: Path) -> None:
    before = time.time()
    _lock.acquire(vault_dir, owner="test")
    after = time.time()
    info = json.loads(_lock._lock_path(vault_dir).read_text())
    assert before <= info["acquired_at"] <= after


def test_release_removes_lock_file(vault_dir: Path) -> None:
    _lock.acquire(vault_dir, owner="test")
    _lock.release(vault_dir)
    assert not _lock._lock_path(vault_dir).exists()


def test_release_returns_true_when_file_existed(vault_dir: Path) -> None:
    _lock.acquire(vault_dir, owner="test")
    assert _lock.release(vault_dir) is True


def test_release_returns_false_when_no_file(vault_dir: Path) -> None:
    assert _lock.release(vault_dir) is False


def test_is_locked_true_when_locked(vault_dir: Path) -> None:
    _lock.acquire(vault_dir, owner="test")
    assert _lock.is_locked(vault_dir) is True


def test_is_locked_false_when_not_locked(vault_dir: Path) -> None:
    assert _lock.is_locked(vault_dir) is False


def test_acquire_times_out_when_already_locked(vault_dir: Path) -> None:
    _lock.acquire(vault_dir, owner="holder")
    with pytest.raises(LockError):
        _lock.acquire(vault_dir, owner="waiter", timeout=0.3)


def test_acquire_raises_stale_error(vault_dir: Path) -> None:
    lock_file = _lock._lock_path(vault_dir)
    stale_payload = {"owner": "zombie", "acquired_at": time.time() - 999}
    lock_file.write_text(json.dumps(stale_payload))
    with pytest.raises(LockStalledError):
        _lock.acquire(vault_dir, owner="newcomer", timeout=0.3)


def test_acquire_after_release_succeeds(vault_dir: Path) -> None:
    _lock.acquire(vault_dir, owner="first")
    _lock.release(vault_dir)
    path = _lock.acquire(vault_dir, owner="second")
    assert path.exists()
