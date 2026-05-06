"""CLI sub-command: envault rotate — interactively rotate the vault master key."""

from __future__ import annotations

import click

from envault.rotate import RotationError, rotate
from envault.cli import _get_password


@click.command("rotate")
@click.option(
    "--actor",
    default=None,
    help="Username recorded in the audit log (defaults to $USER).",
)
def cmd_rotate(actor: str | None) -> None:
    """Rotate the vault master password.

    You will be prompted for the current password and then asked to choose and
    confirm a new one.  All vault data is re-encrypted transparently.
    """
    import os
    from pathlib import Path

    resolved_actor = actor or os.environ.get("USER", "unknown")
    vault_dir = Path.cwd()

    click.echo("Rotating vault master password…")

    old_password = _get_password(confirm=False, prompt="Current password")
    new_password = _get_password(confirm=True, prompt="New password")

    if old_password == new_password:
        click.echo("New password is identical to the current one — nothing to do.", err=True)
        raise SystemExit(1)

    try:
        path = rotate(
            old_password,
            new_password,
            vault_dir=vault_dir,
            actor=resolved_actor,
        )
    except RotationError as exc:
        click.echo(f"Rotation failed: {exc}", err=True)
        raise SystemExit(1)

    click.echo(f"Vault re-encrypted successfully → {path}")
