"""CLI commands for managing variable tags."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.tags import (
    add_tag,
    remove_tag,
    list_tags,
    variables_for_tag,
    delete_tag,
    TagNotFoundError,
    TagsCorruptedError,
)


def _resolve_vault_dir(vault_dir: str | None) -> Path:
    return Path(vault_dir) if vault_dir else Path.cwd()


@click.group(name="tags")
def tags_group() -> None:
    """Manage variable tags for grouping and filtering."""


@tags_group.command("add")
@click.argument("tag")
@click.argument("variables", nargs=-1, required=True)
@click.option("--vault-dir", default=None, help="Path to vault directory.")
def cmd_add(tag: str, variables: tuple[str, ...], vault_dir: str | None) -> None:
    """Add VARIABLES to TAG."""
    vd = _resolve_vault_dir(vault_dir)
    try:
        add_tag(vd, tag, list(variables))
        click.echo(f"Tagged {len(variables)} variable(s) with '{tag}'.")
    except TagsCorruptedError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@tags_group.command("remove")
@click.argument("tag")
@click.argument("variables", nargs=-1, required=True)
@click.option("--vault-dir", default=None, help="Path to vault directory.")
def cmd_remove(tag: str, variables: tuple[str, ...], vault_dir: str | None) -> None:
    """Remove VARIABLES from TAG."""
    vd = _resolve_vault_dir(vault_dir)
    try:
        removed = remove_tag(vd, tag, list(variables))
        click.echo(f"Removed {len(removed)} variable(s) from '{tag}'.")
    except TagNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@tags_group.command("list")
@click.option("--vault-dir", default=None, help="Path to vault directory.")
def cmd_list(vault_dir: str | None) -> None:
    """List all tags and their variables."""
    vd = _resolve_vault_dir(vault_dir)
    try:
        data = list_tags(vd)
    except TagsCorruptedError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    if not data:
        click.echo("No tags defined.")
        return
    for tag, variables in sorted(data.items()):
        click.echo(f"[{tag}]")
        for var in variables:
            click.echo(f"  {var}")


@tags_group.command("show")
@click.argument("tag")
@click.option("--vault-dir", default=None, help="Path to vault directory.")
def cmd_show(tag: str, vault_dir: str | None) -> None:
    """Show variables associated with TAG."""
    vd = _resolve_vault_dir(vault_dir)
    try:
        variables = variables_for_tag(vd, tag)
        for var in variables:
            click.echo(var)
    except TagNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@tags_group.command("delete")
@click.argument("tag")
@click.option("--vault-dir", default=None, help="Path to vault directory.")
@click.confirmation_option(prompt="Delete this tag?")
def cmd_delete(tag: str, vault_dir: str | None) -> None:
    """Delete an entire TAG entry."""
    vd = _resolve_vault_dir(vault_dir)
    try:
        delete_tag(vd, tag)
        click.echo(f"Tag '{tag}' deleted.")
    except TagNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
