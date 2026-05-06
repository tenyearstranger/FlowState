from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import FrontendActivityItem
from src.api.routers.ui_shared import ACTIVITIES

router = APIRouter(prefix="/api", tags=["activities"])


@router.get("/activities/recent", response_model=list[FrontendActivityItem])
async def list_recent_activities() -> list[FrontendActivityItem]:
    return ACTIVITIES
