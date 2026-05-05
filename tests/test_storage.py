"""Tests for envault.storage — vault file persistence layer."""

from __future__ import annotations

import json
import pytest

from envault.storage import (
    DEFAULT_VAULT_FILENAME,
    StorageCorruptedError,
    VaultNotFoundError,
    exists,
    load,
    save,
)


def test_save_creates_vault_file(tmp_path):
    save("encrypted_blob", directory=tmp_path)
    assert (tmp_path / DEFAULT_VAULT_FILENAME).exists()


def test_save_returns_path(tmp_path):
    path = save("encrypted_blob", directory=tmp_path)
    assert path == tmp_path / DEFAULT_VAULT_FILENAME


def test_save_writes_valid_json(tmp_path):
    save("some_ciphertext", directory=tmp_path)
    raw = (tmp_path / DEFAULT_VAULT_FILENAME).read_text(encoding="utf-8")
    data = json.loads(raw)
    assert data["ciphertext"] == "some_ciphertext"
    assert data["version"] == 1


def test_load_returns_ciphertext(tmp_path):
    save("hello_cipher", directory=tmp_path)
    result = load(directory=tmp_path)
    assert result == "hello_cipher"


def test_load_raises_when_file_missing(tmp_path):
    with pytest.raises(VaultNotFoundError):
        load(directory=tmp_path)


def test_load_raises_on_invalid_json(tmp_path):
    (tmp_path / DEFAULT_VAULT_FILENAME).write_text("not json", encoding="utf-8")
    with pytest.raises(StorageCorruptedError):
        load(directory=tmp_path)


def test_load_raises_when_ciphertext_missing(tmp_path):
    (tmp_path / DEFAULT_VAULT_FILENAME).write_text(
        json.dumps({"version": 1}), encoding="utf-8"
    )
    with pytest.raises(StorageCorruptedError):
        load(directory=tmp_path)


def test_exists_returns_false_when_no_vault(tmp_path):
    assert exists(directory=tmp_path) is False


def test_exists_returns_true_after_save(tmp_path):
    save("data", directory=tmp_path)
    assert exists(directory=tmp_path) is True


def test_save_overwrites_existing_vault(tmp_path):
    save("first", directory=tmp_path)
    save("second", directory=tmp_path)
    assert load(directory=tmp_path) == "second"
