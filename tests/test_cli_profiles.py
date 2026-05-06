"""Integration tests for CLI profile commands."""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli_profiles import profile_group
from envault.profiles import _profiles_path


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _opts(vault_dir: Path):
    return ["--vault-dir", str(vault_dir)]


def test_add_command_succeeds(runner, vault_dir):
    result = runner.invoke(profile_group, ["add", "dev"] + _opts(vault_dir))
    assert result.exit_code == 0
    assert "dev" in result.output


def test_add_command_writes_profiles_file(runner, vault_dir):
    runner.invoke(profile_group, ["add", "dev"] + _opts(vault_dir))
    assert _profiles_path(vault_dir).exists()


def test_add_command_custom_vault_file(runner, vault_dir):
    runner.invoke(
        profile_group,
        ["add", "prod", "--vault-file", "custom.json"] + _opts(vault_dir),
    )
    data = json.loads(_profiles_path(vault_dir).read_text())
    assert data["prod"] == "custom.json"


def test_add_default_filename_derived_from_name(runner, vault_dir):
    runner.invoke(profile_group, ["add", "staging"] + _opts(vault_dir))
    data = json.loads(_profiles_path(vault_dir).read_text())
    assert data["staging"] == "vault_staging.json"


def test_list_shows_profiles(runner, vault_dir):
    runner.invoke(profile_group, ["add", "dev"] + _opts(vault_dir))
    runner.invoke(profile_group, ["add", "prod"] + _opts(vault_dir))
    result = runner.invoke(profile_group, ["list"] + _opts(vault_dir))
    assert "dev" in result.output
    assert "prod" in result.output


def test_list_marks_active_profile(runner, vault_dir):
    runner.invoke(profile_group, ["add", "dev"] + _opts(vault_dir))
    runner.invoke(profile_group, ["use", "dev"] + _opts(vault_dir))
    result = runner.invoke(profile_group, ["list"] + _opts(vault_dir))
    assert "*" in result.output


def test_remove_command_succeeds(runner, vault_dir):
    runner.invoke(profile_group, ["add", "dev"] + _opts(vault_dir))
    result = runner.invoke(profile_group, ["remove", "dev"] + _opts(vault_dir))
    assert result.exit_code == 0


def test_remove_missing_profile_exits_nonzero(runner, vault_dir):
    result = runner.invoke(profile_group, ["remove", "ghost"] + _opts(vault_dir))
    assert result.exit_code != 0


def test_use_command_sets_active(runner, vault_dir):
    runner.invoke(profile_group, ["add", "staging"] + _opts(vault_dir))
    result = runner.invoke(profile_group, ["use", "staging"] + _opts(vault_dir))
    assert result.exit_code == 0
    assert "staging" in result.output


def test_use_unknown_profile_exits_nonzero(runner, vault_dir):
    result = runner.invoke(profile_group, ["use", "unknown"] + _opts(vault_dir))
    assert result.exit_code != 0
