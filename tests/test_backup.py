import base64


def setup_vault(client):
    client.post("/api/auth/setup", json={"master_password": "StrongPass123!", "confirm_password": "StrongPass123!"})


def test_backup_export_import_and_integrity(app_ctx):
    client = app_ctx["client"]
    setup_vault(client)
    client.post("/api/credentials", json={
        "website_name": "Example", "website_url": "", "username": "u", "email": "", "password": "p", "notes": ""
    })
    # export
    r = client.get("/api/backup/export")
    assert r.status_code == 200
    backup_bytes = r.content
    assert b'"format": "happycrypt-backup"' in backup_bytes
    assert b"Example" not in backup_bytes  # encrypted; name should not appear plaintext
    assert b'"password": "p"' not in backup_bytes

    # tamper -> import fails (must be logged in per API; session still active)
    import json
    env = json.loads(backup_bytes.decode("utf-8"))
    env["payload"]["credentials"][0]["id"] = "tampered-id"
    tampered_b64 = base64.b64encode(json.dumps(env).encode("utf-8")).decode("ascii")
    r = client.post("/api/backup/import", json={"backup_base64": tampered_b64})
    assert r.status_code == 400

    # valid import (after login, since tamper didn't invalidate; but import invalidates on success)
    good_b64 = base64.b64encode(backup_bytes).decode("ascii")
    r = client.post("/api/backup/import", json={"backup_base64": good_b64})
    assert r.status_code == 200
    # session invalidated, must login with backup's master password
    assert client.get("/api/auth/status").json()["logged_in"] is False
    r = client.post("/api/auth/login", json={"master_password": "StrongPass123!"})
    assert r.status_code == 200
    r = client.get("/api/credentials")
    assert r.json()["count"] == 1
