# Plan: MapProxy Config REST API (FastAPI)

> REST API service that replicates the workflow of the
> [`g3w-admin-mapproxy`](../g3w-admin/plugins/g3w-admin-mapproxy) plugin as a
> standalone version: direct JSON input, no DB (filesystem is the source of
> truth), YAML template ported from the plugin, JWT auth, Docker sidecar with
> MapProxy multiapp that automatically detects new YAML files.

## Plugin → API mapping

| Plugin `g3w-admin-mapproxy` | API equivalent |
|---|---|
| `ActiveMapproxyLayerView.form_valid` (active=True) | `POST /layers` + `PUT /layers/{layer_name}` |
| `ActiveMapproxyLayerView.form_valid` (active=False) | `DELETE /layers/{layer_name}` |
| `ResetMapproxyLayerCacheView` | `POST /layers/{layer_name}/reset-cache` |
| `bridges/shared_folder.upsert_cached_layer` | `services/mapproxy_config.py::upsert()` |
| `bridges/shared_folder.delete_cache` | `services/mapproxy_config.py::delete()` |
| `bridges/shared_folder.invalidate_cache` | `services/mapproxy_config.py::invalidate()` |
| `utils/general.py` (`get_grid`, `service_by_epsg`, `_get_supported_srs`) | `services/grids.py` (port without QGIS) |
| `templates/qmapproxy/mapproxy_conf.yaml` | `app/templates/mapproxy_conf.yaml` (Jinja2) |
| `G3WMapproxyLayer` (Django model) | JSON sidecar `mapproxy_conf_<layer_name>.meta.json` |
| `BaseLayer` (core.models) | JSON sidecar `mapproxy_conf_<layer_name>.baselayer.json` |

## Project layout

```
mapproxy_api/
├── app/
│   ├── main.py                     # FastAPI + include_router
│   ├── config.py                   # pydantic-settings
│   ├── auth.py                     # JWT deps, /token
│   ├── cli.py                      # `python -m app.cli hash <pwd>`
│   ├── templates/mapproxy_conf.yaml
│   ├── models/{layer.py, base_layer.py, auth.py}
│   ├── routers/{layers.py, base_layers.py, auth.py, health.py}
│   └── services/{grids.py, mapproxy_config.py, storage.py}
├── tests/{conftest.py, test_layers.py, test_base_layers.py,
│          test_auth.py, test_yaml_rendering.py}
├── mapproxy_multiapp/mapproxy.yaml # sidecar multiapp config
├── Dockerfile, docker-compose.yml
├── pyproject.toml, .env.example, README.md
```

## API contract

### Endpoints

| Method | Path | Auth |
|---|---|---|
| POST | `/auth/token` | – |
| GET | `/health` | – |
| GET | `/layers` | JWT |
| POST | `/layers` | JWT |
| GET | `/layers/{layer_name}` | JWT |
| PUT | `/layers/{layer_name}` | JWT |
| DELETE | `/layers/{layer_name}` | JWT |
| POST | `/layers/{layer_name}/reset-cache` | JWT |
| GET | `/layers/{layer_name}/yaml` | JWT |
| POST | `/base-layers` | JWT |
| GET | `/base-layers/{layer_name}` | JWT |
| DELETE | `/base-layers/{layer_name}` | JWT |

### `Layer` payload

Input JSON (replaces `qdjango.Layer`): `layer_name`, `title`, `abstract`,
`wms_url`, `wms_layers`, `wms_version`, `srs`, `bbox_4326` (list[float, 4]),
`formats`, `additional_srs`.

## Implementation phases

1. **Scaffolding** — `pyproject.toml`, `config.py`, `main.py`, `.env.example`, `README.md`.
2. **Core services** — `grids.py`, YAML template, `storage.py`, `mapproxy_config.py`.
3. **Auth** — `auth.py`, `routers/auth.py`, password hashing CLI.
4. **Routers** — Pydantic models, `layers`/`base_layers`/`health` routers.
5. **Tests** — pytest + YAML snapshot.
6. **Deploy** — Dockerfile, `mapproxy_multiapp/mapproxy.yaml`, `docker-compose.yml`.

## Decisions

- **Filesystem = DB**: no SQLite. `list_layers()` = directory glob. Meta and base layers are JSON sidecars.
- **`layer_name` as ID** (replaces the numeric `layer.pk`): string `[a-z0-9_-]`, unique.
- **No QGIS dependency**: `wms_url` and `bbox_4326` come pre-computed in the JSON body.
- **BaseLayer as JSON sidecar**: consistent with filesystem-only; easy to migrate to a DB later.
- **In-house JWT**: single admin user via env (`ADMIN_USERNAME` + `ADMIN_PASSWORD_HASH` bcrypt).
- **MapProxy reload**: `mapproxy-util serve-multiapp` scans the directory dynamically.
- **MapProxy URLs in responses**: computed from the `MAPPROXY_PUBLIC_URL` env var.
- **No lock on concurrent writes**: last-write-wins, as in the original plugin.
- **Out of scope**: `.qgs` integration, multi-user/roles, tile preview endpoint, metrics, rate limiting.
