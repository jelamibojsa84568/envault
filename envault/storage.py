"""Backend storage adapter for envault — reads/writes encrypted vault files."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

DEFAULT_VAULT_FILENAME = ".envault"


class VaultNotFoundError(FileNotFoundError):
    """Raised when the vault file does not exist at the expected path."""


class StorageCorruptedError(ValueError):
    """Raised when the vault file cannot be parsed as valid JSON."""


def _vault_path(directory: str | os.PathLike = ".") -> Path:
    """Return the absolute path to the vault file inside *directory*."""
    return Path(directory).resolve() / DEFAULT_VAULT_FILENAME


def save(ciphertext: str, directory: str | os.PathLike = ".") -> Path:
    """Persist *ciphertext* to the vault file and return its path.

    The file is stored as a JSON envelope so that metadata fields can be
    added in future without breaking existing vaults.
    """
    path = _vault_path(directory)
    envelope = {"version": 1, "ciphertext": ciphertext}
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    return path


def load(directory: str | os.PathLike = ".") -> str:
    """Load and return the ciphertext stored in the vault file.

    Raises
    ------
    VaultNotFoundError
        If the vault file does not exist.
    StorageCorruptedError
        If the file is not valid JSON or is missing expected fields.
    """
    path = _vault_path(directory)
    if not path.exists():
        raise VaultNotFoundError(f"No vault found at {path}")

    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StorageCorruptedError(f"Vault file is not valid JSON: {path}") from exc

    if "ciphertext" not in envelope:
        raise StorageCorruptedError("Vault file is missing 'ciphertext' field.")

    return envelope["ciphertext"]


def exists(directory: str | os.PathLike = ".") -> bool:
    """Return *True* if a vault file is present in *directory*."""
    return _vault_path(directory).exists()
