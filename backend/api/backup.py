from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import BackupImportRequest
from backend.security.session import require_session, session_manager
from backend.services.backup_service import export_backup, import_backup

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.get("/export")
def export(request: Request, db: Session = Depends(get_db)):
    # Must be unlocked to ensure user is authenticated owner; backup itself remains encrypted
    require_session(request, unlocked=True)
    try:
        data = export_backup(db)
        return Response(
            content=data,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="happycrypt-backup.json"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import")
def do_import(payload: BackupImportRequest, request: Request, db: Session = Depends(get_db)):
    session = require_session(request, unlocked=False)
    try:
        raw = base64.b64decode(payload.backup_base64.encode("ascii"), validate=True)
        result = import_backup(db, raw)
        # Imported vault may have different master password/verifier; invalidate session for safety
        session_manager.invalidate(session.token)
        return {"ok": True, **result, "message": "Backup imported. Please log in with the backup's master password."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {e}")
