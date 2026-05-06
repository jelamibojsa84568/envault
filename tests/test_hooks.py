"""Tests for envault.hooks."""

from __future__ import annotations

import json
import sys
import pytest
from pathlib import Path

from envault.hooks import (
    HookError,
    set_hook,
    remove_hook,
    get_hooks,
    run_hook,
    HOOKS_FILENAME,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_set_hook_creates_file(vault_dir):
    set_hook(vault_dir, "pre-push", "echo hello")
    assert (vault_dir / HOOKS_FILENAME).exists()


def test_set_hook_stores_command(vault_dir):
    set_hook(vault_dir, "post-pull", "make reload")
    data = json.loads((vault_dir / HOOKS_FILENAME).read_text())
    assert data["post-pull"] == "make reload"


def test_set_hook_invalid_event_raises(vault_dir):
    with pytest.raises(HookError, match="Unknown event"):
        set_hook(vault_dir, "on-deploy", "echo x")


def test_set_hook_overwrites_existing(vault_dir):
    set_hook(vault_dir, "pre-push", "echo first")
    set_hook(vault_dir, "pre-push", "echo second")
    hooks = get_hooks(vault_dir)
    assert hooks["pre-push"] == "echo second"


def test_remove_hook_returns_true_when_exists(vault_dir):
    set_hook(vault_dir, "post-push", "echo done")
    assert remove_hook(vault_dir, "post-push") is True


def test_remove_hook_returns_false_when_missing(vault_dir):
    assert remove_hook(vault_dir, "pre-pull") is False


def test_remove_hook_deletes_entry(vault_dir):
    set_hook(vault_dir, "pre-push", "echo x")
    remove_hook(vault_dir, "pre-push")
    assert "pre-push" not in get_hooks(vault_dir)


def test_get_hooks_empty_when_no_file(vault_dir):
    assert get_hooks(vault_dir) == {}


def test_run_hook_returns_none_when_no_hook(vault_dir):
    assert run_hook(vault_dir, "pre-push") is None


def test_run_hook_returns_output(vault_dir):
    set_hook(vault_dir, "post-push", f"{sys.executable} -c \"print('synced')\"")
    output = run_hook(vault_dir, "post-push")
    assert output == "synced"


def test_run_hook_raises_on_nonzero_exit(vault_dir):
    set_hook(vault_dir, "pre-pull", f"{sys.executable} -c \"raise SystemExit(1)\"")
    with pytest.raises(HookError, match="failed"):
        run_hook(vault_dir, "pre-pull")


def test_corrupted_hooks_file_raises(vault_dir):
    (vault_dir / HOOKS_FILENAME).write_text("not json")
    with pytest.raises(HookError, match="corrupted"):
        get_hooks(vault_dir)
