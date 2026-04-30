"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from envault.crypto import encrypt, decrypt


PASSWORD = "super-secret-password"
SAMPLE_ENV = "API_KEY=abc123\nDB_PASSWORD=hunter2\nDEBUG=false"


def test_encrypt_returns_string():
    result = encrypt(SAMPLE_ENV, PASSWORD)
    assert isinstance(result, str)
    assert len(result) > 0


def test_decrypt_roundtrip():
    encoded = encrypt(SAMPLE_ENV, PASSWORD)
    decoded = decrypt(encoded, PASSWORD)
    assert decoded == SAMPLE_ENV


def test_encrypt_produces_unique_ciphertexts():
    """Each call should produce a different ciphertext due to random salt/nonce."""
    enc1 = encrypt(SAMPLE_ENV, PASSWORD)
    enc2 = encrypt(SAMPLE_ENV, PASSWORD)
    assert enc1 != enc2


def test_decrypt_wrong_password_raises():
    encoded = encrypt(SAMPLE_ENV, PASSWORD)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(encoded, "wrong-password")


def test_decrypt_corrupted_data_raises():
    encoded = encrypt(SAMPLE_ENV, PASSWORD)
    corrupted = encoded[:-4] + "XXXX"
    with pytest.raises(ValueError):
        decrypt(corrupted, PASSWORD)


def test_decrypt_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid encoded payload"):
        decrypt("not-valid-base64!!!", PASSWORD)


def test_encrypt_empty_string():
    encoded = encrypt("", PASSWORD)
    assert decrypt(encoded, PASSWORD) == ""


def test_encrypt_unicode_content():
    content = "GREETING=héllo\nEMOJI=🔐"
    encoded = encrypt(content, PASSWORD)
    assert decrypt(encoded, PASSWORD) == content
