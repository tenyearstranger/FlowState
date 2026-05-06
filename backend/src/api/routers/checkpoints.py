from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.api.deps import get_pipeline_service
from src.api.schemas import FrontendCheckpoint, FrontendActivityItem
from src.api.service import PipelineService
from src.api.routers.ui_shared import (
    ACTIVITIES,
    find_persisted_checkpoint,
    list_persisted_checkpoints,
    to_frontend_checkpoint,
)

router = APIRouter(prefix="/api", tags=["checkpoints"])


class RejectCheckpointRequest(BaseModel):
    reason: str


@router.get("/checkpoints", response_model=list[FrontendCheckpoint])
async def list_checkpoints(
    status_value: str = Query(default="all", alias="status"),
    service: PipelineService = Depends(get_pipeline_service),
) -> list[FrontendCheckpoint]:
    persisted = await list_persisted_checkpoints(service)
    if status_value == "all":
        return persisted
    return [
        checkpoint for checkpoint in persisted
        if checkpoint.status == status_value
    ]


@router.post("/checkpoints/{checkpoint_id}/approve", response_model=FrontendCheckpoint)
async def approve_checkpoint(
    checkpoint_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> FrontendCheckpoint:
    persisted = await find_persisted_checkpoint(checkpoint_id, service)
    if persisted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkpoint not found")

    pipeline, stage_index, current_checkpoint = persisted
    stage_node = pipeline.stages[stage_index]
    if stage_node.status.value != "waiting_human":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Checkpoint already processed")

    updated_pipeline = await service.approve_stage(pipeline.id, stage_index)
    if stage_index + 1 < len(updated_pipeline.stages):
        asyncio.create_task(service.continue_after_approval(pipeline.id, stage_index))
    stage_type = updated_pipeline.stages[stage_index].stage_type
    updated_checkpoint = to_frontend_checkpoint(updated_pipeline, stage_type, stage_index)
    if updated_checkpoint is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Checkpoint update failed")

    ACTIVITIES.insert(
        0,
        FrontendActivityItem(
            time="刚刚",
            text=f"{updated_pipeline.id} · {updated_checkpoint.stage} 检查点审批已通过",
            type="success",
        ),
    )
    del ACTIVITIES[20:]
    return updated_checkpoint


@router.post("/checkpoints/{checkpoint_id}/reject", response_model=FrontendCheckpoint)
async def reject_checkpoint(
    checkpoint_id: str,
    payload: RejectCheckpointRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> FrontendCheckpoint:
    persisted = await find_persisted_checkpoint(checkpoint_id, service)
    if persisted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkpoint not found")

    pipeline, stage_index, current_checkpoint = persisted
    stage_node = pipeline.stages[stage_index]
    if stage_node.status.value != "waiting_human":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Checkpoint already processed")

    updated_pipeline = await service.reject_stage(pipeline.id, stage_index, payload.reason)
    stage_type = updated_pipeline.stages[stage_index].stage_type
    updated_checkpoint = to_frontend_checkpoint(updated_pipeline, stage_type, stage_index)
    if updated_checkpoint is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Checkpoint update failed")

    asyncio.create_task(service.retry_stage(pipeline.id, stage_index))

    ACTIVITIES.insert(
        0,
        FrontendActivityItem(
            time="刚刚",
            text=f"{updated_pipeline.id} · {updated_checkpoint.stage} 检查点已拒绝，Agent 正在重新处理",
            type="warning",
        ),
    )
    del ACTIVITIES[20:]
    return updated_checkpoint
