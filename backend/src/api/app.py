from __future__ import annotations

"""FastAPI application entrypoint."""

from fastapi import FastAPI

from src.api.routers.frontend_mock import router as frontend_mock_router
from src.api.routers.health import router as health_router
from src.api.routers.pipelines import router as pipelines_router
from src.api.service import PipelineService
from src.api.routers.settings import router as settings_router
from src.api.settings_service import SettingsService


def create_app(engine=None, service: PipelineService | None = None) -> FastAPI:
    app = FastAPI(
        title="FlowState API",
        version="0.1.0",
        description="A minimal, standalone RESTful API scaffold for backend development.",
    )

    app.state.pipeline_service = service or PipelineService(engine=engine)
    app.state.settings_service = SettingsService()

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        return {
            "name": "FlowState API",
            "status": "running",
        }

    app.include_router(health_router)
    app.include_router(frontend_mock_router)
    app.include_router(pipelines_router)
    app.include_router(settings_router)
    return app


app = create_app()
