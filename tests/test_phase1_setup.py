import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import config, database, main  # noqa


def test_config_paths_exist():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    assert config.FRONTEND_DIR.exists()
    assert config.DATA_DIR.exists()
    assert config.BACKUP_DIR.exists()


def test_app_health_structure():
    from fastapi.testclient import TestClient
    client = TestClient(main.app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == config.APP_NAME
    assert data["offline"] is True
