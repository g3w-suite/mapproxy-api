from pydantic import BaseModel, Field


class BaseLayerBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = ""
    attributions: str = ""


class BaseLayerCreate(BaseLayerBase):
    layer_name: str


class BaseLayerRead(BaseLayerBase):
    layer_name: str
    servertype: str
    url: str
    srs: str
