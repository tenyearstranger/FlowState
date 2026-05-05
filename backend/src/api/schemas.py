from __future__ import annotations

"""Request and response schemas for the API layer."""

from pydantic import BaseModel, Field

from src.models.pipeline import Pipeline


class HealthResponse(BaseModel):
    status: str = "ok"


class CreatePipelineRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    requirement: str = Field(min_length=1)


class PipelineEnvelope(BaseModel):
    pipeline: Pipeline


class PipelineListResponse(BaseModel):
    items: list[Pipeline]


class RunPipelineResponse(BaseModel):
    status: str
    pipeline_id: str


class FrontendPipelineStage(BaseModel):
    id: str
    name: str
    nameEn: str
    agent: str
    status: str
    duration: int | None = None
    tokens: int | None = None
    output: str | None = None
    isCheckpoint: bool | None = None
    startedAt: str | None = None
    completedAt: str | None = None


class FrontendPipeline(BaseModel):
    id: str
    name: str
    description: str
    status: str
    progress: int
    currentStage: int
    stages: list[FrontendPipelineStage]
    createdAt: str
    updatedAt: str
    template: str | None = None


class FrontendAgent(BaseModel):
    id: str
    name: str
    role: str
    description: str
    model: str
    provider: str
    status: str
    tasksCompleted: int
    avgDuration: int
    avgTokens: int
    color: str


class FrontendCheckpoint(BaseModel):
    id: str
    pipelineId: str
    pipelineName: str
    stage: str
    stageIndex: int
    status: str
    createdAt: str
    output: str
    rejectReason: str | None = None


class FrontendAnalyticsSummary(BaseModel):
    totalRuns: int
    totalSuccess: int
    totalTokens: int
    averageDurationMinutes: float
    mergedChanges: int


class FrontendPipelineRunDatum(BaseModel):
    day: str
    success: int
    failed: int
    total: int


class FrontendTokenUsageDatum(BaseModel):
    time: str
    tokens: int


class FrontendStageDurationDatum(BaseModel):
    stage: str
    avg: int
    p95: int


class FrontendAgentSuccessDatum(BaseModel):
    name: str
    rate: float


class FrontendAnalyticsOverview(BaseModel):
    summary: FrontendAnalyticsSummary
    pipelineRuns: list[FrontendPipelineRunDatum]
    tokenUsage: list[FrontendTokenUsageDatum]
    stageDurations: list[FrontendStageDurationDatum]
    agentSuccessRates: list[FrontendAgentSuccessDatum]


class FrontendActivityItem(BaseModel):
    time: str
    text: str
    type: str
