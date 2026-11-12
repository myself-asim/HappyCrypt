from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.security.session import require_session
from backend.services.password_analyzer import analyze_password
from backend.services.vault_service import list_credentials

router = APIRouter(prefix="/api/security", tags=["security"])


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    session = require_session(request, unlocked=True)
    items = list_credentials(db, session.key)
    total = len(items)

    weak = 0
    strong = 0
    reused_map = Counter()
    analyses = {}
    now = datetime.now(timezone.utc)
    outdated_days = 180

    weak_items = []
    reused_items = []
    outdated_items = []

    for item in items:
        pwd = item.get("password") or ""
        reused_map[pwd] += 1
        analysis = analyze_password(pwd)
        analyses[item["id"]] = analysis
        label = analysis["label"]
        if label in ("Very Weak", "Weak", "Medium"):
            weak += 1
            weak_items.append({"id": item["id"], "website_name": item["website_name"], "label": label})
        else:
            strong += 1
        updated = item.get("updated_at")
        if updated:
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            if now - updated > timedelta(days=outdated_days):
                outdated_items.append({"id": item["id"], "website_name": item["website_name"], "updated_at": item["updated_at"]})

    reused_count = 0
    for item in items:
        pwd = item.get("password") or ""
        if reused_map[pwd] > 1:
            reused_count += 1
            reused_items.append({"id": item["id"], "website_name": item["website_name"], "count": reused_map[pwd]})

    # dedupe reused display
    seen = set()
    reused_unique = []
    for r in reused_items:
        if r["id"] not in seen:
            seen.add(r["id"])
            reused_unique.append(r)

    recent_modified = sorted(items, key=lambda x: x["updated_at"], reverse=True)[:5]
    recent_added = sorted(items, key=lambda x: x["created_at"], reverse=True)[:5]

    return {
        "total_credentials": total,
        "weak_passwords": weak,
        "strong_passwords": strong,
        "reused_passwords": reused_count,
        "overall": {
            "score": 0 if total == 0 else max(0, min(100, round((strong / total) * 100 - (reused_count / max(1,total)) * 20))),
        },
        "weak_items": weak_items[:10],
        "reused_items": reused_unique[:10],
        "potentially_outdated_items": outdated_items[:10],
        "recently_modified": [{"id": i["id"], "website_name": i["website_name"], "updated_at": i["updated_at"]} for i in recent_modified],
        "recently_added": [{"id": i["id"], "website_name": i["website_name"], "created_at": i["created_at"]} for i in recent_added],
    }
