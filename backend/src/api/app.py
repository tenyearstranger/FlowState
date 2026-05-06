from __future__ import annotations

"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers.activities import router as activities_router
from src.api.routers.agents import router as agents_router
from src.api.routers.analytics import router as analytics_router
from src.api.routers.checkpoints import router as checkpoints_router
from src.api.routers.health import router as health_router
from src.api.routers.git import router as git_router
from src.api.routers.pipelines import router as pipelines_router
from src.api.routers.pipelines import ui_router as ui_pipelines_router
from src.api.service import PipelineService
from src.api.routers.settings import router as settings_router
from src.api.settings_service import SettingsService


def create_app(engine=None, service: PipelineService | None = None) -> FastAPI:
    app = FastAPI(
        title="FlowState API",
        version="0.1.0",
        description="A minimal, standalone RESTful API scaffold for backend development.",
    )

    # ===== 新增 CORS 中间件 =====
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],              # 允许所有来源（在生产环境中请根据需要调整）
        allow_credentials=False,
        allow_methods=["*"],              # 允许所有 HTTP 方法（包括 OPTIONS）
        allow_headers=["*"],              # 允许所有请求头
    )
    # ===== CORS 中间件结束 =====

    app.state.pipeline_service = service or PipelineService(engine=engine)
    app.state.settings_service = SettingsService()

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        return {
            "name": "FlowState API",
            "status": "running",
        }

    app.include_router(health_router)
    app.include_router(ui_pipelines_router)
    app.include_router(agents_router)
    app.include_router(checkpoints_router)
    app.include_router(analytics_router)
    app.include_router(activities_router)
    app.include_router(pipelines_router)
    app.include_router(git_router)
    app.include_router(settings_router)
    return app


app = create_app()
