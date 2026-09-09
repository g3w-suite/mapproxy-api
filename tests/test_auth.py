def test_token_success(client):
    r = client.post("/auth/token", data={"username": "admin", "password": "testpass"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_token_wrong_password(client):
    r = client.post("/auth/token", data={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_protected_without_token(client):
    assert client.get("/layers").status_code == 401


def test_protected_with_invalid_token(client):
    r = client.get("/layers", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


def test_health_public(client):
    assert client.get("/health").status_code == 200
