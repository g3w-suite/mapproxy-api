def _bl_payload():
    return {
        "layer_name": "roads",
        "title": "Roads baselayer",
        "description": "desc",
        "attributions": "© me",
    }


def test_create_base_layer_requires_layer(client, auth_headers):
    r = client.post("/base-layers", json=_bl_payload(), headers=auth_headers)
    assert r.status_code == 404


def test_base_layer_crud(client, auth_headers, layer_payload, settings):
    client.post("/layers", json=layer_payload, headers=auth_headers)
    r = client.post("/base-layers", json=_bl_payload(), headers=auth_headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["servertype"] == "WMTS"
    assert body["url"].startswith("http")
    r = client.get("/base-layers/roads", headers=auth_headers)
    assert r.status_code == 200
    r = client.delete("/base-layers/roads", headers=auth_headers)
    assert r.status_code == 204
    assert client.get("/base-layers/roads", headers=auth_headers).status_code == 404


def test_base_layer_tms_when_epsg_4326(client, auth_headers, layer_payload):
    layer_payload["srs"] = "EPSG:4326"
    client.post("/layers", json=layer_payload, headers=auth_headers)
    r = client.post("/base-layers", json=_bl_payload(), headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["servertype"] == "TMS"
