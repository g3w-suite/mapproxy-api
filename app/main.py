from fastapi import FastAPI

from app.routers import auth, base_layers, health, layers

app = FastAPI(
    title="mapproxy-api",
    description="REST API to manage MapProxy layer YAML configurations.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(layers.router)
app.include_router(base_layers.router)
