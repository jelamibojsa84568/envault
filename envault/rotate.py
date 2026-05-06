"""Key rotation: re-encrypt vault ciphertext under a new password."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault import storage, vault
from envault.crypto import decrypt, encrypt
from envault.audit import record


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate(
    old_password: str,
    new_password: str,
    vault_dir: Optional[Path] = None,
    *,
    actor: str = "unknown",
) -> Path:
    """Re-encrypt the vault under *new_password*.

    Parameters
    ----------
    old_password:
        The password currently protecting the vault.
    new_password:
        The password that will protect the vault after rotation.
    vault_dir:
        Directory that contains the vault file.  Defaults to ``Path.cwd()``.
    actor:
        Username / identifier recorded in the audit log.

    Returns
    -------
    Path
        Path to the updated vault file.

    Raises
    ------
    RotationError
        If the vault is not initialised or decryption with the old password
        fails.
    """
    vault_dir = vault_dir or Path.cwd()

    if not vault.is_initialised(vault_dir):
        raise RotationError("Vault is not initialised in this directory.")

    try:
        ciphertext = storage.load(vault_dir)
    except (storage.VaultNotFoundError, storage.StorageCorruptedError) as exc:
        raise RotationError(f"Could not load vault: {exc}") from exc

    try:
        plaintext = decrypt(ciphertext, old_password)
    except Exception as exc:
        raise RotationError("Decryption failed — wrong old password?") from exc

    new_ciphertext = encrypt(plaintext, new_password)
    path = storage.save(new_ciphertext, vault_dir)

    record(
        action="rotate",
        actor=actor,
        details={"vault_dir": str(vault_dir)},
        vault_dir=vault_dir,
    )

    return path
