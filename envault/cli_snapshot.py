"""CLI commands for snapshot management."""

from __future__ import annotations

import datetime
import sys

import click

from envault.cli import _get_password
from envault.snapshot import (
    SnapshotNotFoundError,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)
from envault.storage import load as storage_load
from envault.vault import is_initialised


def _resolve_vault_dir(vault_dir: str | None) -> str:
    import os
    return vault_dir or os.getcwd()


@click.group(name="snapshot")
def snapshot_group() -> None:
    """Manage named snapshots of the vault."""


@snapshot_group.command("save")
@click.argument("name")
@click.option("--vault-dir", default=None, hidden=True)
def cmd_save(name: str, vault_dir: str | None) -> None:
    """Save the current vault state as snapshot NAME."""
    vd = _resolve_vault_dir(vault_dir)
    if not is_initialised(vd):
        click.echo("Vault is not initialised. Run `envault init` first.", err=True)
        sys.exit(1)
    ciphertext = storage_load(vd)
    path = save_snapshot(vd, name, ciphertext)
    click.echo(f"Snapshot '{name}' saved → {path}")


@snapshot_group.command("restore")
@click.argument("name")
@click.option("--vault-dir", default=None, hidden=True)
def cmd_restore(name: str, vault_dir: str | None) -> None:
    """Restore vault to snapshot NAME (overwrites current vault file)."""
    from envault.storage import save as storage_save

    vd = _resolve_vault_dir(vault_dir)
    try:
        ciphertext = load_snapshot(vd, name)
    except SnapshotNotFoundError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    storage_save(vd, ciphertext)
    click.echo(f"Vault restored from snapshot '{name}'.")


@snapshot_group.command("list")
@click.option("--vault-dir", default=None, hidden=True)
def cmd_list(vault_dir: str | None) -> None:
    """List all saved snapshots."""
    vd = _resolve_vault_dir(vault_dir)
    entries = list_snapshots(vd)
    if not entries:
        click.echo("No snapshots found.")
        return
    click.echo(f"{'NAME':<30}  CREATED AT")
    click.echo("-" * 52)
    for entry in entries:
        ts = datetime.datetime.fromtimestamp(entry["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"{entry['name']:<30}  {ts}")


@snapshot_group.command("delete")
@click.argument("name")
@click.option("--vault-dir", default=None, hidden=True)
def cmd_delete(name: str, vault_dir: str | None) -> None:
    """Delete snapshot NAME."""
    vd = _resolve_vault_dir(vault_dir)
    removed = delete_snapshot(vd, name)
    if removed:
        click.echo(f"Snapshot '{name}' deleted.")
    else:
        click.echo(f"Snapshot '{name}' not found.", err=True)
        sys.exit(1)
