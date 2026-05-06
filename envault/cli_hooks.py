"""CLI commands for managing push/pull hooks."""

from __future__ import annotations

from pathlib import Path

import click

from envault.hooks import HookError, set_hook, remove_hook, get_hooks


def _resolve_vault_dir(ctx: click.Context) -> Path:
    return Path(ctx.obj.get("vault_dir", ".")) if ctx.obj else Path(".")


@click.group("hooks")
def hooks_group() -> None:
    """Manage pre/post operation hooks."""


@hooks_group.command("set")
@click.argument("event")
@click.argument("command")
@click.pass_context
def cmd_set(ctx: click.Context, event: str, command: str) -> None:
    """Register COMMAND to run on EVENT.

    EVENT must be one of: pre-push, post-push, pre-pull, post-pull.
    """
    vault_dir = _resolve_vault_dir(ctx)
    try:
        set_hook(vault_dir, event, command)
        click.echo(f"Hook set: {event} -> {command}")
    except HookError as exc:
        raise click.ClickException(str(exc)) from exc


@hooks_group.command("remove")
@click.argument("event")
@click.pass_context
def cmd_remove(ctx: click.Context, event: str) -> None:
    """Remove the hook registered for EVENT."""
    vault_dir = _resolve_vault_dir(ctx)
    try:
        removed = remove_hook(vault_dir, event)
    except HookError as exc:
        raise click.ClickException(str(exc)) from exc
    if removed:
        click.echo(f"Hook removed: {event}")
    else:
        click.echo(f"No hook registered for '{event}'.")


@hooks_group.command("list")
@click.pass_context
def cmd_list(ctx: click.Context) -> None:
    """List all registered hooks."""
    vault_dir = _resolve_vault_dir(ctx)
    try:
        hooks = get_hooks(vault_dir)
    except HookError as exc:
        raise click.ClickException(str(exc)) from exc
    if not hooks:
        click.echo("No hooks registered.")
        return
    for event, command in sorted(hooks.items()):
        click.echo(f"  {event:<12} {command}")
