from __future__ import annotations

import os

from argon2.low_level import Type, hash_secret_raw

from backend.config import (
    ARGON2_HASH_LEN,
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_SALT_LEN,
    ARGON2_TIME_COST,
)


def generate_salt(length: int = ARGON2_SALT_LEN) -> bytes:
    return os.urandom(length)


def derive_key(
    master_password: str,
    salt: bytes,
    time_cost: int = ARGON2_TIME_COST,
    memory_cost: int = ARGON2_MEMORY_COST,
    parallelism: int = ARGON2_PARALLELISM,
    hash_len: int = ARGON2_HASH_LEN,
) -> bytes:
    if not isinstance(master_password, str) or master_password == "":
        raise ValueError("Master password must be a non-empty string")
    return hash_secret_raw(
        secret=master_password.encode("utf-8"),
        salt=salt,
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        hash_len=hash_len,
        type=Type.ID,
    )
