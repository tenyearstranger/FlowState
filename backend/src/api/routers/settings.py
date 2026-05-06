from __future__ import annotations

"""Settings endpoints used by the frontend settings page."""

from fastapi import APIRouter, Depends

from src.api.deps import get_settings_service
from src.api.schemas import FrontendSettingsResponse, FrontendSettingsUpdateRequest
from src.api.settings_service import SettingsService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=FrontendSettingsResponse)
async def get_settings(
    service: SettingsService = Depends(get_settings_service),
) -> FrontendSettingsResponse:
    return FrontendSettingsResponse.model_validate(await service.get_settings())


@router.put("", response_model=FrontendSettingsResponse)
async def update_settings(
    payload: FrontendSettingsUpdateRequest,
    service: SettingsService = Depends(get_settings_service),
) -> FrontendSettingsResponse:
    return FrontendSettingsResponse.model_validate(
        await service.save_settings(payload.model_dump())
    )
