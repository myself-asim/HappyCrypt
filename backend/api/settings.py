from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.config import APP_NAME, APP_VERSION, BACKUP_DIR, DB_PATH
from backend.database import get_db
from backend.schemas import SettingsUpdate
from backend.security import authentication
from backend.security.session import require_session

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings(request: Request, db: Session = Depends(get_db)):
    session = require_session(request, unlocked=False)
    initialized = authentication.is_initialized(db)
    settings = authentication.get_settings(db) if initialized else {}
    return {
        "initialized": initialized,
        "locked": bool(session.locked or not session.key),
        "settings": settings,
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "database_path": str(DB_PATH),
            "backup_dir": str(BACKUP_DIR),
            "offline": True,
        },
    }


@router.put("")
def update_settings(payload: SettingsUpdate, request: Request, db: Session = Depends(get_db)):
    session = require_session(request, unlocked=True)
    try:
        updates = payload.model_dump(exclude_unset=True)
        settings = authentication.update_settings(db, updates)
        # apply auto-lock to active session
        if "auto_lock_minutes" in settings:
            session.auto_lock_minutes = int(settings["auto_lock_minutes"])
        return {"ok": True, "settings": settings}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
