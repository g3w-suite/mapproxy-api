# mapproxy-api

[![CI](https://github.com/g3w-suite/maproxy-api/actions/workflows/ci.yml/badge.svg)](https://github.com/g3w-suite/maproxy-api/actions/workflows/ci.yml)

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

WATCHFILES_FORCE_POLLING=true uvicorn app.main:app --reload --reload-dir app
# open http://localhost:8000/docs
```

`WATCHFILES_FORCE_POLLING=true` avoids `Too many open files (os error 24)` when
the inotify `max_user_instances` limit is exhausted by other tools (VS Code,
etc.). On systems where inotify has room, you can drop it:

```bash
uvicorn app.main:app --reload --reload-dir app
```

## Quickstart (Docker)

```bash
docker compose --env-file /dev/null up --build
# API:      http://localhost:8000/docs
# MapProxy: http://localhost:8080/demo/
```

`--env-file /dev/null` prevents Docker Compose from re-interpolating `$` inside
the bcrypt hash contained in `.env`. The `.env` values are still delivered to
the container via the `env_file: format: raw` directive in `docker-compose.yml`.

## Production (Docker + Nginx reverse proxy)

```bash
docker compose -f docker-compose-prod.yml --env-file /dev/null up --build -d
# API:      http://localhost/docs
# MapProxy: http://localhost/mapproxy/<layer_name>/service?
```

Differences from the dev compose:

- Nginx on port 80 is the only exposed service; `api` and `mapproxy` are
  reachable only inside the docker network.
- MapProxy runs under `gunicorn` (`mapproxy.multiapp:make_wsgi_app`), not the
  built-in development server.
- `MAPPROXY_PUBLIC_URL` is set to `http://localhost/mapproxy` so URLs returned
  by the API point through the reverse proxy.
- Nginx routes: `/mapproxy/...` → mapproxy sidecar, everything else → api.

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
