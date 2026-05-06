"""CLI commands for managing envault profiles."""

from __future__ import annotations

import click
from pathlib import Path

from envault.profiles import (
    set_profile,
    remove_profile,
    get_profile,
    list_profiles,
    set_active_profile,
    active_profile,
    ProfileNotFoundError,
    DEFAULT_PROFILE,
)


def _resolve_vault_dir(vault_dir: str) -> Path:
    return Path(vault_dir).expanduser().resolve()


@click.group(name="profile")
def profile_group() -> None:
    """Manage named vault profiles (dev, staging, prod, …)."""


@profile_group.command("add")
@click.argument("name")
@click.option("--vault-file", default=None, help="Vault filename to associate with the profile.")
@click.option("--vault-dir", default=".", show_default=True)
def cmd_add(name: str, vault_file: str | None, vault_dir: str) -> None:
    """Register a new profile NAME."""
    vd = _resolve_vault_dir(vault_dir)
    filename = vault_file or f"vault_{name}.json"
    set_profile(vd, name, filename)
    click.echo(f"Profile '{name}' -> '{filename}' saved.")


@profile_group.command("remove")
@click.argument("name")
@click.option("--vault-dir", default=".", show_default=True)
def cmd_remove(name: str, vault_dir: str) -> None:
    """Remove profile NAME."""
    vd = _resolve_vault_dir(vault_dir)
    removed = remove_profile(vd, name)
    if removed:
        click.echo(f"Profile '{name}' removed.")
    else:
        click.echo(f"Profile '{name}' not found.", err=True)
        raise SystemExit(1)


@profile_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
def cmd_list(vault_dir: str) -> None:
    """List all registered profiles."""
    vd = _resolve_vault_dir(vault_dir)
    names = list_profiles(vd)
    current = active_profile(vd)
    if not names:
        click.echo("No profiles defined.")
        return
    for name in names:
        marker = " *" if name == current else ""
        try:
            filename = get_profile(vd, name)
        except ProfileNotFoundError:
            filename = "?"
        click.echo(f"  {name}: {filename}{marker}")


@profile_group.command("use")
@click.argument("name")
@click.option("--vault-dir", default=".", show_default=True)
def cmd_use(name: str, vault_dir: str) -> None:
    """Set NAME as the active profile."""
    vd = _resolve_vault_dir(vault_dir)
    try:
        set_active_profile(vd, name)
        click.echo(f"Active profile set to '{name}'.")
    except ProfileNotFoundError:
        click.echo(f"Profile '{name}' does not exist. Add it first.", err=True)
        raise SystemExit(1)
