"""CLI commands for inspecting and clearing vault locks."""

from __future__ import annotations

import json
import time
from pathlib import Path

import click

from envault import lock as _lock


def _resolve_vault_dir(ctx: click.Context) -> Path:
    return Path(ctx.obj.get("vault_dir", "."))


@click.group("lock")
def lock_group() -> None:
    """Manage vault file locks."""


@lock_group.command("status")
@click.pass_context
def cmd_status(ctx: click.Context) -> None:
    """Show whether the vault is currently locked."""
    vault_dir = _resolve_vault_dir(ctx)
    lock_file = _lock._lock_path(vault_dir)

    if not lock_file.exists():
        click.echo("Vault is not locked.")
        return

    info = _lock._read_lock(lock_file)
    if info:
        age = time.time() - info.get("acquired_at", 0)
        stale = age > _lock.STALE_AFTER_SECONDS
        click.echo(
            f"Locked by: {info.get('owner', 'unknown')}  "
            f"({age:.0f}s ago){'  [STALE]' if stale else ''}"
        )
    else:
        click.echo("Lock file exists but is unreadable.")


@lock_group.command("clear")
@click.option("--force", is_flag=True, help="Remove lock without confirmation.")
@click.pass_context
def cmd_clear(ctx: click.Context, force: bool) -> None:
    """Remove a stale or stuck lock file."""
    vault_dir = _resolve_vault_dir(ctx)

    if not _lock.is_locked(vault_dir):
        click.echo("No lock file found — nothing to clear.")
        return

    if not force:
        click.confirm("Remove the existing lock file?", abort=True)

    removed = _lock.release(vault_dir)
    if removed:
        click.echo("Lock cleared.")
    else:
        click.echo("Lock file was already gone.", err=True)
