# mapproxy-api

[![CI](https://github.com/g3w-suite/maproxy-api/actions/workflows/ci.yml/badge.svg)](https://github.com/g3w-suite/maproxy-api/actions/workflows/ci.yml)

REST API to generate and manage [MapProxy](https://mapproxy.org/) YAML
configurations. Port of the `g3w-admin-mapproxy` plugin workflow, standalone
and framework-agnostic (no Django/QGIS required).

## Quickstart (local)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip3 install -e ".[dev]"

cp .env.example .env
cp .env.secrets.example .env.secrets

# generate a password hash for the admin user and paste it into .env.secrets
# as ADMIN_PASSWORD_HASH
python3 -m app.cli hash mysecret

WATCHFILES_FORCE_POLLING=true uvicorn app.main:app --reload --reload-dir app
# open http://localhost:8000/docs
```

Env files are split in two so Docker Compose interpolation never touches the
bcrypt hash:

- `.env` — plain values used by Compose `${...}` substitution and by the app
  during local dev. Must not contain `$`.
- `.env.secrets` — bcrypt hash, JWT secret, other auth config. Delivered to
  the container verbatim via `env_file: format: raw`, and also loaded by
  pydantic-settings for local dev.

`WATCHFILES_FORCE_POLLING=true` avoids `Too many open files (os error 24)` when
the inotify `max_user_instances` limit is exhausted by other tools (VS Code,
etc.). On systems where inotify has room, you can drop it:

```bash
uvicorn app.main:app --reload --reload-dir app
```

## Quickstart (Docker)

```bash
docker compose up --build
# API:      http://localhost:8000/docs
# MapProxy: http://localhost:8080/demo/
```

## Production (Docker + Nginx reverse proxy)

```bash
docker compose -f docker-compose-prod.yml up --build -d
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

### HTTPS / SSL with Let's Encrypt

`docker-compose-prod.yml` and `docker/nginx.conf` are pre-configured to work with Let's Encrypt via a `certbot` sidecar container.

#### 1. Start the stack in HTTP mode
Start the containers so Nginx is listening on port 80 and can serve the ACME challenge:

```bash
docker compose -f docker-compose-prod.yml up -d
```

#### 2. Obtain certificates via Certbot
Run the Certbot container to complete the HTTP-01 challenge (replace with your domain and email):

```bash
docker compose -f docker-compose-prod.yml run --rm certbot certonly \
    --webroot --webroot-path /var/www/certbot \
    -d example.com \
    --email admin@example.com \
    --agree-tos --no-eff-email
```

#### 3. Enable HTTPS in Nginx
Once certificates are generated, enable HTTPS in [docker/nginx.conf](docker/nginx.conf):
- Replace `example.com` with your actual domain in the SSL block.
- Uncomment the `server { listen 443 ssl; ... }` block and the HTTP-to-HTTPS redirect (`return 301 https://$host$request_uri;`) in [docker/nginx.conf](docker/nginx.conf) (or adapt from [docker/nginx-ssl.conf.example](docker/nginx-ssl.conf.example)).
- Update `.env`:
  ```bash
  MAPPROXY_PUBLIC_URL=https://example.com/mapproxy
  ```

#### 4. Reload Nginx
Reload Nginx without downtime:

```bash
docker compose -f docker-compose-prod.yml exec nginx nginx -s reload
```

#### Automatic renewals
The `certbot` container continuously runs in the background and attempts renewal every 12 hours. Set up a daily cron job to reload Nginx so renewed certificates are reloaded into memory:

```bash
0 3 * * * cd /path/to/mapproxy_api && docker compose -f docker-compose-prod.yml exec -T nginx nginx -s reload
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
