from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import APP_NAME, APP_VERSION
from backend.models import Credential, VaultMetadata
from backend.security.authentication import get_meta, get_settings

BACKUP_FORMAT = "happycrypt-backup"
BACKUP_VERSION = 1


def _b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _b64d(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def _canonical_json(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def export_backup(db: Session) -> bytes:
    meta = get_meta(db)
    if not meta:
        raise ValueError("Vault not initialized")
    creds = list(db.scalars(select(Credential)).all())
    payload = {
        "format": BACKUP_FORMAT,
        "version": BACKUP_VERSION,
        "app": APP_NAME,
        "app_version": APP_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "kdf_salt": _b64e(meta.kdf_salt),
            "kdf_time_cost": meta.kdf_time_cost,
            "kdf_memory_cost": meta.kdf_memory_cost,
            "kdf_parallelism": meta.kdf_parallelism,
            "kdf_hash_len": meta.kdf_hash_len,
            "verifier_ciphertext": _b64e(meta.verifier_ciphertext),
            "settings_json": meta.settings_json,
            "created_at": meta.created_at.isoformat() if meta.created_at else None,
            "updated_at": meta.updated_at.isoformat() if meta.updated_at else None,
        },
        "credentials": [
            {
                "id": c.id,
                "encrypted_blob": _b64e(c.encrypted_blob),
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in creds
        ],
    }
    checksum = hashlib.sha256(_canonical_json(payload)).hexdigest()
    envelope = {"checksum_sha256": checksum, "payload": payload}
    return json.dumps(envelope, indent=2).encode("utf-8")


def import_backup(db: Session, backup_bytes: bytes) -> dict:
    try:
        envelope = json.loads(backup_bytes.decode("utf-8"))
    except Exception as e:
        raise ValueError("Backup file is not valid JSON") from e
    if not isinstance(envelope, dict) or "payload" not in envelope or "checksum_sha256" not in envelope:
        raise ValueError("Invalid backup format")
    payload = envelope["payload"]
    expected = envelope["checksum_sha256"]
    actual = hashlib.sha256(_canonical_json(payload)).hexdigest()
    if actual != expected:
        raise ValueError("Backup integrity check failed")
    if payload.get("format") != BACKUP_FORMAT:
        raise ValueError("Unsupported backup format")
    if int(payload.get("version", 0)) != BACKUP_VERSION:
        raise ValueError("Unsupported backup version")
    meta_d = payload.get("metadata") or {}
    creds_d = payload.get("credentials") or []

    # Validate required metadata fields
    required_meta = [
        "kdf_salt", "kdf_time_cost", "kdf_memory_cost", "kdf_parallelism",
        "kdf_hash_len", "verifier_ciphertext", "settings_json",
    ]
    for k in required_meta:
        if k not in meta_d:
            raise ValueError(f"Backup missing metadata field: {k}")

    try:
        # Replace vault contents transactionally
        db.query(Credential).delete()
        db.query(VaultMetadata).delete()
        db.flush()

        meta = VaultMetadata(
            id=1,
            kdf_salt=_b64d(meta_d["kdf_salt"]),
            kdf_time_cost=int(meta_d["kdf_time_cost"]),
            kdf_memory_cost=int(meta_d["kdf_memory_cost"]),
            kdf_parallelism=int(meta_d["kdf_parallelism"]),
            kdf_hash_len=int(meta_d["kdf_hash_len"]),
            verifier_ciphertext=_b64d(meta_d["verifier_ciphertext"]),
            settings_json=str(meta_d.get("settings_json") or "{}"),
        )
        db.add(meta)
        for c in creds_d:
            cred = Credential(
                id=str(c["id"]),
                encrypted_blob=_b64d(c["encrypted_blob"]),
            )
            # preserve timestamps if present
            if c.get("created_at"):
                try:
                    cred.created_at = datetime.fromisoformat(c["created_at"])
                except Exception:
                    pass
            if c.get("updated_at"):
                try:
                    cred.updated_at = datetime.fromisoformat(c["updated_at"])
                except Exception:
                    pass
            db.add(cred)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"imported_credentials": len(creds_d), "version": BACKUP_VERSION}
