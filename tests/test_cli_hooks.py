"""Tests for envault.cli_hooks."""

from __future__ import annotations

from pathlib import Path
import json

import pytest
from click.testing import CliRunner

from envault.cli_hooks import hooks_group
from envault.hooks import HOOKS_FILENAME


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _opts(vault_dir: Path) -> dict:
    return {"obj": {"vault_dir": str(vault_dir)}}


def test_set_command_succeeds(runner, vault_dir):
    result = runner.invoke(
        hooks_group, ["set", "pre-push", "echo hi"], **_opts(vault_dir)
    )
    assert result.exit_code == 0
    assert "pre-push" in result.output


def test_set_command_writes_hooks_file(runner, vault_dir):
    runner.invoke(hooks_group, ["set", "post-pull", "make reload"], **_opts(vault_dir))
    data = json.loads((vault_dir / HOOKS_FILENAME).read_text())
    assert data.get("post-pull") == "make reload"


def test_set_invalid_event_exits_nonzero(runner, vault_dir):
    result = runner.invoke(
        hooks_group, ["set", "on-deploy", "echo x"], **_opts(vault_dir)
    )
    assert result.exit_code != 0
    assert "Unknown event" in result.output


def test_remove_existing_hook(runner, vault_dir):
    runner.invoke(hooks_group, ["set", "pre-push", "echo x"], **_opts(vault_dir))
    result = runner.invoke(hooks_group, ["remove", "pre-push"], **_opts(vault_dir))
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_missing_hook_reports_none(runner, vault_dir):
    result = runner.invoke(hooks_group, ["remove", "post-push"], **_opts(vault_dir))
    assert result.exit_code == 0
    assert "No hook registered" in result.output


def test_list_empty_when_no_hooks(runner, vault_dir):
    result = runner.invoke(hooks_group, ["list"], **_opts(vault_dir))
    assert result.exit_code == 0
    assert "No hooks registered" in result.output


def test_list_shows_registered_hooks(runner, vault_dir):
    runner.invoke(hooks_group, ["set", "pre-push", "echo before"], **_opts(vault_dir))
    runner.invoke(hooks_group, ["set", "post-push", "echo after"], **_opts(vault_dir))
    result = runner.invoke(hooks_group, ["list"], **_opts(vault_dir))
    assert result.exit_code == 0
    assert "pre-push" in result.output
    assert "post-push" in result.output
