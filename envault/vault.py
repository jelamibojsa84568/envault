"""High-level vault API — ties together crypto, dotenv_parser, and storage."""

from __future__ import annotations

from typing import Dict

from envault import crypto, dotenv_parser, storage


def push(
    env_vars: Dict[str, str],
    password: str,
    directory: str = ".",
) -> None:
    """Encrypt *env_vars* with *password* and persist to the vault file.

    Parameters
    ----------
    env_vars:
        Mapping of variable names to their plaintext values.
    password:
        Passphrase used to derive the encryption key.
    directory:
        Directory in which the vault file is written (default: cwd).
    """
    plaintext = dotenv_parser.serialise(env_vars)
    ciphertext = crypto.encrypt(plaintext, password)
    storage.save(ciphertext, directory=directory)


def pull(
    password: str,
    directory: str = ".",
) -> Dict[str, str]:
    """Load and decrypt the vault, returning the env-var mapping.

    Parameters
    ----------
    password:
        Passphrase used to derive the decryption key.
    directory:
        Directory from which the vault file is read (default: cwd).

    Raises
    ------
    storage.VaultNotFoundError
        If no vault file exists in *directory*.
    storage.StorageCorruptedError
        If the vault file cannot be parsed.
    ValueError
        If *password* is incorrect or the ciphertext is tampered.
    """
    ciphertext = storage.load(directory=directory)
    plaintext = crypto.decrypt(ciphertext, password)
    return dotenv_parser.parse(plaintext)


def is_initialised(directory: str = ".") -> bool:
    """Return *True* if a vault file exists in *directory*."""
    return storage.exists(directory=directory)
