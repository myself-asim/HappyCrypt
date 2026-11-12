from backend.security import authentication


def test_master_password_setup_and_login(app_ctx):
    client = app_ctx["client"]
    # status uninitialized
    r = client.get("/api/auth/status")
    assert r.status_code == 200 and r.json()["initialized"] is False

    # setup
    r = client.post("/api/auth/setup", json={"master_password": "StrongPass123!", "confirm_password": "StrongPass123!"})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    st = client.get("/api/auth/status").json()
    assert st["initialized"] is True and st["logged_in"] is True and st["locked"] is False

    # logout
    r = client.post("/api/auth/logout")
    assert r.status_code == 200

    # correct login
    r = client.post("/api/auth/login", json={"master_password": "StrongPass123!"})
    assert r.status_code == 200

    # incorrect login
    client.post("/api/auth/logout")
    r = client.post("/api/auth/login", json={"master_password": "wrong"})
    assert r.status_code == 401


def test_lock_unlock_and_session_expiry_flow(app_ctx):
    client = app_ctx["client"]
    client.post("/api/auth/setup", json={"master_password": "StrongPass123!", "confirm_password": "StrongPass123!"})
    r = client.post("/api/auth/lock")
    assert r.status_code == 200
    st = client.get("/api/auth/status").json()
    assert st["locked"] is True
    # unlock wrong
    r = client.post("/api/auth/unlock", json={"master_password": "bad"})
    assert r.status_code == 401
    # unlock correct
    r = client.post("/api/auth/unlock", json={"master_password": "StrongPass123!"})
    assert r.status_code == 200
    assert client.get("/api/auth/status").json()["locked"] is False


def test_change_master_password_invalidates_session(app_ctx):
    client = app_ctx["client"]
    client.post("/api/auth/setup", json={"master_password": "StrongPass123!", "confirm_password": "StrongPass123!"})
    r = client.post("/api/auth/change-master", json={
        "current_password": "StrongPass123!",
        "new_password": "NewStrongPass123!",
        "confirm_new_password": "NewStrongPass123!",
    })
    assert r.status_code == 200
    st = client.get("/api/auth/status").json()
    assert st["logged_in"] is False
    # old password fails, new works
    assert client.post("/api/auth/login", json={"master_password": "StrongPass123!"}).status_code == 401
    assert client.post("/api/auth/login", json={"master_password": "NewStrongPass123!"}).status_code == 200
