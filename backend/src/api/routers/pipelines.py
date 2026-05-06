"""Minimal RESTful pipeline endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status

from src.api.deps import get_pipeline_service
from src.api.schemas import (
    CreatePipelineRequest,
    FrontendActivityItem,
    FrontendCreatePipelineRequest,
    FrontendPipeline,
    PipelineActionResponse,
    PipelineEnvelope,
    PipelineListResponse,
    RunPipelineResponse,
)
from src.api.service import PipelineService, PipelineValidationError
from src.models.pipeline import Pipeline, PipelineStatus
from src.api.routers.ui_shared import (
    ACTIVITIES,
    build_seed_pipelines,
    seed_activities,
    to_frontend_pipeline,
)

router = APIRouter(prefix="/api/v1/pipelines", tags=["pipelines"])
ui_router = APIRouter(prefix="/api", tags=["pipelines-ui"])


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
    try:
        pipeline = await service.create_pipeline(
            title=payload.title,
            project_path=payload.project_path,
            requirement=payload.requirement,
        )
    except PipelineValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
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


@router.post("/{pipeline_id}/pause", response_model=PipelineActionResponse)
async def pause_pipeline(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineActionResponse:
    try:
        pipeline = await service.pause_pipeline(pipeline_id)
    except PipelineValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return PipelineActionResponse(pipeline=pipeline)


@router.post("/{pipeline_id}/resume", response_model=PipelineActionResponse)
async def resume_pipeline(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineActionResponse:
    try:
        pipeline = await service.resume_pipeline(pipeline_id)
    except PipelineValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return PipelineActionResponse(pipeline=pipeline)


@router.post("/{pipeline_id}/cancel", response_model=PipelineActionResponse)
async def cancel_pipeline(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineActionResponse:
    try:
        pipeline = await service.cancel_pipeline(pipeline_id)
    except PipelineValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return PipelineActionResponse(pipeline=pipeline)


@router.post("/{pipeline_id}/retry", response_model=PipelineActionResponse)
async def retry_pipeline(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineActionResponse:
    try:
        pipeline = await service.retry_pipeline(pipeline_id)
    except PipelineValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return PipelineActionResponse(pipeline=pipeline)


@ui_router.post("/dev/seed", response_model=list[FrontendPipeline], status_code=status.HTTP_201_CREATED)
async def seed_demo_data(
    reset: bool = Query(default=False),
    service: PipelineService = Depends(get_pipeline_service),
) -> list[FrontendPipeline]:
    if reset:
        for pipeline in await service.list_pipelines():
            await service.state_store.delete(pipeline.id)
        ACTIVITIES.clear()

    seeded = []
    for pipeline in build_seed_pipelines():
        existing = await service.get_pipeline(pipeline.id)
        if existing is None:
            await service.state_store.save(pipeline)
            seeded.append(pipeline)
        else:
            seeded.append(existing)

    if not ACTIVITIES:
        seed_activities(seeded)

    return [to_frontend_pipeline(item) for item in await service.list_pipelines()]


@ui_router.get("/pipelines", response_model=list[FrontendPipeline])
async def list_pipelines_ui(
    service: PipelineService = Depends(get_pipeline_service),
) -> list[FrontendPipeline]:
    return [to_frontend_pipeline(item) for item in await service.list_pipelines()]


@ui_router.post("/pipelines", response_model=FrontendPipeline, status_code=status.HTTP_201_CREATED)
async def create_pipeline_ui(
    payload: FrontendCreatePipelineRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> FrontendPipeline:
    try:
        pipeline = await service.create_pipeline(
            title="",
            requirement=payload.requirement,
            project_path=payload.projectPath,
            start_immediately=True,
        )
    except PipelineValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    ACTIVITIES.insert(
        0,
        FrontendActivityItem(
            time="刚刚",
            text=(
                f"{pipeline.id} · 需求分析已完成，"
                f"{'等待人工审批' if pipeline.status == PipelineStatus.WAITING_HUMAN else '进入下一阶段'}"
            ),
            type="checkpoint" if pipeline.status == PipelineStatus.WAITING_HUMAN else "success",
        ),
    )
    del ACTIVITIES[20:]

    return to_frontend_pipeline(pipeline)


@ui_router.get("/pipelines/{pipeline_id}", response_model=FrontendPipeline)
async def get_pipeline_ui(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> FrontendPipeline:
    pipeline = await service.get_pipeline(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return to_frontend_pipeline(pipeline)


@ui_router.get("/pipelines/{pipeline_id}/logs", response_model=list[str])
async def get_pipeline_logs_ui(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> list[str]:
    pipeline = await service.get_pipeline(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return pipeline.logs


@ui_router.post("/pipelines/{pipeline_id}/pause", response_model=FrontendPipeline)
async def pause_pipeline_ui(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> FrontendPipeline:
    try:
        pipeline = await service.pause_pipeline(pipeline_id)
    except PipelineValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return to_frontend_pipeline(pipeline)


@ui_router.post("/pipelines/{pipeline_id}/resume", response_model=FrontendPipeline)
async def resume_pipeline_ui(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> FrontendPipeline:
    try:
        pipeline = await service.resume_pipeline(pipeline_id)
    except PipelineValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return to_frontend_pipeline(pipeline)


@ui_router.post("/pipelines/{pipeline_id}/cancel", response_model=FrontendPipeline)
async def cancel_pipeline_ui(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> FrontendPipeline:
    try:
        pipeline = await service.cancel_pipeline(pipeline_id)
    except PipelineValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return to_frontend_pipeline(pipeline)


@ui_router.post("/pipelines/{pipeline_id}/retry", response_model=FrontendPipeline)
async def retry_pipeline_ui(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> FrontendPipeline:
    try:
        pipeline = await service.retry_pipeline(pipeline_id)
    except PipelineValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return to_frontend_pipeline(pipeline)
