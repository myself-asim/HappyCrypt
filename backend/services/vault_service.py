from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Credential
from backend.security.encryption import decrypt_json, encrypt_json


SENSITIVE_FIELDS = ["website_name", "website_url", "username", "email", "password", "notes"]


def _aad(cred_id: str) -> bytes:
    return f"cred:{cred_id}".encode("utf-8")


def _normalize_payload(data: dict) -> dict:
    return {
        "website_name": (data.get("website_name") or "").strip(),
        "website_url": (data.get("website_url") or "").strip(),
        "username": (data.get("username") or "").strip(),
        "email": (data.get("email") or "").strip(),
        "password": data.get("password") or "",
        "notes": data.get("notes") or "",
    }


def list_credentials(db: Session, key: bytes) -> list[dict]:
    creds = list(db.scalars(select(Credential)).all())
    result = []
    for c in creds:
        payload = decrypt_json(key, c.encrypted_blob, aad=_aad(c.id))
        result.append({
            "id": c.id,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            **_normalize_payload(payload),
        })
    # default sort: recently modified desc
    result.sort(key=lambda x: x["updated_at"], reverse=True)
    return result


def get_credential(db: Session, key: bytes, cred_id: str) -> dict | None:
    c = db.get(Credential, cred_id)
    if not c:
        return None
    payload = decrypt_json(key, c.encrypted_blob, aad=_aad(c.id))
    return {
        "id": c.id,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
        **_normalize_payload(payload),
    }


def create_credential(db: Session, key: bytes, data: dict) -> dict:
    import uuid
    payload = _normalize_payload(data)
    if not payload["website_name"]:
        raise ValueError("Website/Application name is required")
    if not payload["password"]:
        raise ValueError("Password is required")
    cred_id = str(uuid.uuid4())
    encrypted_blob = encrypt_json(key, payload, aad=_aad(cred_id))
    now = datetime.now(timezone.utc)
    c = Credential(id=cred_id, encrypted_blob=encrypted_blob, created_at=now, updated_at=now)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {
        "id": c.id,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
        **payload,
    }


def update_credential(db: Session, key: bytes, cred_id: str, updates: dict) -> dict | None:
    c = db.get(Credential, cred_id)
    if not c:
        return None
    payload = decrypt_json(key, c.encrypted_blob, aad=_aad(c.id))
    payload = _normalize_payload(payload)
    for field in SENSITIVE_FIELDS:
        if field in updates and updates[field] is not None:
            payload[field] = updates[field]
    payload = _normalize_payload(payload)
    if not payload["website_name"]:
        raise ValueError("Website/Application name is required")
    if not payload["password"]:
        raise ValueError("Password is required")
    c.encrypted_blob = encrypt_json(key, payload, aad=_aad(c.id))
    c.updated_at = datetime.now(timezone.utc)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {
        "id": c.id,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
        **payload,
    }


def delete_credential(db: Session, cred_id: str) -> bool:
    c = db.get(Credential, cred_id)
    if not c:
        return False
    db.delete(c)
    db.commit()
    return True


def search_credentials(items: list[dict], query: str) -> list[dict]:
    q = (query or "").strip().lower()
    if not q:
        return items
    def match(item: dict) -> bool:
        return (
            q in (item.get("website_name") or "").lower()
            or q in (item.get("website_url") or "").lower()
            or q in (item.get("username") or "").lower()
            or q in (item.get("email") or "").lower()
        )
    return [i for i in items if match(i)]
