from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.config import SESSION_COOKIE_NAME
from backend.database import get_db
from backend.schemas import ChangeMasterPassword, MasterPasswordLogin, MasterPasswordSetup
from backend.security import authentication
from backend.security.session import enforce_local_origin, get_session_token, require_session, session_manager

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/status")
def auth_status(request: Request, db: Session = Depends(get_db)):
    enforce_local_origin(request)
    initialized = authentication.is_initialized(db)
    token = get_session_token(request)
    session = session_manager.get(token) if token else None
    logged_in = session is not None
    locked = True
    if session:
        locked = bool(session.locked or not session.key)
    return {"initialized": initialized, "logged_in": logged_in, "locked": locked}


@router.post("/setup")
def setup(payload: MasterPasswordSetup, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce_local_origin(request)
    if payload.master_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    try:
        meta = authentication.initialize_vault(db, payload.master_password)
        _, key = authentication.verify_master_password(db, payload.master_password)
        settings = authentication.get_settings(db)
        session = session_manager.create(key, settings.get("auto_lock_minutes", 10))
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session.token,
            httponly=True,
            samesite="strict",
            secure=False,  # localhost
            path="/",
        )
        return {"ok": True, "initialized": True, "locked": False}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(payload: MasterPasswordLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce_local_origin(request)
    try:
        meta, key = authentication.verify_master_password(db, payload.master_password)
        settings = authentication.get_settings(db)
        session = session_manager.create(key, settings.get("auto_lock_minutes", 10))
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session.token,
            httponly=True,
            samesite="strict",
            secure=False,
            path="/",
        )
        return {"ok": True, "locked": False}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid master password")


@router.post("/unlock")
def unlock(payload: MasterPasswordLogin, request: Request, db: Session = Depends(get_db)):
    enforce_local_origin(request)
    token = get_session_token(request)
    session = session_manager.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        _, key = authentication.verify_master_password(db, payload.master_password)
        session_manager.unlock(session.token, key)
        settings = authentication.get_settings(db)
        session.auto_lock_minutes = int(settings.get("auto_lock_minutes", session.auto_lock_minutes))
        return {"ok": True, "locked": False}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid master password")


@router.post("/lock")
def lock(request: Request):
    session = require_session(request, unlocked=False)
    session_manager.lock(session.token)
    return {"ok": True, "locked": True}


@router.post("/logout")
def logout(request: Request, response: Response):
    enforce_local_origin(request)
    token = get_session_token(request)
    if token:
        session_manager.invalidate(token)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"ok": True, "logged_in": False}


@router.post("/change-master")
def change_master(payload: ChangeMasterPassword, request: Request, response: Response, db: Session = Depends(get_db)):
    session = require_session(request, unlocked=True)
    if payload.new_password != payload.confirm_new_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    try:
        authentication.change_master_password(db, payload.current_password, payload.new_password)
        # Invalidate old session after password change
        session_manager.invalidate(session.token)
        response.delete_cookie(SESSION_COOKIE_NAME, path="/")
        return {"ok": True, "logged_in": False, "message": "Master password changed. Please log in again."}
    except ValueError as e:
        msg = str(e)
        code = 401 if "Invalid" in msg or "Decryption" in msg else 400
        raise HTTPException(status_code=code, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to change master password")
