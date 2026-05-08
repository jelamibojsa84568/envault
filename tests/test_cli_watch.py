"""Tests for envault.cli_watch."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_watch import cmd_watch


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    """Return a minimal initialised vault directory."""
    (tmp_path / ".envault").mkdir()
    (tmp_path / ".env").write_text("KEY=value\n")
    return tmp_path


def _opts(vault_dir: Path) -> list[str]:
    return ["--vault-dir", str(vault_dir), "--interval", "0.01"]


def test_watch_exits_when_vault_not_initialised(runner: CliRunner, tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("KEY=val")
    result = runner.invoke(cmd_watch, ["--vault-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "not initialised" in result.output


def test_watch_exits_when_env_file_missing(runner: CliRunner, vault_dir: Path) -> None:
    (vault_dir / ".env").unlink()
    with patch("envault.cli_watch.is_initialised", return_value=True), \
         patch("envault.cli_watch._get_password", return_value="secret"):
        result = runner.invoke(cmd_watch, _opts(vault_dir))
    assert result.exit_code != 0
    assert "not found" in result.output


def test_watch_starts_and_stops_on_keyboard_interrupt(runner: CliRunner, vault_dir: Path) -> None:
    with patch("envault.cli_watch.is_initialised", return_value=True), \
         patch("envault.cli_watch._get_password", return_value="secret"), \
         patch("envault.cli_watch.watch", side_effect=KeyboardInterrupt):
        result = runner.invoke(cmd_watch, _opts(vault_dir))
    assert result.exit_code == 0
    assert "stopped" in result.output


def test_watch_on_change_calls_push(runner: CliRunner, vault_dir: Path) -> None:
    """Verify that the on_change callback invokes push_with_audit."""
    push_mock = MagicMock()

    captured_callback: list = []

    def _fake_watch(path, on_change, *, interval, max_iterations=None):  # noqa: ANN001
        captured_callback.append(on_change)
        raise KeyboardInterrupt

    with patch("envault.cli_watch.is_initialised", return_value=True), \
         patch("envault.cli_watch._get_password", return_value="secret"), \
         patch("envault.cli_watch.push_with_audit", push_mock), \
         patch("envault.cli_watch.watch", side_effect=_fake_watch):
        runner.invoke(cmd_watch, _opts(vault_dir))

    assert captured_callback, "on_change callback was never captured"
    captured_callback[0](vault_dir / ".env")
    push_mock.assert_called_once()
