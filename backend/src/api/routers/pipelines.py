"""Minimal RESTful pipeline endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status

from src.api.deps import get_pipeline_service
from src.api.schemas import (
    CreatePipelineRequest,
    PipelineEnvelope,
    PipelineListResponse,
    RunPipelineResponse,
)
from src.api.service import PipelineService
from src.models.pipeline import Pipeline

router = APIRouter(prefix="/api/v1/pipelines", tags=["pipelines"])


async def _get_pipeline_or_404(
    pipeline_id: str,
    service: PipelineService,
) -> Pipeline:
    pipeline = await service.get_pipeline(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return pipeline


@router.post("", response_model=PipelineEnvelope, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    payload: CreatePipelineRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineEnvelope:
    pipeline = await service.create_pipeline(
        title=payload.title,
        requirement=payload.requirement,
    )
    return PipelineEnvelope(pipeline=pipeline)


@router.get("", response_model=PipelineListResponse)
async def list_pipelines(
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineListResponse:
    items = await service.list_pipelines()
    return PipelineListResponse(items=items)


@router.get("/{pipeline_id}", response_model=Pipeline)
async def get_pipeline(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> Pipeline:
    return await _get_pipeline_or_404(pipeline_id, service)


@router.post("/{pipeline_id}/run", response_model=RunPipelineResponse)
async def run_pipeline(
    pipeline_id: str,
    background_tasks: BackgroundTasks,
    service: PipelineService = Depends(get_pipeline_service),
) -> RunPipelineResponse:
    await _get_pipeline_or_404(pipeline_id, service)
    background_tasks.add_task(service.run_pipeline_by_id, pipeline_id)
    return RunPipelineResponse(status="scheduled", pipeline_id=pipeline_id)


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> Response:
    deleted = await service.delete_pipeline(pipeline_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
