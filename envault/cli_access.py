"""CLI commands for managing vault access control."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.access import (
    grant,
    revoke,
    list_users,
    get_role,
    AccessDeniedError,
    InvalidRoleError,
    VALID_ROLES,
)


def _resolve_vault_dir(vault_dir: str | None) -> Path:
    return Path(vault_dir) if vault_dir else Path.cwd()


@click.group("access")
def access_group() -> None:
    """Manage user access permissions for the vault."""


@access_group.command("grant")
@click.argument("username")
@click.argument("role", type=click.Choice(list(VALID_ROLES)))
@click.option("--vault-dir", default=None, help="Path to vault directory.")
def cmd_grant(username: str, role: str, vault_dir: str | None) -> None:
    """Grant USERNAME the specified ROLE."""
    path = _resolve_vault_dir(vault_dir)
    try:
        grant(path, username, role)
        click.echo(f"Granted '{role}' to '{username}'.")
    except InvalidRoleError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@access_group.command("revoke")
@click.argument("username")
@click.option("--vault-dir", default=None, help="Path to vault directory.")
def cmd_revoke(username: str, vault_dir: str | None) -> None:
    """Remove USERNAME from the access list."""
    path = _resolve_vault_dir(vault_dir)
    existed = revoke(path, username)
    if existed:
        click.echo(f"Revoked access for '{username}'.")
    else:
        click.echo(f"User '{username}' was not in the access list.")


@access_group.command("list")
@click.option("--vault-dir", default=None, help="Path to vault directory.")
def cmd_list(vault_dir: str | None) -> None:
    """List all users and their roles."""
    path = _resolve_vault_dir(vault_dir)
    users = list_users(path)
    if not users:
        click.echo("No users have been granted access.")
        return
    click.echo(f"{'USERNAME':<25} ROLE")
    click.echo("-" * 35)
    for username, role in sorted(users.items()):
        click.echo(f"{username:<25} {role}")


@access_group.command("check")
@click.argument("username")
@click.option("--vault-dir", default=None, help="Path to vault directory.")
def cmd_check(username: str, vault_dir: str | None) -> None:
    """Show the current role for USERNAME."""
    path = _resolve_vault_dir(vault_dir)
    role = get_role(path, username)
    if role:
        click.echo(f"'{username}' has role '{role}'.")
    else:
        click.echo(f"'{username}' has no access.")
