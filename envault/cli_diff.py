"""CLI helpers that integrate audit logging and diff display into push/pull."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import click

from envault import vault, audit
from envault.diff import compute_diff, format_diff
from envault.dotenv_parser import parse


def push_with_audit(
    env_file: str,
    password: str,
    vault_dir: str | Path | None = None,
    *,
    show_diff: bool = True,
) -> None:
    """Push env vars, print a diff, and record the action in the audit log."""
    env_path = Path(env_file)
    new_vars: Dict[str, str] = parse(env_path.read_text(encoding="utf-8"))

    old_vars: Dict[str, str] = {}
    if vault.is_initialised(vault_dir):
        try:
            old_vars = vault.pull(password, vault_dir=vault_dir)
        except Exception:
            old_vars = {}

    diff = compute_diff(old_vars, new_vars)

    vault.push(new_vars, password, vault_dir=vault_dir)

    if show_diff:
        if diff.is_empty:
            click.echo("Vault up-to-date — no changes pushed.")
        else:
            click.echo("Changes pushed:")
            click.echo(format_diff(diff))

    audit.record(
        "push",
        details={
            "added": len(diff.added),
            "removed": len(diff.removed),
            "changed": len(diff.changed),
        },
        vault_dir=vault_dir,
    )


def pull_with_audit(
    env_file: str,
    password: str,
    vault_dir: str | Path | None = None,
    *,
    show_diff: bool = True,
) -> None:
    """Pull env vars, print a diff against the local file, and audit the action."""
    env_path = Path(env_file)

    old_vars: Dict[str, str] = {}
    if env_path.exists():
        old_vars = parse(env_path.read_text(encoding="utf-8"))

    new_vars = vault.pull(password, vault_dir=vault_dir)

    diff = compute_diff(old_vars, new_vars)

    from envault.dotenv_parser import serialise
    env_path.write_text(serialise(new_vars), encoding="utf-8")

    if show_diff:
        if diff.is_empty:
            click.echo("Local .env already up-to-date.")
        else:
            click.echo("Changes applied to local .env:")
            click.echo(format_diff(diff))

    audit.record(
        "pull",
        details={
            "added": len(diff.added),
            "removed": len(diff.removed),
            "changed": len(diff.changed),
        },
        vault_dir=vault_dir,
    )
