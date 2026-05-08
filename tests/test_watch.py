"""Tests for envault.watch."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from envault.watch import WatchError, _file_hash, watch


# ---------------------------------------------------------------------------
# _file_hash
# ---------------------------------------------------------------------------

def test_file_hash_returns_string_for_existing_file(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=value")
    result = _file_hash(f)
    assert isinstance(result, str) and len(result) == 32


def test_file_hash_returns_none_for_missing_file(tmp_path: Path) -> None:
    assert _file_hash(tmp_path / "nonexistent") is None


def test_file_hash_changes_when_content_changes(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=a")
    h1 = _file_hash(f)
    f.write_text("KEY=b")
    h2 = _file_hash(f)
    assert h1 != h2


def test_file_hash_stable_for_same_content(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=value")
    assert _file_hash(f) == _file_hash(f)


# ---------------------------------------------------------------------------
# watch
# ---------------------------------------------------------------------------

def test_watch_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(WatchError, match="File not found"):
        watch(tmp_path / "missing.env", MagicMock(), interval=0.01, max_iterations=1)


def test_watch_calls_on_change_when_file_modified(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("KEY=original")
    callback = MagicMock()

    def _mutate_then_stop(path: Path) -> None:  # noqa: ARG001
        callback(path)

    # Patch: write new content just before the first iteration fires.
    original_sleep = time.sleep

    call_count = 0

    def _fake_sleep(seconds: float) -> None:  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            env.write_text("KEY=changed")
        original_sleep(0)

    import envault.watch as watch_mod
    watch_mod_sleep = watch_mod.__dict__.get("time")

    import unittest.mock as mock
    with mock.patch("envault.watch.time.sleep", side_effect=_fake_sleep):
        watch(env, _mutate_then_stop, interval=0.01, max_iterations=2)

    callback.assert_called_once()


def test_watch_no_callback_when_file_unchanged(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("KEY=same")
    callback = MagicMock()

    import unittest.mock as mock
    with mock.patch("envault.watch.time.sleep"):
        watch(env, callback, interval=0.01, max_iterations=3)

    callback.assert_not_called()
