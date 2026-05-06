from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.deps import get_pipeline_service
from src.api.schemas import FrontendAnalyticsOverview
from src.api.service import PipelineService
from src.api.routers.ui_shared import build_dynamic_analytics

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics", response_model=FrontendAnalyticsOverview)
async def get_analytics(
    service: PipelineService = Depends(get_pipeline_service),
) -> FrontendAnalyticsOverview:
    return build_dynamic_analytics(await service.list_pipelines())
