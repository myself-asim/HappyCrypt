import importlib
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def app_ctx(tmp_path, monkeypatch):
    # Isolated environment per test
    data_dir = tmp_path / "data"
    backup_dir = tmp_path / "backups"
    data_dir.mkdir()
    backup_dir.mkdir()
    db_path = data_dir / "happycrypt.db"

    import backend.config as config
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    monkeypatch.setattr(config, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(config, "DB_PATH", db_path)

    import backend.database as database
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", TestingSessionLocal)

    # Reload modules that may cache settings/state
    import backend.security.session as session_mod
    session_mod.session_manager._sessions.clear()

    import backend.models  # noqa
    database.Base.metadata.create_all(bind=engine)

    import backend.main as main
    # ensure startup/init uses patched engine (we already created tables)
    app = main.app

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[database.get_db] = override_get_db
    client = TestClient(app, base_url="http://127.0.0.1:8000")
    yield {"client": client, "db_path": db_path, "SessionLocal": TestingSessionLocal, "tmp_path": tmp_path}
    app.dependency_overrides.clear()
    session_mod.session_manager._sessions.clear()
