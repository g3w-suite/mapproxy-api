import glob
import json
import shutil
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.services import grids, storage

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(disabled_extensions=("yaml",), default=False),
    keep_trailing_newline=True,
)


def render_yaml(data: dict[str, Any]) -> str:
    """Build the Jinja2 context from a layer payload and render the template."""
    srs = data["srs"]
    epsg = grids.epsg_number(srs)
    service_type = grids.service_by_epsg(epsg)
    context = {
        "layer_name": data["layer_name"],
        "title": data["title"].replace("'", r"\'"),
        "abstract": (data.get("abstract") or "").replace("'", r"\'"),
        "ows_url": data["wms_url"],
        "wms_layers": data["wms_layers"],
        "wms_version": data.get("wms_version") or "1.3.0",
        "supported_srs": grids.supported_srs(srs, data.get("additional_srs")),
        "srs": srs,
        "bbox_4326": ",".join(str(v) for v in data["bbox_4326"]),
        "formats": data.get("formats") or ["png", "jpeg", "tiff"],
        "has_localgrid": grids.has_localgrid(srs),
        "tms": grids.has_localgrid(srs) and service_type == "tms",
    }
    template = _env.get_template("mapproxy_conf.yaml")
    return template.render(context)


def upsert(conf_dir: Path, data: dict[str, Any]) -> Path:
    name = data["layer_name"]
    yaml_content = render_yaml(data)
    yaml_p = storage.conf_path(conf_dir, name)
    meta_p = storage.meta_path(conf_dir, name)
    storage.atomic_write(yaml_p, yaml_content)
    storage.atomic_write(meta_p, json.dumps(data, indent=2, sort_keys=True))
    return yaml_p


def delete(conf_dir: Path, cache_dir: Path, layer_name: str) -> bool:
    """Remove YAML + meta + baselayer sidecar + all matching cache dirs."""
    removed = False
    for p in (
        storage.conf_path(conf_dir, layer_name),
        storage.meta_path(conf_dir, layer_name),
        storage.baselayer_path(conf_dir, layer_name),
    ):
        if p.is_file():
            p.unlink()
            removed = True
    for folder in glob.glob(storage.cache_dir_glob(cache_dir, layer_name)):
        if Path(folder).is_dir():
            shutil.rmtree(folder)
            removed = True
    return removed


def invalidate(conf_dir: Path, cache_dir: Path, layer_name: str) -> Path:
    """Delete cache dirs and regenerate YAML from stored meta sidecar."""
    meta_p = storage.meta_path(conf_dir, layer_name)
    if not meta_p.is_file():
        raise FileNotFoundError(layer_name)
    data = json.loads(meta_p.read_text())
    for folder in glob.glob(storage.cache_dir_glob(cache_dir, layer_name)):
        if Path(folder).is_dir():
            shutil.rmtree(folder)
    return upsert(conf_dir, data)


def get_layer(conf_dir: Path, layer_name: str) -> dict[str, Any] | None:
    meta_p = storage.meta_path(conf_dir, layer_name)
    if not meta_p.is_file():
        return None
    return json.loads(meta_p.read_text())


def list_layers(conf_dir: Path) -> list[dict[str, Any]]:
    if not conf_dir.is_dir():
        return []
    out = []
    for meta in sorted(conf_dir.glob("mapproxy_conf_*.meta.json")):
        try:
            out.append(json.loads(meta.read_text()))
        except (OSError, ValueError):
            continue
    return out


def exists(conf_dir: Path, layer_name: str) -> bool:
    return storage.meta_path(conf_dir, layer_name).is_file()
