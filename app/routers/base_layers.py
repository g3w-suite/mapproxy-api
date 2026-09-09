import json

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth import get_current_user
from app.config import Settings, get_settings
from app.models.base_layer import BaseLayerCreate, BaseLayerRead
from app.services import grids, mapproxy_config, storage

router = APIRouter(prefix="/base-layers", tags=["base-layers"])


def _build(data: dict, layer: dict, settings: Settings) -> BaseLayerRead:
    epsg = grids.epsg_number(layer["srs"])
    service = grids.service_by_epsg(epsg)
    base = settings.mapproxy_public_url.rstrip("/")
    name = layer["layer_name"]
    if service == "tms":
        grid = grids.get_grid(str(epsg), service)
        url = f"{base}/mapproxy_conf_{name}/tms/{name}/{grid}/{{z}}/{{x}}/{{-y}}.png"
    else:
        url = f"{base}/mapproxy_conf_{name}/service/?"
    return BaseLayerRead(
        layer_name=name,
        title=data["title"],
        description=data.get("description", ""),
        attributions=data.get("attributions", ""),
        servertype=service.upper(),
        url=url,
        srs=layer["srs"],
    )


@router.post("", response_model=BaseLayerRead, status_code=status.HTTP_201_CREATED)
def create_base_layer(
    payload: BaseLayerCreate,
    settings: Settings = Depends(get_settings),
    _: str = Depends(get_current_user),
) -> BaseLayerRead:
    layer = mapproxy_config.get_layer(settings.mapproxy_conf_dir, payload.layer_name)
    if not layer:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="layer not found")
    data = payload.model_dump(mode="json")
    p = storage.baselayer_path(settings.mapproxy_conf_dir, payload.layer_name)
    storage.atomic_write(p, json.dumps(data, indent=2, sort_keys=True))
    return _build(data, layer, settings)


@router.get("/{layer_name}", response_model=BaseLayerRead)
def get_base_layer(
    layer_name: str,
    settings: Settings = Depends(get_settings),
    _: str = Depends(get_current_user),
) -> BaseLayerRead:
    p = storage.baselayer_path(settings.mapproxy_conf_dir, layer_name)
    if not p.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    layer = mapproxy_config.get_layer(settings.mapproxy_conf_dir, layer_name)
    if not layer:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="layer not found")
    return _build(json.loads(p.read_text()), layer, settings)


@router.delete("/{layer_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_base_layer(
    layer_name: str,
    settings: Settings = Depends(get_settings),
    _: str = Depends(get_current_user),
) -> Response:
    p = storage.baselayer_path(settings.mapproxy_conf_dir, layer_name)
    if not p.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    p.unlink()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
