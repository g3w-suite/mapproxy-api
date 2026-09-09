import os
import tempfile
from pathlib import Path


def conf_path(conf_dir: Path, layer_name: str) -> Path:
    return conf_dir / f"mapproxy_conf_{layer_name}.yaml"


def meta_path(conf_dir: Path, layer_name: str) -> Path:
    return conf_dir / f"mapproxy_conf_{layer_name}.meta.json"


def baselayer_path(conf_dir: Path, layer_name: str) -> Path:
    return conf_dir / f"mapproxy_conf_{layer_name}.baselayer.json"


def cache_dir_glob(cache_dir: Path, layer_name: str) -> str:
    return str(cache_dir / f"{layer_name}_cache_*")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
