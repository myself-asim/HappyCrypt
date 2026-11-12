from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

from fastapi import Header, HTTPException, Request, status

from backend.config import SESSION_COOKIE_NAME


@dataclass
class SessionData:
    token: str
    key: bytes
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    locked: bool = False
    auto_lock_minutes: int = 10


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}
        self._lock = threading.RLock()

    def create(self, key: bytes, auto_lock_minutes: int) -> SessionData:
        token = secrets.token_urlsafe(32)
        session = SessionData(token=token, key=key, auto_lock_minutes=auto_lock_minutes)
        with self._lock:
            self._sessions[token] = session
        return session

    def get(self, token: str | None) -> Optional[SessionData]:
        if not token:
            return None
        with self._lock:
            session = self._sessions.get(token)
            if not session:
                return None
            # Auto-lock on inactivity
            if not session.locked and session.auto_lock_minutes > 0:
                idle_seconds = time.time() - session.last_active
                if idle_seconds > session.auto_lock_minutes * 60:
                    session.locked = True
                    session.key = b""  # clear key from active use marker? keep object but require unlock
            return session

    def touch(self, token: str) -> None:
        with self._lock:
            session = self._sessions.get(token)
            if session and not session.locked:
                session.last_active = time.time()

    def lock(self, token: str) -> None:
        with self._lock:
            session = self._sessions.get(token)
            if session:
                session.locked = True
                # keep key? no, must not keep usable state unnecessarily; but unlock needs rederive.
                session.key = b""

    def invalidate(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)

    def unlock(self, token: str, key: bytes) -> None:
        with self._lock:
            session = self._sessions.get(token)
            if session:
                session.key = key
                session.locked = False
                session.last_active = time.time()


session_manager = SessionManager()

ALLOWED_ORIGINS = {"http://127.0.0.1:8000", "http://localhost:8000"}


def enforce_local_origin(request: Request) -> None:
    # For browser requests, enforce Origin/Referer to mitigate unauthorized local cross-site calls.
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    host = request.headers.get("host")
    if origin and origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden origin")
    if referer and not any(referer.startswith(o) for o in ALLOWED_ORIGINS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden referer")
    if host not in {"127.0.0.1:8000", "localhost:8000"}:
        # Allow test clients/localhost variants carefully
        if not host.startswith("127.0.0.1") and not host.startswith("localhost"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden host")


def get_session_token(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE_NAME)


def require_session(request: Request, unlocked: bool = True) -> SessionData:
    enforce_local_origin(request)
    token = get_session_token(request)
    session = session_manager.get(token)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if unlocked and (session.locked or not session.key):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Vault is locked")
    if unlocked:
        session_manager.touch(session.token)
    return session
