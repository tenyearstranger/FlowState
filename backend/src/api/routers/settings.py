from __future__ import annotations

"""Settings endpoints used by the frontend settings page."""

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_settings_service
from src.api.schemas import (
    FrontendSettingsResponse,
    FrontendSettingsUpdateRequest,
    FrontendSettingsValidateRequest,
    FrontendSettingsValidateResponse,
)
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


@router.post("/validate-llm", response_model=FrontendSettingsValidateResponse)
async def validate_llm_settings(
    payload: FrontendSettingsValidateRequest,
    service: SettingsService = Depends(get_settings_service),
) -> FrontendSettingsValidateResponse:
    try:
        result = await service.validate_llm_settings(payload.agentId, payload.llm.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FrontendSettingsValidateResponse.model_validate(result)
