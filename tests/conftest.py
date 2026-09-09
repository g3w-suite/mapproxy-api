import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")

TEST_PASSWORD = "testpass"


@pytest.fixture
def settings(tmp_path: Path, monkeypatch):
    from app.auth import hash_password
    from app.config import get_settings

    conf = tmp_path / "conf"
    cache = conf / "cache_data"
    conf.mkdir()
    cache.mkdir()

    monkeypatch.setenv("MAPPROXY_CONF_DIR", str(conf))
    monkeypatch.setenv("MAPPROXY_CACHE_DIR", str(cache))
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", hash_password(TEST_PASSWORD))
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    get_settings.cache_clear()
    yield get_settings()
    get_settings.cache_clear()


@pytest.fixture
def client(settings):
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def token(client) -> str:
    r = client.post(
        "/auth/token",
        data={"username": "admin", "password": TEST_PASSWORD},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def auth_headers(token) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def layer_payload() -> dict:
    return {
        "layer_name": "roads",
        "title": "Roads",
        "abstract": "Road network",
        "wms_url": "https://example.org/wms",
        "wms_layers": "roads",
        "srs": "EPSG:3857",
        "bbox_4326": [6.5, 44.0, 13.5, 47.5],
    }
