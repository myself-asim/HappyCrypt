from backend.services.password_analyzer import analyze_password
from backend.services.password_generator import generate_password


def test_password_generator_uses_selected_sets():
    pw = generate_password(length=24, uppercase=True, lowercase=True, numbers=True, special=True)
    assert len(pw) == 24
    assert any(c.islower() for c in pw)
    assert any(c.isupper() for c in pw)
    assert any(c.isdigit() for c in pw)
    assert any(not c.isalnum() for c in pw)


def test_password_generator_validation():
    try:
        generate_password(uppercase=False, lowercase=False, numbers=False, special=False)
        assert False, "should raise"
    except ValueError:
        pass


def test_password_analyzer_labels():
    weak = analyze_password("123")
    strong = analyze_password("V3ry$trong&LongPassphrase2026!")
    assert weak["label"] in ("Very Weak", "Weak", "Medium")
    assert strong["label"] in ("Strong", "Very Strong")
    assert 0 <= weak["score"] <= 4 and 0 <= strong["score"] <= 4


def test_unauthorized_api_access(app_ctx):
    client = app_ctx["client"]
    # not initialized/authenticated
    r = client.get("/api/credentials")
    assert r.status_code in (401, 423)
    r = client.get("/api/settings")
    assert r.status_code == 401


def test_session_lock_blocks_vault(app_ctx):
    client = app_ctx["client"]
    client.post("/api/auth/setup", json={"master_password": "StrongPass123!", "confirm_password": "StrongPass123!"})
    client.post("/api/auth/lock")
    r = client.get("/api/credentials")
    assert r.status_code == 423
