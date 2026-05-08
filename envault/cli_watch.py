"""CLI command: envault watch — auto-push on local .env changes."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.cli import _get_password
from envault.vault import is_initialised
from envault.cli_diff import push_with_audit
from envault.watch import WatchError, watch


def _resolve_vault_dir(vault_dir: str | None) -> Path:
    return Path(vault_dir) if vault_dir else Path.cwd()


@click.command("watch")
@click.option("--env-file", default=".env", show_default=True, help=".env file to monitor.")
@click.option("--vault-dir", default=None, hidden=True)
@click.option("--interval", default=1.0, show_default=True, help="Poll interval in seconds.")
@click.pass_context
def cmd_watch(ctx: click.Context, env_file: str, vault_dir: str | None, interval: float) -> None:
    """Watch a .env file and auto-push changes to the vault."""
    vd = _resolve_vault_dir(vault_dir)

    if not is_initialised(vd):
        click.echo("Vault is not initialised. Run `envault init` first.", err=True)
        sys.exit(1)

    env_path = vd / env_file
    if not env_path.exists():
        click.echo(f"File not found: {env_path}", err=True)
        sys.exit(1)

    password = _get_password(confirm=False)
    click.echo(f"Watching {env_path} (interval={interval}s) … Press Ctrl+C to stop.")

    def _on_change(path: Path) -> None:
        click.echo(f"  Change detected in {path.name}, pushing …")
        try:
            push_with_audit(vd, path, password, user="watch")
            click.echo("  Push successful.")
        except Exception as exc:  # noqa: BLE001
            click.echo(f"  Push failed: {exc}", err=True)

    try:
        watch(env_path, _on_change, interval=interval)
    except WatchError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nWatcher stopped.")
