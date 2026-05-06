"""Shared FastAPI dependencies."""

from fastapi import Request

from src.api.service import PipelineService
from src.api.settings_service import SettingsService


def get_pipeline_service(request: Request) -> PipelineService:
    return request.app.state.pipeline_service


def get_settings_service(request: Request) -> SettingsService:
    return request.app.state.settings_service
