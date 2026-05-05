"""Command-line interface for envault.

Provides the `envault` command with subcommands for managing encrypted
environment variables across a team.
"""

import sys
import argparse
from pathlib import Path

from envault import vault
from envault.storage import VaultNotFoundError, StorageCorruptedError


def _get_password(prompt: str = "Vault password: ") -> str:
    """Prompt the user for a password without echoing it."""
    import getpass
    password = getpass.getpass(prompt)
    if not password:
        print("Error: password must not be empty.", file=sys.stderr)
        sys.exit(1)
    return password


def cmd_init(args: argparse.Namespace) -> int:
    """Initialise a new vault in the current directory."""
    if vault.is_initialised():
        print("Vault already initialised in this directory.")
        return 1

    password = _get_password("New vault password: ")
    confirm = _get_password("Confirm password: ")
    if password != confirm:
        print("Error: passwords do not match.", file=sys.stderr)
        return 1

    env_file = Path(args.env_file)
    if not env_file.exists():
        print(f"Error: {env_file} not found. Create it first.", file=sys.stderr)
        return 1

    path = vault.push(env_file.read_text(), password)
    print(f"Vault initialised and saved to {path}")
    return 0


def cmd_push(args: argparse.Namespace) -> int:
    """Encrypt and push the local .env file to the vault."""
    env_file = Path(args.env_file)
    if not env_file.exists():
        print(f"Error: {env_file} not found.", file=sys.stderr)
        return 1

    password = _get_password()
    try:
        path = vault.push(env_file.read_text(), password)
        print(f"Pushed to {path}")
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_pull(args: argparse.Namespace) -> int:
    """Decrypt the vault and write variables to the local .env file."""
    password = _get_password()
    try:
        content = vault.pull(password)
    except VaultNotFoundError:
        print("Error: no vault found. Run `envault init` first.", file=sys.stderr)
        return 1
    except StorageCorruptedError:
        print("Error: vault file is corrupted.", file=sys.stderr)
        return 1
    except ValueError as exc:
        # Wrong password or tampered ciphertext
        print(f"Error: decryption failed — {exc}", file=sys.stderr)
        return 1

    env_file = Path(args.env_file)
    env_file.write_text(content)
    print(f"Pulled and wrote {len(content.splitlines())} lines to {env_file}")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    """Show whether a vault exists in the current directory."""
    if vault.is_initialised():
        print("Vault is initialised in this directory.")
    else:
        print("No vault found. Run `envault init` to create one.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Secure environment variable manager.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        metavar="FILE",
        help="Path to the .env file (default: .env)",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    subparsers.add_parser("init", help="Initialise a new vault from the local .env file.")
    subparsers.add_parser("push", help="Encrypt and push the local .env to the vault.")
    subparsers.add_parser("pull", help="Decrypt the vault and write to the local .env file.")
    subparsers.add_parser("status", help="Show vault status for the current directory.")

    return parser


def main(argv: list[str] | None = None) -> int:  # noqa: UP007
    """Entry point for the `envault` CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    commands = {
        "init": cmd_init,
        "push": cmd_push,
        "pull": cmd_pull,
        "status": cmd_status,
    }
    return commands[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
