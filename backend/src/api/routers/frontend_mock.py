"""Static mock endpoints used by the current frontend screens."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from src.api.schemas import (
    FrontendActivityItem,
    FrontendAgent,
    FrontendAnalyticsOverview,
    FrontendCheckpoint,
    FrontendPipeline,
    FrontendPipelineStage,
)

router = APIRouter(prefix="/api", tags=["frontend-mock"])


def _stage(
    stage_id: str,
    name: str,
    name_en: str,
    agent: str,
    status_value: str,
    *,
    duration: int | None = None,
    tokens: int | None = None,
    output: str | None = None,
    is_checkpoint: bool | None = None,
) -> FrontendPipelineStage:
    return FrontendPipelineStage(
        id=stage_id,
        name=name,
        nameEn=name_en,
        agent=agent,
        status=status_value,
        duration=duration,
        tokens=tokens,
        output=output,
        isCheckpoint=is_checkpoint,
    )


PIPELINES: list[FrontendPipeline] = [
    FrontendPipeline(
        id="pl-001",
        name="用户认证系统 · JWT Token 刷新",
        description="实现 Access Token / Refresh Token 双 Token 机制，支持无感刷新",
        status="running",
        progress=28,
        currentStage=1,
        template="新功能开发",
        createdAt="2026-05-04T08:30:00Z",
        updatedAt="2026-05-04T09:12:00Z",
        stages=[
            _stage(
                "pl-001-stage-1",
                "需求分析",
                "Requirements Analysis",
                "RequirementsAgent",
                "completed",
                duration=42,
                tokens=3240,
                output=(
                    "## 结构化需求文档\n\n"
                    "### 功能目标\n"
                    "实现一个用户认证系统，支持 JWT Token 刷新机制。\n\n"
                    "### 核心需求\n"
                    "1. 用户注册：邮箱 + 密码，自动发送验证邮件\n"
                    "2. 用户登录：支持邮箱/用户名登录，返回双 Token\n"
                    "3. Token 刷新：Access Token 过期后自动刷新\n"
                    "4. 用户登出：吊销 Refresh Token，清除会话"
                ),
            ),
            _stage(
                "pl-001-stage-2",
                "方案设计",
                "Design",
                "ArchitectAgent",
                "awaiting_review",
                duration=87,
                tokens=5680,
                is_checkpoint=True,
                output=(
                    "## 技术方案设计\n\n"
                    "### 架构决策\n"
                    "采用无状态 JWT 方案，Refresh Token 存储于 Redis，支持主动吊销。\n\n"
                    "### API 设计\n"
                    "POST /auth/register\n"
                    "POST /auth/login\n"
                    "POST /auth/refresh\n"
                    "POST /auth/logout\n"
                    "GET /auth/me"
                ),
            ),
            _stage("pl-001-stage-3", "代码生成", "Code Generation", "CodegenAgent", "idle"),
            _stage("pl-001-stage-4", "测试生成", "Test Generation", "TestAgent", "idle"),
            _stage(
                "pl-001-stage-5",
                "代码评审",
                "Code Review",
                "ReviewAgent",
                "idle",
                is_checkpoint=True,
            ),
            _stage("pl-001-stage-6", "交付集成", "Delivery", "DeliveryAgent", "idle"),
        ],
    ),
    FrontendPipeline(
        id="pl-002",
        name="API 限流中间件重构",
        description="将现有的 IP 限流升级为基于用户/租户的分级限流策略",
        status="paused",
        progress=33,
        currentStage=1,
        template="重构优化",
        createdAt="2026-05-03T14:20:00Z",
        updatedAt="2026-05-03T16:45:00Z",
        stages=[
            _stage("pl-002-stage-1", "需求分析", "Requirements Analysis", "RequirementsAgent", "completed", duration=38, tokens=3010),
            _stage(
                "pl-002-stage-2",
                "方案设计",
                "Design",
                "ArchitectAgent",
                "awaiting_review",
                duration=79,
                tokens=5210,
                is_checkpoint=True,
                output=(
                    "## API 限流重构方案\n\n"
                    "采用令牌桶算法，基于 Redis 实现用户级和租户级双层限流。"
                ),
            ),
            _stage("pl-002-stage-3", "代码生成", "Code Generation", "CodegenAgent", "idle"),
            _stage("pl-002-stage-4", "测试生成", "Test Generation", "TestAgent", "idle"),
            _stage("pl-002-stage-5", "代码评审", "Code Review", "ReviewAgent", "idle", is_checkpoint=True),
            _stage("pl-002-stage-6", "交付集成", "Delivery", "DeliveryAgent", "idle"),
        ],
    ),
    FrontendPipeline(
        id="pl-003",
        name="数据库连接池优化",
        description="修复高并发场景下连接池泄漏问题，优化超时配置",
        status="completed",
        progress=100,
        currentStage=5,
        template="Bug 修复",
        createdAt="2026-05-02T10:00:00Z",
        updatedAt="2026-05-02T14:30:00Z",
        stages=[
            _stage("pl-003-stage-1", "需求分析", "Requirements Analysis", "RequirementsAgent", "completed", duration=22, tokens=1820),
            _stage("pl-003-stage-2", "方案设计", "Design", "ArchitectAgent", "completed", duration=45, tokens=2940, is_checkpoint=True),
            _stage("pl-003-stage-3", "代码生成", "Code Generation", "CodegenAgent", "completed", duration=110, tokens=9100),
            _stage("pl-003-stage-4", "测试生成", "Test Generation", "TestAgent", "completed", duration=54, tokens=3600),
            _stage("pl-003-stage-5", "代码评审", "Code Review", "ReviewAgent", "completed", duration=48, tokens=2980, is_checkpoint=True),
            _stage("pl-003-stage-6", "交付集成", "Delivery", "DeliveryAgent", "completed", duration=20, tokens=1200),
        ],
    ),
    FrontendPipeline(
        id="pl-004",
        name="消息推送服务接入 WebSocket",
        description="为实时通知功能添加 WebSocket 支持，替换现有轮询方案",
        status="pending",
        progress=0,
        currentStage=0,
        template="新功能开发",
        createdAt="2026-05-04T10:00:00Z",
        updatedAt="2026-05-04T10:00:00Z",
        stages=[
            _stage("pl-004-stage-1", "需求分析", "Requirements Analysis", "RequirementsAgent", "idle"),
            _stage("pl-004-stage-2", "方案设计", "Design", "ArchitectAgent", "idle", is_checkpoint=True),
            _stage("pl-004-stage-3", "代码生成", "Code Generation", "CodegenAgent", "idle"),
            _stage("pl-004-stage-4", "测试生成", "Test Generation", "TestAgent", "idle"),
            _stage("pl-004-stage-5", "代码评审", "Code Review", "ReviewAgent", "idle", is_checkpoint=True),
            _stage("pl-004-stage-6", "交付集成", "Delivery", "DeliveryAgent", "idle"),
        ],
    ),
    FrontendPipeline(
        id="pl-005",
        name="日志系统升级 · OpenTelemetry",
        description="统一接入 OpenTelemetry，支持分布式追踪和指标采集",
        status="failed",
        progress=67,
        currentStage=3,
        template="重构优化",
        createdAt="2026-05-01T09:00:00Z",
        updatedAt="2026-05-01T11:20:00Z",
        stages=[
            _stage("pl-005-stage-1", "需求分析", "Requirements Analysis", "RequirementsAgent", "completed", duration=30, tokens=2400),
            _stage("pl-005-stage-2", "方案设计", "Design", "ArchitectAgent", "completed", duration=61, tokens=4100, is_checkpoint=True),
            _stage("pl-005-stage-3", "代码生成", "Code Generation", "CodegenAgent", "completed", duration=133, tokens=11800),
            _stage("pl-005-stage-4", "测试生成", "Test Generation", "TestAgent", "failed", duration=76, tokens=4300),
            _stage("pl-005-stage-5", "代码评审", "Code Review", "ReviewAgent", "idle", is_checkpoint=True),
            _stage("pl-005-stage-6", "交付集成", "Delivery", "DeliveryAgent", "idle"),
        ],
    ),
]

PIPELINE_LOGS: dict[str, list[str]] = {
    "pl-001": [
        "[08:30:01] Pipeline pl-001 已启动",
        "[08:30:02] RequirementsAgent 初始化，模型: gpt-4o",
        "[08:30:35] 需求分析完成，输出 423 tokens",
        "[08:30:36] ArchitectAgent 初始化，模型: claude-3-7-sonnet",
        "[08:31:08] 技术方案已生成，触发检查点 [方案设计审批]",
        "[08:31:09] 等待人工审批...",
    ],
    "pl-002": [
        "[15:02:11] Pipeline pl-002 已启动",
        "[15:08:42] RequirementsAgent 需求梳理完成",
        "[15:10:03] ArchitectAgent 生成限流重构方案",
        "[15:10:04] 等待人工审批...",
    ],
    "pl-003": [
        "[10:00:01] Pipeline pl-003 已启动",
        "[13:58:44] DeliveryAgent 已创建 MR #42",
        "[14:30:00] 流水线执行完成",
    ],
    "pl-004": ["[10:00:00] Pipeline pl-004 已创建，等待调度执行"],
    "pl-005": [
        "[09:00:01] Pipeline pl-005 已启动",
        "[10:44:15] TestAgent 正在分析代码变更集...",
        "[10:51:32] ERROR 测试覆盖率不足 (62%)",
    ],
}

AGENTS: list[FrontendAgent] = [
    FrontendAgent(
        id="agent-1",
        name="RequirementsAgent",
        role="需求分析师",
        description="理解自然语言需求，澄清歧义，输出结构化需求文档与验收标准",
        model="gpt-4o",
        provider="OpenAI",
        status="idle",
        tasksCompleted=47,
        avgDuration=38,
        avgTokens=3200,
        color="#5B72FF",
    ),
    FrontendAgent(
        id="agent-2",
        name="ArchitectAgent",
        role="架构设计师",
        description="分析现有代码库，设计技术方案，确定文件变更清单与 API 接口",
        model="claude-3-7-sonnet",
        provider="Anthropic",
        status="running",
        tasksCompleted=41,
        avgDuration=92,
        avgTokens=5800,
        color="#A259FF",
    ),
    FrontendAgent(
        id="agent-3",
        name="CodegenAgent",
        role="代码生成器",
        description="按照技术方案逐文件生成或修改代码，输出完整的代码变更集",
        model="claude-3-7-sonnet",
        provider="Anthropic",
        status="idle",
        tasksCompleted=39,
        avgDuration=145,
        avgTokens=12600,
        color="#FF7A5C",
    ),
    FrontendAgent(
        id="agent-4",
        name="TestAgent",
        role="测试工程师",
        description="根据代码变更集自动生成单元测试和集成测试，输出测试报告",
        model="gpt-4o-mini",
        provider="OpenAI",
        status="running",
        tasksCompleted=35,
        avgDuration=67,
        avgTokens=4100,
        color="#34C759",
    ),
    FrontendAgent(
        id="agent-5",
        name="ReviewAgent",
        role="代码审查员",
        description="多维度审查代码变更，生成评审报告",
        model="gpt-4o",
        provider="OpenAI",
        status="idle",
        tasksCompleted=38,
        avgDuration=78,
        avgTokens=6200,
        color="#FF9F0A",
    ),
    FrontendAgent(
        id="agent-6",
        name="DeliveryAgent",
        role="交付集成",
        description="整合所有变更，自动创建 Git 分支、提交代码、发起 PR",
        model="gpt-4o-mini",
        provider="OpenAI",
        status="running",
        tasksCompleted=30,
        avgDuration=25,
        avgTokens=1800,
        color="#00C7BE",
    ),
]

CHECKPOINTS: list[FrontendCheckpoint] = [
    FrontendCheckpoint(
        id="cp-001",
        pipelineId="pl-001",
        pipelineName="用户认证系统 · JWT Token 刷新",
        stage="方案设计",
        stageIndex=1,
        status="pending",
        createdAt="2026-05-04T08:52:00Z",
        output=PIPELINES[0].stages[1].output or "",
    ),
    FrontendCheckpoint(
        id="cp-002",
        pipelineId="pl-002",
        pipelineName="API 限流中间件重构",
        stage="方案设计",
        stageIndex=1,
        status="pending",
        createdAt="2026-05-03T15:10:00Z",
        output="## API 限流重构方案\n\n采用令牌桶算法，基于 Redis 实现分级限流。",
    ),
]

ANALYTICS = FrontendAnalyticsOverview.model_validate(
    {
        "summary": {
            "totalRuns": 41,
            "totalSuccess": 36,
            "totalTokens": 56200,
            "averageDurationMinutes": 7.4,
            "mergedChanges": 18,
        },
        "pipelineRuns": [
            {"day": "4/28", "success": 3, "failed": 0, "total": 3},
            {"day": "4/29", "success": 5, "failed": 1, "total": 6},
            {"day": "4/30", "success": 4, "failed": 0, "total": 4},
            {"day": "5/1", "success": 6, "failed": 1, "total": 7},
            {"day": "5/2", "success": 8, "failed": 0, "total": 8},
            {"day": "5/3", "success": 7, "failed": 2, "total": 9},
            {"day": "5/4", "success": 3, "failed": 1, "total": 4},
        ],
        "tokenUsage": [
            {"time": "08:00", "tokens": 2400},
            {"time": "09:00", "tokens": 8600},
            {"time": "10:00", "tokens": 5200},
            {"time": "11:00", "tokens": 12400},
            {"time": "12:00", "tokens": 3800},
            {"time": "13:00", "tokens": 9200},
            {"time": "14:00", "tokens": 14600},
        ],
        "stageDurations": [
            {"stage": "需求分析", "avg": 38, "p95": 62},
            {"stage": "方案设计", "avg": 92, "p95": 145},
            {"stage": "代码生成", "avg": 145, "p95": 220},
            {"stage": "测试生成", "avg": 67, "p95": 98},
            {"stage": "代码评审", "avg": 78, "p95": 130},
            {"stage": "交付集成", "avg": 25, "p95": 38},
        ],
        "agentSuccessRates": [
            {"name": "RequirementsAgent", "rate": 98.2},
            {"name": "ArchitectAgent", "rate": 95.1},
            {"name": "CodegenAgent", "rate": 91.8},
            {"name": "TestAgent", "rate": 88.4},
            {"name": "ReviewAgent", "rate": 97.3},
            {"name": "DeliveryAgent", "rate": 99.1},
        ],
    }
)

ACTIVITIES: list[FrontendActivityItem] = [
    FrontendActivityItem(
        time="2分钟前",
        text="pl-001 · ArchitectAgent 产出方案设计，等待人工审批",
        type="checkpoint",
    ),
    FrontendActivityItem(
        time="15分钟前",
        text="pl-002 · 方案设计检查点等待审批（已超时 17m）",
        type="warning",
    ),
    FrontendActivityItem(
        time="1小时前",
        text="pl-005 · TestAgent 运行失败，原因：测试覆盖率不足 (62%)",
        type="error",
    ),
    FrontendActivityItem(
        time="3小时前",
        text="pl-003 · DeliveryAgent 成功创建 MR #42，已合并",
        type="success",
    ),
]


def _get_pipeline_or_404(pipeline_id: str) -> FrontendPipeline:
    for pipeline in PIPELINES:
        if pipeline.id == pipeline_id:
            return pipeline
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")


@router.get("/pipelines", response_model=list[FrontendPipeline])
async def list_pipelines() -> list[FrontendPipeline]:
    return PIPELINES


@router.get("/pipelines/{pipeline_id}", response_model=FrontendPipeline)
async def get_pipeline(pipeline_id: str) -> FrontendPipeline:
    return _get_pipeline_or_404(pipeline_id)


@router.get("/pipelines/{pipeline_id}/logs", response_model=list[str])
async def get_pipeline_logs(pipeline_id: str) -> list[str]:
    _get_pipeline_or_404(pipeline_id)
    return PIPELINE_LOGS.get(pipeline_id, [])


@router.get("/agents", response_model=list[FrontendAgent])
async def list_agents() -> list[FrontendAgent]:
    return AGENTS


@router.get("/checkpoints", response_model=list[FrontendCheckpoint])
async def list_checkpoints(
    status_value: str = Query(default="all", alias="status"),
) -> list[FrontendCheckpoint]:
    if status_value == "all":
        return CHECKPOINTS
    return [checkpoint for checkpoint in CHECKPOINTS if checkpoint.status == status_value]


@router.get("/analytics", response_model=FrontendAnalyticsOverview)
async def get_analytics() -> FrontendAnalyticsOverview:
    return ANALYTICS


@router.get("/activities/recent", response_model=list[FrontendActivityItem])
async def list_recent_activities() -> list[FrontendActivityItem]:
    return ACTIVITIES
