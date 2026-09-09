from pathlib import Path


def test_create_layer_writes_yaml_and_meta(client, auth_headers, layer_payload, settings):
    r = client.post("/layers", json=layer_payload, headers=auth_headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["layer_name"] == "roads"
    assert body["tms_url"].startswith("http")
    yaml_p = settings.mapproxy_conf_dir / "mapproxy_conf_roads.yaml"
    meta_p = settings.mapproxy_conf_dir / "mapproxy_conf_roads.meta.json"
    assert yaml_p.is_file()
    assert meta_p.is_file()


def test_create_layer_conflict(client, auth_headers, layer_payload):
    client.post("/layers", json=layer_payload, headers=auth_headers)
    r = client.post("/layers", json=layer_payload, headers=auth_headers)
    assert r.status_code == 409


def test_list_layers(client, auth_headers, layer_payload):
    client.post("/layers", json=layer_payload, headers=auth_headers)
    r = client.get("/layers", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_layer_404(client, auth_headers):
    assert client.get("/layers/nope", headers=auth_headers).status_code == 404


def test_get_yaml(client, auth_headers, layer_payload):
    client.post("/layers", json=layer_payload, headers=auth_headers)
    r = client.get("/layers/roads/yaml", headers=auth_headers)
    assert r.status_code == 200
    assert "layers:" in r.text
    assert "roads" in r.text


def test_update_layer(client, auth_headers, layer_payload):
    client.post("/layers", json=layer_payload, headers=auth_headers)
    payload = {k: v for k, v in layer_payload.items() if k != "layer_name"}
    payload["title"] = "Updated"
    r = client.put("/layers/roads", json=payload, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"


def test_delete_layer(client, auth_headers, layer_payload, settings):
    client.post("/layers", json=layer_payload, headers=auth_headers)
    r = client.delete("/layers/roads", headers=auth_headers)
    assert r.status_code == 204
    yaml_p = settings.mapproxy_conf_dir / "mapproxy_conf_roads.yaml"
    assert not yaml_p.exists()


def test_reset_cache_clears_dirs_and_recreates_yaml(
    client, auth_headers, layer_payload, settings
):
    client.post("/layers", json=layer_payload, headers=auth_headers)
    cache = Path(settings.mapproxy_cache_dir) / "roads_cache_EPSG3857"
    cache.mkdir(parents=True)
    (cache / "dummy.png").write_bytes(b"x")
    r = client.post("/layers/roads/reset-cache", headers=auth_headers)
    assert r.status_code == 200
    assert not cache.exists()
    assert (settings.mapproxy_conf_dir / "mapproxy_conf_roads.yaml").is_file()


def test_invalid_layer_name(client, auth_headers, layer_payload):
    layer_payload["layer_name"] = "Bad Name!"
    r = client.post("/layers", json=layer_payload, headers=auth_headers)
    assert r.status_code == 422
