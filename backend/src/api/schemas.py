from __future__ import annotations

"""Request and response schemas for the API layer."""

from pydantic import BaseModel, Field

from src.models.pipeline import Pipeline


class HealthResponse(BaseModel):
    status: str = "ok"


class CreatePipelineRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    project_path: str = Field(default="", max_length=1000)
    requirement: str = Field(min_length=1)


class PipelineEnvelope(BaseModel):
    pipeline: Pipeline


class PipelineListResponse(BaseModel):
    items: list[Pipeline]


class RunPipelineResponse(BaseModel):
    status: str
    pipeline_id: str


class PipelineActionResponse(BaseModel):
    pipeline: Pipeline


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
    subPhase: str | None = None
    depsManifest: dict | None = None


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
    projectPath: str | None = None
    projectSummary: str | None = None
    requirementDocPath: str | None = None
    solutionDocPath: str | None = None


class FrontendCreatePipelineRequest(BaseModel):
    projectPath: str = Field(min_length=1)
    requirement: str = Field(min_length=1)


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
    subPhase: str | None = None          # e.g. "deps_confirm" for testing stage phase 1
    depsManifest: dict | None = None     # pip/npm packages to install
    reviewScore: int | None = None       # stage5: 0-100 review score
    reviewIssues: list | None = None     # stage5: [{severity, file, line, message}]
    passRate: str | None = None          # stage4 phase2: "8/8"


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


class FrontendSettingsLLM(BaseModel):
    provider: str
    model: str
    baseUrl: str
    apiKey: str


class FrontendSettingsPipeline(BaseModel):
    defaultProvider: str
    maxAgentRetries: int
    checkpointTimeoutMinutes: int
    autoCreateBranch: bool
    autoCommitCode: bool
    autoCreateMR: bool
    branchNamePattern: str
    repositoryPath: str
    semanticIndex: bool


class FrontendSettingsGeneral(BaseModel):
    checkpointNotifications: bool
    pipelineCompleteNotifications: bool
    agentFailureAlerts: bool
    logRetentionDays: str
    anonymousUsageStats: bool
    appVersion: str
    engineVersion: str
    apiVersion: str


class FrontendSettingsResponse(BaseModel):
    llm: FrontendSettingsLLM
    agentConfigs: dict[str, FrontendSettingsLLM]
    pipeline: FrontendSettingsPipeline
    general: FrontendSettingsGeneral


class FrontendSettingsLLMUpdate(BaseModel):
    provider: str
    model: str
    baseUrl: str
    apiKey: str


class FrontendSettingsPipelineUpdate(BaseModel):
    defaultProvider: str
    maxAgentRetries: int
    checkpointTimeoutMinutes: int
    autoCreateBranch: bool
    autoCommitCode: bool
    autoCreateMR: bool
    branchNamePattern: str
    repositoryPath: str
    semanticIndex: bool


class FrontendSettingsGeneralUpdate(BaseModel):
    checkpointNotifications: bool
    pipelineCompleteNotifications: bool
    agentFailureAlerts: bool
    logRetentionDays: str
    anonymousUsageStats: bool


class FrontendSettingsUpdateRequest(BaseModel):
    llm: FrontendSettingsLLMUpdate
    agentConfigs: dict[str, FrontendSettingsLLMUpdate] = Field(default_factory=dict)
    pipeline: FrontendSettingsPipelineUpdate
    general: FrontendSettingsGeneralUpdate


class FrontendSettingsValidateRequest(BaseModel):
    agentId: str | None = None
    llm: FrontendSettingsLLMUpdate


class FrontendSettingsValidateResponse(BaseModel):
    ok: bool
    message: str
    provider: str
    model: str
