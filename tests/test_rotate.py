"""Tests for envault.rotate."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault import storage, vault
from envault.crypto import decrypt
from envault.rotate import RotationError, rotate


OLD_PASSWORD = "old-secret"
NEW_PASSWORD = "new-secret"
SAMPLE_ENV = b"API_KEY=abc123\nDEBUG=true\n"


@pytest.fixture()
def initialised_vault(tmp_path: Path) -> Path:
    """Create a minimal initialised vault and return its directory."""
    vault.push(SAMPLE_ENV, OLD_PASSWORD, vault_dir=tmp_path)
    return tmp_path


def test_rotate_returns_path(initialised_vault: Path) -> None:
    path = rotate(OLD_PASSWORD, NEW_PASSWORD, vault_dir=initialised_vault)
    assert isinstance(path, Path)
    assert path.exists()


def test_rotate_new_password_decrypts_correctly(initialised_vault: Path) -> None:
    rotate(OLD_PASSWORD, NEW_PASSWORD, vault_dir=initialised_vault)
    ciphertext = storage.load(initialised_vault)
    plaintext = decrypt(ciphertext, NEW_PASSWORD)
    assert plaintext == SAMPLE_ENV


def test_rotate_old_password_no_longer_works(initialised_vault: Path) -> None:
    rotate(OLD_PASSWORD, NEW_PASSWORD, vault_dir=initialised_vault)
    ciphertext = storage.load(initialised_vault)
    with pytest.raises(Exception):
        decrypt(ciphertext, OLD_PASSWORD)


def test_rotate_wrong_old_password_raises(initialised_vault: Path) -> None:
    with pytest.raises(RotationError, match="Decryption failed"):
        rotate("wrong-password", NEW_PASSWORD, vault_dir=initialised_vault)


def test_rotate_uninitialised_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(RotationError, match="not initialised"):
        rotate(OLD_PASSWORD, NEW_PASSWORD, vault_dir=tmp_path)


def test_rotate_records_audit_entry(initialised_vault: Path) -> None:
    from envault.audit import get_log

    rotate(OLD_PASSWORD, NEW_PASSWORD, vault_dir=initialised_vault, actor="alice")
    entries = get_log(initialised_vault)
    assert any(e["action"] == "rotate" and e["actor"] == "alice" for e in entries)
