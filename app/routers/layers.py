from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth import get_current_user
from app.config import Settings, get_settings
from app.models.layer import LayerCreate, LayerRead, LayerUpdate
from app.services import grids, mapproxy_config, storage

router = APIRouter(prefix="/layers", tags=["layers"])


def _to_read(data: dict, settings: Settings) -> LayerRead:
    base = settings.mapproxy_public_url.rstrip("/")
    name = data["layer_name"]
    epsg = grids.epsg_number(data["srs"])
    service = grids.service_by_epsg(epsg)
    grid = grids.get_grid(str(epsg), service)
    tms_url = f"{base}/mapproxy_conf_{name}/tms/{name}/{grid}/{{z}}/{{x}}/{{-y}}.png"
    wmts_url = f"{base}/mapproxy_conf_{name}/service/?"
    return LayerRead(**data, tms_url=tms_url, wmts_url=wmts_url)


@router.get("", response_model=list[LayerRead])
def list_layers(
    settings: Settings = Depends(get_settings),
    _: str = Depends(get_current_user),
) -> list[LayerRead]:
    return [_to_read(d, settings) for d in mapproxy_config.list_layers(settings.mapproxy_conf_dir)]


@router.post("", response_model=LayerRead, status_code=status.HTTP_201_CREATED)
def create_layer(
    payload: LayerCreate,
    settings: Settings = Depends(get_settings),
    _: str = Depends(get_current_user),
) -> LayerRead:
    if mapproxy_config.exists(settings.mapproxy_conf_dir, payload.layer_name):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="layer already exists")
    data = payload.model_dump(mode="json")
    mapproxy_config.upsert(settings.mapproxy_conf_dir, data)
    return _to_read(data, settings)


@router.get("/{layer_name}", response_model=LayerRead)
def get_layer(
    layer_name: str,
    settings: Settings = Depends(get_settings),
    _: str = Depends(get_current_user),
) -> LayerRead:
    data = mapproxy_config.get_layer(settings.mapproxy_conf_dir, layer_name)
    if not data:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return _to_read(data, settings)


@router.put("/{layer_name}", response_model=LayerRead)
def update_layer(
    layer_name: str,
    payload: LayerUpdate,
    settings: Settings = Depends(get_settings),
    _: str = Depends(get_current_user),
) -> LayerRead:
    if not mapproxy_config.exists(settings.mapproxy_conf_dir, layer_name):
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    data = {"layer_name": layer_name, **payload.model_dump(mode="json")}
    mapproxy_config.upsert(settings.mapproxy_conf_dir, data)
    return _to_read(data, settings)


@router.delete("/{layer_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_layer(
    layer_name: str,
    settings: Settings = Depends(get_settings),
    _: str = Depends(get_current_user),
) -> Response:
    if not mapproxy_config.exists(settings.mapproxy_conf_dir, layer_name):
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    mapproxy_config.delete(
        settings.mapproxy_conf_dir, settings.mapproxy_cache_dir, layer_name
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{layer_name}/reset-cache")
def reset_cache(
    layer_name: str,
    settings: Settings = Depends(get_settings),
    _: str = Depends(get_current_user),
) -> dict:
    try:
        mapproxy_config.invalidate(
            settings.mapproxy_conf_dir, settings.mapproxy_cache_dir, layer_name
        )
    except FileNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return {"status": "ok", "message": "Cache erased"}


@router.get("/{layer_name}/yaml")
def get_layer_yaml(
    layer_name: str,
    settings: Settings = Depends(get_settings),
    _: str = Depends(get_current_user),
) -> Response:
    yaml_p = storage.conf_path(settings.mapproxy_conf_dir, layer_name)
    if not yaml_p.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return Response(content=yaml_p.read_text(), media_type="text/yaml")
