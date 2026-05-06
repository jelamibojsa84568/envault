"""Integration tests for CLI access commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_access import access_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _opts(vault_dir: Path):
    return ["--vault-dir", str(vault_dir)]


def test_grant_command_succeeds(runner, vault_dir):
    result = runner.invoke(access_group, ["grant", "alice", "write"] + _opts(vault_dir))
    assert result.exit_code == 0
    assert "Granted 'write' to 'alice'" in result.output


def test_grant_writes_access_file(runner, vault_dir):
    runner.invoke(access_group, ["grant", "bob", "admin"] + _opts(vault_dir))
    data = json.loads((vault_dir / ".envault_access.json").read_text())
    assert data["bob"] == "admin"


def test_revoke_existing_user(runner, vault_dir):
    runner.invoke(access_group, ["grant", "carol", "read"] + _opts(vault_dir))
    result = runner.invoke(access_group, ["revoke", "carol"] + _opts(vault_dir))
    assert result.exit_code == 0
    assert "Revoked access" in result.output


def test_revoke_nonexistent_user(runner, vault_dir):
    result = runner.invoke(access_group, ["revoke", "ghost"] + _opts(vault_dir))
    assert result.exit_code == 0
    assert "not in the access list" in result.output


def test_list_shows_all_users(runner, vault_dir):
    runner.invoke(access_group, ["grant", "alice", "admin"] + _opts(vault_dir))
    runner.invoke(access_group, ["grant", "bob", "read"] + _opts(vault_dir))
    result = runner.invoke(access_group, ["list"] + _opts(vault_dir))
    assert "alice" in result.output
    assert "admin" in result.output
    assert "bob" in result.output
    assert "read" in result.output


def test_list_empty_vault(runner, vault_dir):
    result = runner.invoke(access_group, ["list"] + _opts(vault_dir))
    assert "No users" in result.output


def test_check_existing_user(runner, vault_dir):
    runner.invoke(access_group, ["grant", "dave", "write"] + _opts(vault_dir))
    result = runner.invoke(access_group, ["check", "dave"] + _opts(vault_dir))
    assert "write" in result.output


def test_check_unknown_user(runner, vault_dir):
    result = runner.invoke(access_group, ["check", "nobody"] + _opts(vault_dir))
    assert "no access" in result.output
