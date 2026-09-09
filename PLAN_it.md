# Plan: MapProxy Config REST API (FastAPI)

> Servizio REST FastAPI che replica il workflow del plugin
> [`g3w-admin-mapproxy`](../g3w-admin/plugins/g3w-admin-mapproxy) in versione
> standalone: input JSON diretto, nessun DB (source of truth = filesystem),
> template YAML portato dal plugin, auth JWT, sidecar Docker con MapProxy
> multiapp che rileva i nuovi YAML automaticamente.

## Mapping plugin → API

| Plugin `g3w-admin-mapproxy` | Equivalente nell'API |
|---|---|
| `ActiveMapproxyLayerView.form_valid` (active=True) | `POST /layers` + `PUT /layers/{layer_name}` |
| `ActiveMapproxyLayerView.form_valid` (active=False) | `DELETE /layers/{layer_name}` |
| `ResetMapproxyLayerCacheView` | `POST /layers/{layer_name}/reset-cache` |
| `bridges/shared_folder.upsert_cached_layer` | `services/mapproxy_config.py::upsert()` |
| `bridges/shared_folder.delete_cache` | `services/mapproxy_config.py::delete()` |
| `bridges/shared_folder.invalidate_cache` | `services/mapproxy_config.py::invalidate()` |
| `utils/general.py` (`get_grid`, `service_by_epsg`, `_get_supported_srs`) | `services/grids.py` (port senza QGIS) |
| `templates/qmapproxy/mapproxy_conf.yaml` | `app/templates/mapproxy_conf.yaml` (Jinja2) |
| `G3WMapproxyLayer` (Django model) | JSON sidecar `mapproxy_conf_<layer_name>.meta.json` |
| `BaseLayer` (core.models) | JSON sidecar `mapproxy_conf_<layer_name>.baselayer.json` |

## Struttura progetto

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
├── mapproxy_multiapp/mapproxy.yaml # config multiapp del sidecar
├── Dockerfile, docker-compose.yml
├── pyproject.toml, .env.example, README.md
```

## Contratto API

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

Input JSON (sostituisce `qdjango.Layer`): `layer_name`, `title`, `abstract`,
`wms_url`, `wms_layers`, `wms_version`, `srs`, `bbox_4326` (list[float,4]),
`formats`, `additional_srs`.

## Fasi implementative

1. **Scaffolding** — `pyproject.toml`, `config.py`, `main.py`, `.env.example`, `README.md`.
2. **Servizi core** — `grids.py`, template YAML, `storage.py`, `mapproxy_config.py`.
3. **Auth** — `auth.py`, `routers/auth.py`, CLI hash password.
4. **Router** — modelli Pydantic, router `layers`/`base_layers`/`health`.
5. **Test** — pytest + snapshot YAML.
6. **Deploy** — Dockerfile, `mapproxy_multiapp/mapproxy.yaml`, `docker-compose.yml`.

## Decisions

- **Filesystem = DB**: niente SQLite. `list_layers()` = glob su directory. Meta e baselayer come JSON sidecar.
- **`layer_name` come ID** (sostituisce `layer.pk` numerico): stringa `[a-z0-9_-]`, univoca.
- **Nessuna dipendenza QGIS**: `wms_url` e `bbox_4326` già calcolati nel body JSON.
- **BaseLayer come sidecar JSON**: coerente con filesystem-only; migrabile a DB in futuro.
- **JWT interno**: singolo admin via env (`ADMIN_USERNAME` + `ADMIN_PASSWORD_HASH` bcrypt).
- **Reload MapProxy**: `mapproxy-util serve-multiapp` scansiona dinamicamente la cartella.
- **URL MapProxy nelle response**: calcolati da `MAPPROXY_PUBLIC_URL` env var.
- **No lock su write concorrenti**: last-write-wins, come nel plugin originale.
- **Fuori scope**: integrazione `.qgs`, multi-utente/ruoli, endpoint tile preview, metriche, rate limit.
