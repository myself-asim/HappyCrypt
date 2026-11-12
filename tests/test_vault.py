import sqlite3


def setup_vault(client):
    client.post("/api/auth/setup", json={"master_password": "StrongPass123!", "confirm_password": "StrongPass123!"})


def test_credential_crud(app_ctx):
    client = app_ctx["client"]
    setup_vault(client)
    # create
    r = client.post("/api/credentials", json={
        "website_name": "Example", "website_url": "https://example.com",
        "username": "alice", "email": "a@example.com", "password": "secret1", "notes": "note"
    })
    assert r.status_code == 200
    cred = r.json()
    cid = cred["id"]
    assert cred["website_name"] == "Example" and cred["password"] == "secret1"

    # list
    r = client.get("/api/credentials")
    assert r.status_code == 200 and r.json()["count"] == 1

    # get
    r = client.get(f"/api/credentials/{cid}")
    assert r.status_code == 200 and r.json()["username"] == "alice"

    # update
    r = client.put(f"/api/credentials/{cid}", json={"password": "secret2", "username": "bob"})
    assert r.status_code == 200 and r.json()["password"] == "secret2" and r.json()["username"] == "bob"

    # search
    r = client.get("/api/credentials", params={"q": "Example"})
    assert r.json()["count"] == 1
    r = client.get("/api/credentials", params={"q": "nope"})
    assert r.json()["count"] == 0

    # delete
    r = client.delete(f"/api/credentials/{cid}")
    assert r.status_code == 200
    assert client.get("/api/credentials").json()["count"] == 0


def test_credentials_not_plaintext_in_db(app_ctx):
    client = app_ctx["client"]
    db_path = app_ctx["db_path"]
    setup_vault(client)
    secret_pw = "PLAINTEXT_SHOULD_NOT_APPEAR_123!"
    client.post("/api/credentials", json={
        "website_name": "SecretSite", "website_url": "https://secret.example",
        "username": "secretuser", "email": "secret@example.com", "password": secret_pw, "notes": "topsecret"
    })
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT encrypted_blob FROM credentials").fetchall()
        assert rows, "credential row expected"
        blob = rows[0][0]
        raw = blob if isinstance(blob, bytes) else str(blob).encode()
        assert b"SecretSite" not in raw
        assert b"secretuser" not in raw
        assert secret_pw.encode() not in raw
    finally:
        conn.close()
