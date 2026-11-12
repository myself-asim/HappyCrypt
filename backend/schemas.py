from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MasterPasswordSetup(BaseModel):
    master_password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)


class MasterPasswordLogin(BaseModel):
    master_password: str = Field(min_length=1)


class ChangeMasterPassword(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)
    confirm_new_password: str = Field(min_length=8)


class CredentialCreate(BaseModel):
    website_name: str = Field(min_length=1)
    website_url: str = ""
    username: str = ""
    email: str = ""
    password: str = Field(min_length=1)
    notes: str = ""


class CredentialUpdate(BaseModel):
    website_name: Optional[str] = None
    website_url: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None


class CredentialOut(BaseModel):
    id: str
    website_name: str
    website_url: str
    username: str
    email: str
    password: str
    notes: str
    created_at: datetime
    updated_at: datetime


class CredentialSummary(BaseModel):
    id: str
    website_name: str
    website_url: str
    username: str
    email: str
    created_at: datetime
    updated_at: datetime


class GeneratorRequest(BaseModel):
    length: int = Field(default=16, ge=4, le=128)
    uppercase: bool = True
    lowercase: bool = True
    numbers: bool = True
    special: bool = True
    exclude_ambiguous: bool = False


class AnalyzeRequest(BaseModel):
    password: str = Field(min_length=0)


class SettingsUpdate(BaseModel):
    auto_lock_minutes: Optional[int] = Field(default=None, ge=1, le=240)
    clipboard_clear_seconds: Optional[int] = Field(default=None, ge=5, le=300)
    theme: Optional[str] = None


class BackupImportRequest(BaseModel):
    # base64-encoded backup file content sent as JSON for simplicity in local API
    backup_base64: str
