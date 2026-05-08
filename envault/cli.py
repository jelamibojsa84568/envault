"""CLI entry-point for envault."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.vault import is_initialised, push, pull
from envault.storage import VaultNotFoundError
from envault.cli_diff import push_with_audit, pull_with_audit
from envault.cli_access import access_group
from envault.cli_rotate import cmd_rotate
from envault.cli_export import cmd_export
from envault.cli_snapshot import snapshot_group
from envault.cli_tags import tags_group
from envault.cli_hooks import hooks_group
from envault.cli_profiles import profile_group
from envault.cli_watch import cmd_watch


def _get_password(confirm: bool = False) -> str:
    prompt = "Vault password"
    if confirm:
        return click.prompt(prompt, hide_input=True, confirmation_prompt=True)
    return click.prompt(prompt, hide_input=True)


@click.command("init")
@click.option("--vault-dir", default=None, hidden=True)
def cmd_init(vault_dir: str | None) -> None:
    """Initialise a new vault in the current directory."""
    vd = Path(vault_dir) if vault_dir else Path.cwd()
    vault_meta = vd / ".envault"
    if vault_meta.exists():
        click.echo("Vault already initialised.")
        return
    vault_meta.mkdir(parents=True, exist_ok=True)
    click.echo(f"Vault initialised at {vault_meta}")


@click.command("push")
@click.option("--env-file", default=".env", show_default=True)
@click.option("--vault-dir", default=None, hidden=True)
def cmd_push(env_file: str, vault_dir: str | None) -> None:
    """Encrypt and push the local .env to the vault."""
    vd = Path(vault_dir) if vault_dir else Path.cwd()
    if not is_initialised(vd):
        click.echo("Vault is not initialised.", err=True)
        sys.exit(1)
    password = _get_password(confirm=False)
    env_path = vd / env_file
    push_with_audit(vd, env_path, password, user="cli")
    click.echo("Pushed.")


@click.command("pull")
@click.option("--env-file", default=".env", show_default=True)
@click.option("--vault-dir", default=None, hidden=True)
def cmd_pull(env_file: str, vault_dir: str | None) -> None:
    """Pull and decrypt the vault into a local .env."""
    vd = Path(vault_dir) if vault_dir else Path.cwd()
    if not is_initialised(vd):
        click.echo("Vault is not initialised.", err=True)
        sys.exit(1)
    password = _get_password(confirm=False)
    env_path = vd / env_file
    try:
        pull_with_audit(vd, env_path, password, user="cli")
    except VaultNotFoundError:
        click.echo("No vault found. Push first.", err=True)
        sys.exit(1)
    click.echo("Pulled.")


@click.command("status")
@click.option("--vault-dir", default=None, hidden=True)
def cmd_status(vault_dir: str | None) -> None:
    """Show whether the vault is initialised."""
    vd = Path(vault_dir) if vault_dir else Path.cwd()
    if is_initialised(vd):
        click.echo("Vault is initialised.")
    else:
        click.echo("Vault is NOT initialised.")


@click.group()
def cli() -> None:
    """envault — secure .env manager."""


cli.add_command(cmd_init, "init")
cli.add_command(cmd_push, "push")
cli.add_command(cmd_pull, "pull")
cli.add_command(cmd_status, "status")
cli.add_command(cmd_rotate, "rotate")
cli.add_command(cmd_export, "export")
cli.add_command(cmd_watch, "watch")
cli.add_command(access_group, "access")
cli.add_command(snapshot_group, "snapshot")
cli.add_command(tags_group, "tags")
cli.add_command(hooks_group, "hooks")
cli.add_command(profile_group, "profile")


if __name__ == "__main__":  # pragma: no cover
    cli()
