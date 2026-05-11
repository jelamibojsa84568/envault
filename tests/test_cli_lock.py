"""Tests for envault.cli_lock."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault import lock as _lock
from envault.cli_lock import lock_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _opts(vault_dir: Path) -> dict:
    return {"obj": {"vault_dir": str(vault_dir)}}


def test_status_reports_not_locked(runner: CliRunner, vault_dir: Path) -> None:
    result = runner.invoke(lock_group, ["status"], **_opts(vault_dir))
    assert result.exit_code == 0
    assert "not locked" in result.output


def test_status_reports_locked(runner: CliRunner, vault_dir: Path) -> None:
    _lock.acquire(vault_dir, owner="alice")
    result = runner.invoke(lock_group, ["status"], **_opts(vault_dir))
    assert result.exit_code == 0
    assert "alice" in result.output


def test_status_reports_stale(runner: CliRunner, vault_dir: Path) -> None:
    lock_file = _lock._lock_path(vault_dir)
    lock_file.write_text(json.dumps({"owner": "ghost", "acquired_at": time.time() - 999}))
    result = runner.invoke(lock_group, ["status"], **_opts(vault_dir))
    assert result.exit_code == 0
    assert "STALE" in result.output


def test_clear_removes_lock_with_force(runner: CliRunner, vault_dir: Path) -> None:
    _lock.acquire(vault_dir, owner="test")
    result = runner.invoke(lock_group, ["clear", "--force"], **_opts(vault_dir))
    assert result.exit_code == 0
    assert not _lock.is_locked(vault_dir)
    assert "cleared" in result.output


def test_clear_reports_nothing_when_no_lock(runner: CliRunner, vault_dir: Path) -> None:
    result = runner.invoke(lock_group, ["clear", "--force"], **_opts(vault_dir))
    assert result.exit_code == 0
    assert "nothing" in result.output


def test_clear_prompts_without_force(runner: CliRunner, vault_dir: Path) -> None:
    _lock.acquire(vault_dir, owner="test")
    result = runner.invoke(lock_group, ["clear"], input="y\n", **_opts(vault_dir))
    assert result.exit_code == 0
    assert not _lock.is_locked(vault_dir)
