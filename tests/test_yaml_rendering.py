from app.services.mapproxy_config import render_yaml


def _base_data():
    return {
        "layer_name": "roads",
        "title": "Roads",
        "abstract": "Road network",
        "wms_url": "https://example.org/wms",
        "wms_layers": "roads",
        "wms_version": "1.3.0",
        "srs": "EPSG:3857",
        "bbox_4326": [6.5, 44.0, 13.5, 47.5],
        "formats": ["png", "jpeg"],
        "additional_srs": [],
    }


def test_render_no_localgrid_for_web_mercator():
    yaml = render_yaml(_base_data())
    assert "localgrid_" not in yaml
    assert "GLOBAL_MERCATOR" in yaml
    assert "GLOBAL_WEBMERCATOR" in yaml
    assert "roads_cache" in yaml
    assert "roads_wms" in yaml
    assert "https://example.org/wms" in yaml


def test_render_localgrid_for_custom_srs():
    data = _base_data()
    data["srs"] = "EPSG:32632"
    yaml = render_yaml(data)
    assert "localgrid_tms" in yaml
    assert "localgrid_wmts" in yaml
    assert "'EPSG:32632'" in yaml
    assert "localgrid_wmts, GLOBAL_MERCATOR" in yaml


def test_render_localgrid_tms_when_epsg_4326():
    data = _base_data()
    data["srs"] = "EPSG:4326"
    yaml = render_yaml(data)
    assert "localgrid_" not in yaml
    assert "GLOBAL_GEODETIC" in yaml


def test_render_escapes_single_quote_in_title():
    data = _base_data()
    data["title"] = "Chi's Roads"
    yaml = render_yaml(data)
    assert "Chi\\'s Roads" in yaml


def test_render_supported_srs_contains_extras():
    data = _base_data()
    data["srs"] = "EPSG:32632"
    data["additional_srs"] = ["EPSG:25832"]
    yaml = render_yaml(data)
    assert "EPSG:32632" in yaml
    assert "EPSG:25832" in yaml
