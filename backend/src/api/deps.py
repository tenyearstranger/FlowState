"""Shared FastAPI dependencies."""

from fastapi import Request

from src.api.service import PipelineService


def get_pipeline_service(request: Request) -> PipelineService:
    return request.app.state.pipeline_service
