"""Port of qmapproxy/utils/general.py, stripped of QGIS/mapproxy runtime deps."""

_STANDARD_GRIDS = {
    "4326": "GLOBAL_GEODETIC",
    "900913": "GLOBAL_MERCATOR",
    "3857": "GLOBAL_WEBMERCATOR",
}


def get_grid(epsg: str = "3857", service_type: str = "tms") -> str:
    return _STANDARD_GRIDS.get(epsg, f"localgrid_{service_type}")


def service_by_epsg(epsg: int) -> str:
    return "tms" if epsg == 4326 else "wmts"


def epsg_number(srs: str) -> int:
    """Parse '<AUTH>:<code>' -> int(code)."""
    return int(srs.split(":", 1)[1])


def supported_srs(srs: str, extra: list[str] | None = None) -> list[str]:
    base = ["CRS:84", "EPSG:4326", "EPSG:3857"]
    if srs and srs not in base:
        base.append(srs)
    if extra:
        for s in extra:
            if s not in base:
                base.append(s)
    return base


def has_localgrid(srs: str) -> bool:
    return srs not in ("EPSG:900913", "EPSG:4326", "EPSG:3857")
