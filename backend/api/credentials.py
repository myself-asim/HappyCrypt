from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import CredentialCreate, CredentialSummary, CredentialUpdate
from backend.security.session import require_session
from backend.services import vault_service

router = APIRouter(prefix="/api/credentials", tags=["credentials"])


@router.get("")
def list_credentials(
    request: Request,
    q: str = Query(default=""),
    sort: str = Query(default="updated_desc"),
    db: Session = Depends(get_db),
):
    session = require_session(request, unlocked=True)
    items = vault_service.list_credentials(db, session.key)
    items = vault_service.search_credentials(items, q)
    if sort == "name_asc":
        items.sort(key=lambda x: (x.get("website_name") or "").lower())
    elif sort == "name_desc":
        items.sort(key=lambda x: (x.get("website_name") or "").lower(), reverse=True)
    elif sort == "created_desc":
        items.sort(key=lambda x: x["created_at"], reverse=True)
    elif sort == "created_asc":
        items.sort(key=lambda x: x["created_at"])
    elif sort == "updated_asc":
        items.sort(key=lambda x: x["updated_at"])
    else:  # updated_desc
        items.sort(key=lambda x: x["updated_at"], reverse=True)

    summaries = [
        {
            "id": i["id"],
            "website_name": i["website_name"],
            "website_url": i["website_url"],
            "username": i["username"],
            "email": i["email"],
            "created_at": i["created_at"],
            "updated_at": i["updated_at"],
        }
        for i in items
    ]
    return {"items": summaries, "count": len(summaries)}


@router.get("/{cred_id}")
def get_credential(cred_id: str, request: Request, db: Session = Depends(get_db)):
    session = require_session(request, unlocked=True)
    item = vault_service.get_credential(db, session.key, cred_id)
    if not item:
        raise HTTPException(status_code=404, detail="Credential not found")
    return item


@router.post("")
def create_credential(payload: CredentialCreate, request: Request, db: Session = Depends(get_db)):
    session = require_session(request, unlocked=True)
    try:
        item = vault_service.create_credential(db, session.key, payload.model_dump())
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{cred_id}")
def update_credential(cred_id: str, payload: CredentialUpdate, request: Request, db: Session = Depends(get_db)):
    session = require_session(request, unlocked=True)
    try:
        item = vault_service.update_credential(db, session.key, cred_id, payload.model_dump(exclude_unset=True))
        if not item:
            raise HTTPException(status_code=404, detail="Credential not found")
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{cred_id}")
def delete_credential(cred_id: str, request: Request, db: Session = Depends(get_db)):
    require_session(request, unlocked=True)
    ok = vault_service.delete_credential(db, cred_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"ok": True}
