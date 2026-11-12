import pytest

from backend.security.encryption import decrypt_bytes, decrypt_json, encrypt_bytes, encrypt_json, DecryptionError


def test_encryption_roundtrip_bytes():
    key = b"0" * 32
    pt = b"secret-data"
    blob = encrypt_bytes(key, pt, aad=b"aad")
    assert blob != pt
    assert decrypt_bytes(key, blob, aad=b"aad") == pt


def test_encryption_unique_nonce():
    key = b"1" * 32
    pt = b"same"
    a = encrypt_bytes(key, pt)
    b = encrypt_bytes(key, pt)
    assert a != b  # unique nonce per operation


def test_ciphertext_tampering_detected():
    key = b"2" * 32
    blob = bytearray(encrypt_bytes(key, b"hello", aad=b"x"))
    blob[-1] ^= 0x01
    with pytest.raises(DecryptionError):
        decrypt_bytes(key, bytes(blob), aad=b"x")


def test_aad_mismatch_detected():
    key = b"3" * 32
    blob = encrypt_bytes(key, b"hello", aad=b"cred:1")
    with pytest.raises(DecryptionError):
        decrypt_bytes(key, blob, aad=b"cred:2")


def test_json_roundtrip():
    key = b"4" * 32
    data = {"site": "Example", "password": "p@ss"}
    blob = encrypt_json(key, data, aad=b"aad")
    assert decrypt_json(key, blob, aad=b"aad") == data
