"""Small service layer that keeps the API decoupled from runtime details."""

from __future__ import annotations

from datetime import datetime

from src.models.pipeline import (
    Pipeline,
    PipelineContext,
    PipelineStatus,
    StageNode,
    StageType,
)
from src.store.state_store import StateStore


def _build_default_stages() -> list[StageNode]:
    return [
        StageNode(stage_type=StageType.REQUIREMENT),
        StageNode(stage_type=StageType.SOLUTION),
        StageNode(stage_type=StageType.CODING),
        StageNode(stage_type=StageType.TESTING),
        StageNode(stage_type=StageType.REVIEW),
        StageNode(stage_type=StageType.DELIVERY),
    ]


class PipelineService:
    """A tiny adapter around either an injected engine or local persistence."""

    def __init__(self, engine=None, state_store: StateStore | None = None):
        self.engine = engine
        self.state_store = state_store or getattr(engine, "state_store", None) or StateStore()

    async def create_pipeline(self, *, title: str, requirement: str) -> Pipeline:
        if self.engine is not None:
            return await self.engine.create_pipeline(requirement=requirement, title=title)

        pipeline = Pipeline(
            title=title or requirement[:60],
            status=PipelineStatus.PENDING,
            context=PipelineContext(requirement_raw=requirement),
            stages=_build_default_stages(),
        )
        await self.state_store.save(pipeline)
        return pipeline

    async def get_pipeline(self, pipeline_id: str) -> Pipeline | None:
        return await self.state_store.load(pipeline_id)

    async def list_pipelines(self) -> list[Pipeline]:
        return await self.state_store.list_pipelines()

    async def delete_pipeline(self, pipeline_id: str) -> bool:
        pipeline = await self.state_store.load(pipeline_id)
        if pipeline is None:
            return False
        await self.state_store.delete(pipeline_id)
        return True

    async def run_pipeline_by_id(self, pipeline_id: str) -> Pipeline:
        pipeline = await self.state_store.load(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        return await self.run_pipeline(pipeline)

    async def run_pipeline(self, pipeline: Pipeline) -> Pipeline:
        if self.engine is not None:
            await self.engine.run_pipeline(pipeline)
            return pipeline

        pipeline.status = PipelineStatus.RUNNING
        pipeline.updated_at = datetime.now()
        await self.state_store.save(pipeline)
        return pipeline
