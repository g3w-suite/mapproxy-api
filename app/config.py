from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mapproxy_conf_dir: Path = Path("/data/mapproxy/conf")
    mapproxy_cache_dir: Path = Path("/data/mapproxy/conf/cache_data")
    mapproxy_public_url: str = "http://localhost:8080"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    admin_username: str = "admin"
    admin_password_hash: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
