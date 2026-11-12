from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import (
    ARGON2_HASH_LEN,
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
    DEFAULT_AUTO_LOCK_MINUTES,
    DEFAULT_CLIPBOARD_CLEAR_SECONDS,
)
from backend.models import Credential, VaultMetadata
from backend.security.encryption import decrypt_json, encrypt_json
from backend.security.key_derivation import derive_key, generate_salt

VERIFIER_PLAINTEXT = {"app": "HappyCrypt", "verifier": "ok"}


def utcnow():
    return datetime.now(timezone.utc)


def is_initialized(db: Session) -> bool:
    return db.scalar(select(VaultMetadata).where(VaultMetadata.id == 1)) is not None


def get_meta(db: Session) -> VaultMetadata | None:
    return db.scalar(select(VaultMetadata).where(VaultMetadata.id == 1))


def _derive_from_meta(master_password: str, meta: VaultMetadata) -> bytes:
    return derive_key(
        master_password,
        meta.kdf_salt,
        time_cost=meta.kdf_time_cost,
        memory_cost=meta.kdf_memory_cost,
        parallelism=meta.kdf_parallelism,
        hash_len=meta.kdf_hash_len,
    )


def initialize_vault(db: Session, master_password: str) -> VaultMetadata:
    if is_initialized(db):
        raise ValueError("Vault already initialized")
    if not master_password or len(master_password) < 8:
        raise ValueError("Master password must be at least 8 characters")
    salt = generate_salt()
    key = derive_key(master_password, salt)
    verifier = encrypt_json(key, VERIFIER_PLAINTEXT, aad=b"vault-meta:1")
    settings = {
        "auto_lock_minutes": DEFAULT_AUTO_LOCK_MINUTES,
        "clipboard_clear_seconds": DEFAULT_CLIPBOARD_CLEAR_SECONDS,
        "theme": "dark",
    }
    meta = VaultMetadata(
        id=1,
        kdf_salt=salt,
        kdf_time_cost=ARGON2_TIME_COST,
        kdf_memory_cost=ARGON2_MEMORY_COST,
        kdf_parallelism=ARGON2_PARALLELISM,
        kdf_hash_len=ARGON2_HASH_LEN,
        verifier_ciphertext=verifier,
        settings_json=json.dumps(settings),
    )
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta


def verify_master_password(db: Session, master_password: str) -> tuple[VaultMetadata, bytes]:
    meta = get_meta(db)
    if not meta:
        raise ValueError("Vault not initialized")
    key = _derive_from_meta(master_password, meta)
    # Will raise if wrong key/tampered
    data = decrypt_json(key, meta.verifier_ciphertext, aad=b"vault-meta:1")
    if data != VERIFIER_PLAINTEXT:
        raise ValueError("Invalid verifier")
    return meta, key


def change_master_password(db: Session, current_password: str, new_password: str) -> VaultMetadata:
    if not new_password or len(new_password) < 8:
        raise ValueError("New master password must be at least 8 characters")
    # Authenticate with current password (also checks init)
    meta, old_key = verify_master_password(db, current_password)

    # Decrypt all credentials with old key
    creds = list(db.scalars(select(Credential)).all())
    decrypted_items = []
    for c in creds:
        payload = decrypt_json(old_key, c.encrypted_blob, aad=f"cred:{c.id}".encode("utf-8"))
        decrypted_items.append((c, payload))

    # Prepare new key/material
    new_salt = generate_salt()
    new_key = derive_key(
        new_password,
        new_salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=ARGON2_HASH_LEN,
    )
    new_verifier = encrypt_json(new_key, VERIFIER_PLAINTEXT, aad=b"vault-meta:1")

    # Transactional/crash-safe-ish update: stage all new blobs, verify, then commit once
    try:
        for c, payload in decrypted_items:
            c.encrypted_blob = encrypt_json(new_key, payload, aad=f"cred:{c.id}".encode("utf-8"))
            c.updated_at = utcnow()
        # Verify re-encryption before finalizing metadata
        for c, payload in decrypted_items:
            check = decrypt_json(new_key, c.encrypted_blob, aad=f"cred:{c.id}".encode("utf-8"))
            if check != payload:
                raise ValueError("Re-encryption verification failed")

        meta.kdf_salt = new_salt
        meta.kdf_time_cost = ARGON2_TIME_COST
        meta.kdf_memory_cost = ARGON2_MEMORY_COST
        meta.kdf_parallelism = ARGON2_PARALLELISM
        meta.kdf_hash_len = ARGON2_HASH_LEN
        meta.verifier_ciphertext = new_verifier
        meta.updated_at = utcnow()
        db.add(meta)
        db.commit()
        db.refresh(meta)
        return meta
    except Exception:
        db.rollback()
        raise


def get_settings(db: Session) -> dict:
    meta = get_meta(db)
    if not meta:
        return {
            "auto_lock_minutes": DEFAULT_AUTO_LOCK_MINUTES,
            "clipboard_clear_seconds": DEFAULT_CLIPBOARD_CLEAR_SECONDS,
            "theme": "dark",
        }
    try:
        settings = json.loads(meta.settings_json or "{}")
    except Exception:
        settings = {}
    settings.setdefault("auto_lock_minutes", DEFAULT_AUTO_LOCK_MINUTES)
    settings.setdefault("clipboard_clear_seconds", DEFAULT_CLIPBOARD_CLEAR_SECONDS)
    settings.setdefault("theme", "dark")
    return settings


def update_settings(db: Session, updates: dict) -> dict:
    meta = get_meta(db)
    if not meta:
        raise ValueError("Vault not initialized")
    settings = get_settings(db)
    for k in ("auto_lock_minutes", "clipboard_clear_seconds", "theme"):
        if k in updates and updates[k] is not None:
            settings[k] = updates[k]
    # basic validation
    settings["auto_lock_minutes"] = max(1, int(settings["auto_lock_minutes"]))
    settings["clipboard_clear_seconds"] = max(5, int(settings["clipboard_clear_seconds"]))
    if settings["theme"] not in ("dark", "light"):
        settings["theme"] = "dark"
    meta.settings_json = json.dumps(settings)
    meta.updated_at = utcnow()
    db.add(meta)
    db.commit()
    return settings
