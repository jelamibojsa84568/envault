"""Encryption and decryption utilities for envault using AES-GCM."""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
ITERATIONS = 260_000


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a password and salt using PBKDF2-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(password.encode())


def encrypt(plaintext: str, password: str) -> str:
    """Encrypt plaintext with the given password.

    Returns a base64-encoded string containing salt + nonce + ciphertext.
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode()


def decrypt(encoded: str, password: str) -> str:
    """Decrypt a base64-encoded payload produced by :func:`encrypt`.

    Raises ``ValueError`` on authentication failure or bad password.
    """
    try:
        payload = base64.b64decode(encoded)
    except Exception as exc:
        raise ValueError("Invalid encoded payload.") from exc

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed — wrong password or corrupted data.") from exc

    return plaintext.decode()
