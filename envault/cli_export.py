"""CLI command: envault export — decrypt vault and print secrets in chosen format."""
from __future__ import annotations

import sys
import click

from envault.cli import _get_password
from envault.export import render, ExportFormat, UnsupportedFormatError
from envault.vault import pull, is_initialised


_FORMAT_CHOICES = ["shell", "docker", "json"]


@click.command("export")
@click.option(
    "--format", "-f",
    "fmt",
    default="shell",
    show_default=True,
    type=click.Choice(_FORMAT_CHOICES, case_sensitive=False),
    help="Output format.",
)
@click.option(
    "--output", "-o",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help="Write output to FILE instead of stdout.",
)
@click.option(
    "--vault-dir",
    default=".",
    show_default=True,
    type=click.Path(exists=True, file_okay=False),
    help="Directory that contains the vault.",
)
def cmd_export(fmt: str, output: str | None, vault_dir: str) -> None:
    """Decrypt the vault and print variables in the requested format.

    Examples:

    \b
        envault export                     # POSIX shell exports
        envault export -f docker           # docker --env flags
        envault export -f json -o env.json # write JSON to file
    """
    if not is_initialised(vault_dir):
        click.echo("Vault is not initialised. Run `envault init` first.", err=True)
        sys.exit(1)

    password = _get_password(confirm=False)

    try:
        env = pull(vault_dir, password)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error reading vault: {exc}", err=True)
        sys.exit(1)

    try:
        rendered = render(env, fmt)  # type: ignore[arg-type]
    except UnsupportedFormatError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        click.echo(f"Exported {len(env)} variable(s) to {output} ({fmt} format).")
    else:
        click.echo(rendered, nl=False)
