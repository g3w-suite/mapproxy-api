# mapproxy-api

REST API to generate and manage [MapProxy](https://mapproxy.org/) YAML
configurations. Port of the `g3w-admin-mapproxy` plugin workflow, standalone
and framework-agnostic (no Django/QGIS required).

## Quickstart (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# generate a password hash for the admin user
python -m app.cli hash mysecret
# copy the output into .env as ADMIN_PASSWORD_HASH
cp .env.example .env

uvicorn app.main:app --reload
# open http://localhost:8000/docs
```

## Quickstart (Docker)

```bash
docker compose up --build
# API:      http://localhost:8000/docs
# MapProxy: http://localhost:8080/demo/
```

## Typical flow

```bash
# 1. login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
    -d 'username=admin&password=mysecret' | jq -r .access_token)

# 2. create a layer configuration
curl -X POST http://localhost:8000/layers \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "layer_name": "roads",
      "title": "Roads",
      "abstract": "Road network",
      "wms_url": "https://example.org/wms",
      "wms_layers": "roads",
      "srs": "EPSG:3857",
      "bbox_4326": [6.5, 44.0, 13.5, 47.5]
    }'

# 3. reset the cache
curl -X POST http://localhost:8000/layers/roads/reset-cache \
    -H "Authorization: Bearer $TOKEN"

# 4. delete the layer
curl -X DELETE http://localhost:8000/layers/roads \
    -H "Authorization: Bearer $TOKEN"
```
