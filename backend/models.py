from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class VaultMetadata(Base):
    __tablename__ = "vault_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    # Random salt for Argon2id key derivation
    kdf_salt: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    kdf_time_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    kdf_memory_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    kdf_parallelism: Mapped[int] = mapped_column(Integer, nullable=False)
    kdf_hash_len: Mapped[int] = mapped_column(Integer, nullable=False)
    # Encrypted verifier blob (nonce+ciphertext) used to validate master password
    verifier_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    # JSON settings (auto-lock, clipboard timeout, theme, etc.)
    settings_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # AES-256-GCM nonce + ciphertext+tag (combined) of JSON payload
    encrypted_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
