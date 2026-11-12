from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api import auth, backup, credentials, generator, security, settings
from backend.config import APP_NAME, APP_VERSION, FRONTEND_DIR
from backend.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

# Local-only app; restrict to localhost origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": APP_NAME, "version": APP_VERSION, "offline": True}


# API routers
app.include_router(auth.router)
app.include_router(credentials.router)
app.include_router(generator.router)
app.include_router(security.router)
app.include_router(backup.router)
app.include_router(settings.router)

# Serve frontend assets
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")
