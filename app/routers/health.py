import os

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    conf_dir = settings.mapproxy_conf_dir
    exists = conf_dir.is_dir()
    writable = exists and os.access(conf_dir, os.W_OK)
    return {
        "status": "ok",
        "mapproxy_conf_dir": str(conf_dir),
        "exists": exists,
        "writable": writable,
    }
