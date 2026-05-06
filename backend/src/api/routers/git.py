from __future__ import annotations

"""Git 状态查询与清理接口。"""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.api.deps import get_pipeline_service
from src.api.service import PipelineService
from src.models.pipeline import StageType
from src.services.git_service import GitError


router = APIRouter(prefix="/api/v1/pipelines", tags=["git"])


async def _load_pipeline_or_404(pipeline_id: str, service: PipelineService):
    pipeline = await service.get_pipeline(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return pipeline


@router.get("/{pipeline_id}/git/status")
async def get_git_status(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
):
    pipeline = await _load_pipeline_or_404(pipeline_id, service)
    return pipeline.context.git.model_dump()


@router.get("/{pipeline_id}/git/diff")
async def get_git_diff(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> Response:
    pipeline = await _load_pipeline_or_404(pipeline_id, service)
    try:
        diff_text = service.git_diff_for_pipeline(pipeline)
    except GitError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return Response(content=diff_text, media_type="text/plain; charset=utf-8")


@router.get("/{pipeline_id}/git/diff/{stage}")
async def get_git_diff_for_stage(
    pipeline_id: str,
    stage: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> Response:
    pipeline = await _load_pipeline_or_404(pipeline_id, service)
    try:
        stage_type = StageType(stage)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown stage: {stage}") from error

    try:
        diff_text = service.git_diff_for_pipeline(pipeline, stage_type=stage_type)
    except GitError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return Response(content=diff_text, media_type="text/plain; charset=utf-8")


@router.get("/{pipeline_id}/git/log")
async def get_git_log(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
):
    pipeline = await _load_pipeline_or_404(pipeline_id, service)
    return [item.model_dump() for item in pipeline.context.git.stage_commits]


@router.get("/{pipeline_id}/git/pr-command")
async def get_pr_command(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
):
    pipeline = await _load_pipeline_or_404(pipeline_id, service)
    return {"pr_command": pipeline.context.git.pr_command}


@router.delete("/{pipeline_id}/git")
async def cleanup_pipeline_git(
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service),
):
    try:
        pipeline = await service.cleanup_pipeline_git(pipeline_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return pipeline.context.git.model_dump()

