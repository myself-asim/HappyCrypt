from __future__ import annotations

import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE = 12


class EncryptionError(Exception):
    pass


class DecryptionError(Exception):
    pass


def encrypt_bytes(key: bytes, plaintext: bytes, aad: bytes | None = None) -> bytes:
    if len(key) != 32:
        raise EncryptionError("Key must be 256 bits")
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce + ciphertext


def decrypt_bytes(key: bytes, blob: bytes, aad: bytes | None = None) -> bytes:
    if len(key) != 32:
        raise DecryptionError("Key must be 256 bits")
    if len(blob) < NONCE_SIZE + 16:
        raise DecryptionError("Ciphertext blob is too short")
    nonce = blob[:NONCE_SIZE]
    ciphertext = blob[NONCE_SIZE:]
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, aad)
    except Exception as e:
        raise DecryptionError("Decryption failed or data tampered") from e


def encrypt_json(key: bytes, data: Any, aad: bytes | None = None) -> bytes:
    plaintext = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return encrypt_bytes(key, plaintext, aad)


def decrypt_json(key: bytes, blob: bytes, aad: bytes | None = None) -> Any:
    plaintext = decrypt_bytes(key, blob, aad)
    try:
        return json.loads(plaintext.decode("utf-8"))
    except Exception as e:
        raise DecryptionError("Invalid decrypted payload") from e
