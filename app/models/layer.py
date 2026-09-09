import re

from pydantic import BaseModel, Field, HttpUrl, field_validator

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_SRS_RE = re.compile(r"^[A-Z]+:\d+$")


class LayerBase(BaseModel):
    title: str = Field(..., min_length=1)
    abstract: str = ""
    wms_url: HttpUrl
    wms_layers: str = Field(..., min_length=1)
    wms_version: str = "1.3.0"
    srs: str
    bbox_4326: list[float] = Field(..., min_length=4, max_length=4)
    formats: list[str] = Field(default_factory=lambda: ["png", "jpeg", "tiff"])
    additional_srs: list[str] = Field(default_factory=list)

    @field_validator("srs")
    @classmethod
    def _check_srs(cls, v: str) -> str:
        if not _SRS_RE.match(v):
            raise ValueError("srs must look like 'EPSG:<code>'")
        return v

    @field_validator("additional_srs")
    @classmethod
    def _check_additional_srs(cls, v: list[str]) -> list[str]:
        for s in v:
            if not _SRS_RE.match(s):
                raise ValueError(f"invalid srs: {s!r}")
        return v


class LayerCreate(LayerBase):
    layer_name: str

    @field_validator("layer_name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        if not _NAME_RE.match(v):
            raise ValueError("layer_name must match [a-z0-9][a-z0-9_-]*")
        return v


class LayerUpdate(LayerBase):
    pass


class LayerRead(LayerCreate):
    tms_url: str | None = None
    wmts_url: str | None = None
