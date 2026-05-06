"""Tests for the CLI tag commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_tags import tags_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _opts(vault_dir: Path) -> list[str]:
    return ["--vault-dir", str(vault_dir)]


def test_add_command_succeeds(runner, vault_dir):
    result = runner.invoke(tags_group, ["add", "backend", "DB_URL", "SECRET"] + _opts(vault_dir))
    assert result.exit_code == 0
    assert "2 variable(s)" in result.output


def test_add_command_writes_tags_file(runner, vault_dir):
    runner.invoke(tags_group, ["add", "infra", "AWS_KEY"] + _opts(vault_dir))
    tags_file = vault_dir / ".envault" / "tags.json"
    assert tags_file.exists()
    data = json.loads(tags_file.read_text())
    assert "infra" in data
    assert "AWS_KEY" in data["infra"]


def test_list_command_shows_tags(runner, vault_dir):
    runner.invoke(tags_group, ["add", "db", "DB_HOST", "DB_PORT"] + _opts(vault_dir))
    result = runner.invoke(tags_group, ["list"] + _opts(vault_dir))
    assert result.exit_code == 0
    assert "[db]" in result.output
    assert "DB_HOST" in result.output


def test_list_command_empty(runner, vault_dir):
    result = runner.invoke(tags_group, ["list"] + _opts(vault_dir))
    assert result.exit_code == 0
    assert "No tags defined" in result.output


def test_show_command_lists_variables(runner, vault_dir):
    runner.invoke(tags_group, ["add", "frontend", "API_URL", "CDN"] + _opts(vault_dir))
    result = runner.invoke(tags_group, ["show", "frontend"] + _opts(vault_dir))
    assert result.exit_code == 0
    assert "API_URL" in result.output
    assert "CDN" in result.output


def test_show_command_missing_tag_fails(runner, vault_dir):
    result = runner.invoke(tags_group, ["show", "ghost"] + _opts(vault_dir))
    assert result.exit_code != 0
    assert "Error" in result.output


def test_remove_command_removes_variable(runner, vault_dir):
    runner.invoke(tags_group, ["add", "misc", "FOO", "BAR"] + _opts(vault_dir))
    result = runner.invoke(tags_group, ["remove", "misc", "FOO"] + _opts(vault_dir))
    assert result.exit_code == 0
    assert "1 variable(s)" in result.output


def test_delete_command_removes_tag(runner, vault_dir):
    runner.invoke(tags_group, ["add", "temp", "X"] + _opts(vault_dir))
    result = runner.invoke(
        tags_group, ["delete", "temp"] + _opts(vault_dir), input="y\n"
    )
    assert result.exit_code == 0
    assert "deleted" in result.output
