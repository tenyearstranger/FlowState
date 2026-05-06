from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.deps import get_pipeline_service
from src.api.schemas import FrontendAgent
from src.api.service import PipelineService
from src.api.routers.ui_shared import build_dynamic_agents

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/agents", response_model=list[FrontendAgent])
async def list_agents(
    service: PipelineService = Depends(get_pipeline_service),
) -> list[FrontendAgent]:
    return build_dynamic_agents(await service.list_pipelines())
