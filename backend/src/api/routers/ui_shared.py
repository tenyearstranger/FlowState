from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from src.config import get_config, get_stage_config
from src.api.schemas import (
    FrontendActivityItem,
    FrontendAgent,
    FrontendAnalyticsOverview,
    FrontendCheckpoint,
    FrontendPipeline,
    FrontendPipelineStage,
)
from src.api.service import PipelineService
from src.models.pipeline import (
    Pipeline,
    PipelineContext,
    PipelineStatus,
    StageNode,
    StageStatus,
    StageType,
)

CHECKPOINT_STAGE_TYPES = {
    StageType.REQUIREMENT,
    StageType.SOLUTION,
    StageType.TESTING,
    StageType.REVIEW,
    StageType.DELIVERY,
}

ACTIVITIES: list[FrontendActivityItem] = []


def make_stage(
    stage_type: StageType,
    status: StageStatus,
    *,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    output: dict | None = None,
    total_tokens: int | None = None,
) -> StageNode:
    stage = StageNode(
        stage_type=stage_type,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
    )
    if output is not None:
        stage.agent_output = output
    if total_tokens is not None:
        stage.total_tokens = total_tokens
        if stage.agent_output is None:
            stage.agent_output = {}
        stage.agent_output["usage"] = {
            "prompt_tokens": int(total_tokens * 0.4),
            "completion_tokens": int(total_tokens * 0.6),
            "total_tokens": total_tokens,
        }
    return stage


def build_seed_pipelines() -> list[Pipeline]:
    now = datetime.now()
    earlier = now - timedelta(minutes=45)
    mid = now - timedelta(minutes=25)
    recent = now - timedelta(minutes=10)

    pl_001 = Pipeline(
        id="pl-001",
        title="用户认证系统 · JWT Token 刷新",
        status=PipelineStatus.WAITING_HUMAN,
        context=PipelineContext(
            requirement_raw="实现 Access Token / Refresh Token 双 Token 机制，支持无感刷新",
            requirement_doc=(
                "## 结构化需求文档\n\n"
                "### 功能目标\n"
                "实现一个用户认证系统，支持 JWT Token 刷新机制。\n\n"
                "### 核心需求\n"
                "1. 用户注册：邮箱 + 密码，自动发送验证邮件\n"
                "2. 用户登录：支持邮箱/用户名登录，返回双 Token\n"
                "3. Token 刷新：Access Token 过期后自动刷新\n"
                "4. 用户登出：吊销 Refresh Token，清除会话"
            ),
            solution_doc=(
                "## 技术方案设计\n\n"
                "采用无状态 JWT 方案，Refresh Token 存储于 Redis，支持主动吊销。"
            ),
        ),
        stages=[
            make_stage(
                StageType.REQUIREMENT,
                StageStatus.COMPLETED,
                started_at=earlier,
                completed_at=mid,
                output={"document": "需求分析完成，已生成结构化需求文档。"},
                total_tokens=3200,
            ),
            make_stage(
                StageType.SOLUTION,
                StageStatus.WAITING_HUMAN,
                started_at=mid,
                completed_at=recent,
                output={"design": "技术方案已生成，等待审批。"},
                total_tokens=5680,
            ),
            make_stage(StageType.CODING, StageStatus.PENDING),
            make_stage(StageType.TESTING, StageStatus.PENDING),
            make_stage(StageType.REVIEW, StageStatus.PENDING),
            make_stage(StageType.DELIVERY, StageStatus.PENDING),
        ],
        logs=[
            "[08:30:01] Pipeline pl-001 已启动",
            "[08:30:35] 需求分析完成",
            "[08:31:08] 技术方案已生成，等待人工审批",
        ],
        created_at=earlier,
        updated_at=recent,
    )

    pl_002 = Pipeline(
        id="pl-002",
        title="API 限流中间件重构",
        status=PipelineStatus.WAITING_HUMAN,
        context=PipelineContext(
            requirement_raw="将现有的 IP 限流升级为基于用户/租户的分级限流策略",
            requirement_doc="需求分析完成，准备输出限流重构方案。",
            solution_doc="采用令牌桶算法，基于 Redis 实现用户级和租户级双层限流。",
        ),
        stages=[
            make_stage(
                StageType.REQUIREMENT,
                StageStatus.COMPLETED,
                started_at=earlier,
                completed_at=mid,
                output={"document": "需求分析完成，已生成需求文档。"},
                total_tokens=3010,
            ),
            make_stage(
                StageType.SOLUTION,
                StageStatus.WAITING_HUMAN,
                started_at=mid,
                completed_at=recent,
                output={"design": "限流重构方案已生成，等待审批。"},
                total_tokens=5210,
            ),
            make_stage(StageType.CODING, StageStatus.PENDING),
            make_stage(StageType.TESTING, StageStatus.PENDING),
            make_stage(StageType.REVIEW, StageStatus.PENDING),
            make_stage(StageType.DELIVERY, StageStatus.PENDING),
        ],
        logs=[
            "[15:02:11] Pipeline pl-002 已启动",
            "[15:10:04] 等待人工审批...",
        ],
        created_at=earlier,
        updated_at=recent,
    )

    pl_003 = Pipeline(
        id="pl-003",
        title="数据库连接池优化",
        status=PipelineStatus.RUNNING,
        context=PipelineContext(
            requirement_raw="修复高并发场景下连接池泄漏问题，优化超时配置",
            requirement_doc="需求分析完成，已确认优化范围。",
            solution_doc="连接池参数与回收策略优化方案已确认。",
        ),
        stages=[
            make_stage(
                StageType.REQUIREMENT,
                StageStatus.COMPLETED,
                started_at=earlier,
                completed_at=mid,
                output={"document": "需求分析完成。"},
                total_tokens=1820,
            ),
            make_stage(
                StageType.SOLUTION,
                StageStatus.COMPLETED,
                started_at=mid,
                completed_at=recent,
                output={"design": "技术方案已确认。"},
                total_tokens=2940,
            ),
            make_stage(
                StageType.CODING,
                StageStatus.RUNNING,
                started_at=recent,
                output={"text": "正在生成代码变更集..."},
            ),
            make_stage(StageType.TESTING, StageStatus.PENDING),
            make_stage(StageType.REVIEW, StageStatus.PENDING),
            make_stage(StageType.DELIVERY, StageStatus.PENDING),
        ],
        logs=[
            "[10:00:01] Pipeline pl-003 已启动",
            "[10:45:10] CodegenAgent 正在生成代码...",
        ],
        created_at=earlier,
        updated_at=now,
    )

    return [pl_001, pl_002, pl_003]


def seed_activities(pipelines: list[Pipeline]) -> None:
    ACTIVITIES.clear()
    for pipeline in pipelines[:3]:
        ACTIVITIES.append(
            FrontendActivityItem(
                time="刚刚",
                text=f"{pipeline.id} · {pipeline.title} 已进入运行队列",
                type="checkpoint" if pipeline.status == PipelineStatus.WAITING_HUMAN else "success",
            )
        )


def stage_type_label(stage_type: StageType) -> tuple[str, str]:
    labels = {
        StageType.REQUIREMENT: ("需求分析", "Requirements Analysis"),
        StageType.SOLUTION: ("方案设计", "Design"),
        StageType.CODING: ("代码生成", "Code Generation"),
        StageType.TESTING: ("测试生成", "Test Generation"),
        StageType.REVIEW: ("代码评审", "Code Review"),
        StageType.DELIVERY: ("交付集成", "Delivery"),
    }
    return labels[stage_type]


def stage_agent_name(stage_type: StageType) -> str:
    mapping = {
        StageType.REQUIREMENT: "RequirementsAgent",
        StageType.SOLUTION: "ArchitectAgent",
        StageType.CODING: "CodegenAgent",
        StageType.TESTING: "TestAgent",
        StageType.REVIEW: "ReviewAgent",
        StageType.DELIVERY: "DeliveryAgent",
    }
    return mapping[stage_type]


def frontend_stage_status(stage_status: StageStatus) -> str:
    mapping = {
        StageStatus.PENDING: "idle",
        StageStatus.RUNNING: "running",
        StageStatus.WAITING_HUMAN: "awaiting_review",
        StageStatus.APPROVED: "completed",
        StageStatus.REJECTED: "rejected",
        StageStatus.COMPLETED: "completed",
        StageStatus.FAILED: "failed",
    }
    return mapping[stage_status]


def frontend_pipeline_status(pipeline_status: PipelineStatus) -> str:
    mapping = {
        PipelineStatus.PENDING: "pending",
        PipelineStatus.RUNNING: "running",
        PipelineStatus.PAUSED: "paused",
        PipelineStatus.WAITING_HUMAN: "paused",
        PipelineStatus.COMPLETED: "completed",
        PipelineStatus.FAILED: "failed",
        PipelineStatus.CANCELLED: "cancelled",
    }
    return mapping[pipeline_status]


def serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def stage_duration_seconds(stage: StageNode) -> int | None:
    if stage.started_at is None or stage.completed_at is None:
        return None
    delta = int((stage.completed_at - stage.started_at).total_seconds())
    return max(delta, 0)


def stage_total_tokens(stage: StageNode) -> int | None:
    if stage.total_tokens is not None:
        return stage.total_tokens
    usage = stage.agent_output.get("usage") if stage.agent_output else None
    if isinstance(usage, dict):
        total = usage.get("total_tokens")
        if total is not None:
            return int(total)
        prompt = int(usage.get("prompt_tokens", 0) or 0)
        completion = int(usage.get("completion_tokens", 0) or 0)
        if prompt or completion:
            return prompt + completion
    return None


def extract_stage_output(pipeline: Pipeline, stage_type: StageType, agent_output: dict | None) -> str | None:
    if agent_output:
        for key in ("text", "document", "design", "report", "result", "summary"):
            value = agent_output.get(key)
            if isinstance(value, str) and value.strip():
                return value
    context_fallback = {
        StageType.REQUIREMENT: pipeline.context.requirement_doc,
        StageType.SOLUTION: pipeline.context.solution_doc,
        StageType.TESTING: pipeline.context.test_report,
        StageType.REVIEW: pipeline.context.review_report,
        StageType.DELIVERY: pipeline.context.delivery_result,
    }
    if stage_type == StageType.CODING and pipeline.context.generated_code:
        return "\n".join(
            f"{path}\n{content}" for path, content in pipeline.context.generated_code.items()
        )
    return context_fallback.get(stage_type)


def calculate_progress(pipeline: Pipeline) -> int:
    if not pipeline.stages:
        return 0
    completed = sum(
        1 for stage in pipeline.stages
        if stage.status in {StageStatus.COMPLETED, StageStatus.APPROVED, StageStatus.WAITING_HUMAN}
    )
    if pipeline.status == PipelineStatus.RUNNING:
        running_bonus = 8 if any(stage.status == StageStatus.RUNNING for stage in pipeline.stages) else 0
        return min(99, round((completed / len(pipeline.stages)) * 100) + running_bonus)
    return round((completed / len(pipeline.stages)) * 100)


def current_stage_index(pipeline: Pipeline) -> int:
    for index, stage in enumerate(pipeline.stages):
        if stage.status not in {StageStatus.COMPLETED, StageStatus.APPROVED}:
            return index
    return max(len(pipeline.stages) - 1, 0)


def to_frontend_pipeline(pipeline: Pipeline) -> FrontendPipeline:
    stages = []
    for index, stage in enumerate(pipeline.stages):
        name, name_en = stage_type_label(stage.stage_type)
        stages.append(
            FrontendPipelineStage(
                id=f"{pipeline.id}-stage-{index + 1}",
                name=name,
                nameEn=name_en,
                agent=stage_agent_name(stage.stage_type),
                status=frontend_stage_status(stage.status),
                duration=stage_duration_seconds(stage),
                tokens=stage_total_tokens(stage),
                output=extract_stage_output(pipeline, stage.stage_type, stage.agent_output),
                isCheckpoint=stage.stage_type in CHECKPOINT_STAGE_TYPES,
                startedAt=serialize_datetime(stage.started_at),
                completedAt=serialize_datetime(stage.completed_at),
            )
        )

    return FrontendPipeline(
        id=pipeline.id,
        name=pipeline.title or pipeline.context.requirement_raw[:60],
        description=pipeline.context.requirement_raw,
        status=frontend_pipeline_status(pipeline.status),
        progress=calculate_progress(pipeline),
        currentStage=current_stage_index(pipeline),
        stages=stages,
        createdAt=serialize_datetime(pipeline.created_at) or "",
        updatedAt=serialize_datetime(pipeline.updated_at) or "",
        template="新功能开发",
        projectPath=pipeline.context.project_path or None,
        projectSummary=pipeline.context.project_summary,
        requirementDocPath=pipeline.context.requirement_doc_path,
        solutionDocPath=pipeline.context.solution_doc_path,
    )


def to_frontend_checkpoint(pipeline: Pipeline, stage: StageType, index: int) -> FrontendCheckpoint | None:
    stage_node = pipeline.stages[index]
    if stage_node.status not in {
        StageStatus.WAITING_HUMAN,
        StageStatus.APPROVED,
        StageStatus.REJECTED,
    }:
        return None

    stage_name, _ = stage_type_label(stage)
    created_at = (
        serialize_datetime(stage_node.completed_at)
        or serialize_datetime(stage_node.started_at)
        or serialize_datetime(pipeline.updated_at)
        or serialize_datetime(pipeline.created_at)
        or datetime.now(timezone.utc).isoformat()
    )
    return FrontendCheckpoint(
        id=build_checkpoint_id(pipeline.id, stage),
        pipelineId=pipeline.id,
        pipelineName=pipeline.title or pipeline.context.requirement_raw[:60],
        stage=stage_name,
        stageIndex=index,
        status=(
            "pending"
            if stage_node.status == StageStatus.WAITING_HUMAN
            else "approved"
            if stage_node.status == StageStatus.APPROVED
            else "rejected"
        ),
        createdAt=created_at,
        output=extract_stage_output(pipeline, stage, stage_node.agent_output) or "",
        rejectReason=stage_node.human_feedback,
    )


def build_checkpoint_id(pipeline_id: str, stage: StageType) -> str:
    return f"cp-{pipeline_id}-{stage.value}"


def build_dynamic_agents(pipelines: list[Pipeline]) -> list[FrontendAgent]:
    cfg = get_config()
    agent_meta = {
        StageType.REQUIREMENT: {
            "id": "requirements-agent",
            "name": "RequirementsAgent",
            "role": "需求分析",
            "description": "负责解析原始需求，输出结构化需求文档与模块划分。",
            "color": "#5B72FF",
        },
        StageType.SOLUTION: {
            "id": "architect-agent",
            "name": "ArchitectAgent",
            "role": "方案设计",
            "description": "负责输出技术方案、接口设计与文件规划。",
            "color": "#A259FF",
        },
        StageType.CODING: {
            "id": "codegen-agent",
            "name": "CodegenAgent",
            "role": "代码生成",
            "description": "负责根据方案分批生成多文件代码。",
            "color": "#FF7A5C",
        },
        StageType.TESTING: {
            "id": "test-agent",
            "name": "TestAgent",
            "role": "测试生成",
            "description": "负责生成测试、汇总报告并判断是否需要人工确认。",
            "color": "#34C759",
        },
        StageType.REVIEW: {
            "id": "review-agent",
            "name": "ReviewAgent",
            "role": "代码评审",
            "description": "负责给出代码质量、风险和改进建议。",
            "color": "#FF9F0A",
        },
        StageType.DELIVERY: {
            "id": "delivery-agent",
            "name": "DeliveryAgent",
            "role": "交付集成",
            "description": "负责产出交付清单、PR 信息和部署说明。",
            "color": "#00C7BE",
        },
    }
    stage_stats: dict[StageType, dict[str, int | list[int] | str]] = {
        stage_type: {
            "tasks_completed": 0,
            "running": 0,
            "durations": [],
            "tokens": [],
            "model": "",
        }
        for stage_type in StageType
    }

    for pipeline in pipelines:
        for stage in pipeline.stages:
            entry = stage_stats[stage.stage_type]
            if stage.status == StageStatus.RUNNING:
                entry["running"] = int(entry["running"]) + 1
            if stage.status in {StageStatus.COMPLETED, StageStatus.APPROVED, StageStatus.WAITING_HUMAN}:
                entry["tasks_completed"] = int(entry["tasks_completed"]) + 1
            duration = stage_duration_seconds(stage)
            if duration is not None:
                cast_list = entry["durations"]
                assert isinstance(cast_list, list)
                cast_list.append(duration)
            tokens = stage_total_tokens(stage)
            if tokens is not None:
                cast_list = entry["tokens"]
                assert isinstance(cast_list, list)
                cast_list.append(tokens)
            if stage.model_name:
                entry["model"] = stage.model_name

    agents: list[FrontendAgent] = []
    for stage_type in StageType:
        meta = agent_meta[stage_type]
        stats = stage_stats[stage_type]
        durations = stats["durations"]
        tokens = stats["tokens"]
        assert isinstance(durations, list)
        assert isinstance(tokens, list)
        stage_cfg = get_stage_config(stage_type.value)
        provider_name = str(
            stage_cfg.provider_override
            or cfg.llm.provider.value
        ).replace("_", " ").title()
        resolved_model = str(stats["model"] or stage_cfg.model_override or cfg.llm.model or "unknown")
        agents.append(
            FrontendAgent(
                id=meta["id"],
                name=meta["name"],
                role=meta["role"],
                description=meta["description"],
                model=resolved_model,
                provider=provider_name,
                status="running" if int(stats["running"]) > 0 else "idle",
                tasksCompleted=int(stats["tasks_completed"]),
                avgDuration=round(sum(durations) / len(durations)) if durations else 0,
                avgTokens=round(sum(tokens) / len(tokens)) if tokens else 0,
                color=meta["color"],
            )
        )
    return agents


def build_dynamic_analytics(pipelines: list[Pipeline]) -> FrontendAnalyticsOverview:
    today = datetime.now().date()
    day_buckets = {
        day: {"success": 0, "failed": 0, "total": 0}
        for day in range(7)
    }
    token_buckets: dict[str, int] = defaultdict(int)
    stage_duration_buckets: dict[StageType, list[int]] = defaultdict(list)

    total_tokens = 0
    total_success = 0
    total_duration_minutes = 0.0
    merged_changes = 0

    for pipeline in pipelines:
        created_date = pipeline.created_at.date()
        delta_days = (today - created_date).days
        if 0 <= delta_days <= 6:
            bucket = day_buckets[6 - delta_days]
            bucket["total"] += 1
            if pipeline.status == PipelineStatus.COMPLETED:
                bucket["success"] += 1
            elif pipeline.status == PipelineStatus.FAILED:
                bucket["failed"] += 1

        if pipeline.status == PipelineStatus.COMPLETED:
            total_success += 1
            merged_changes += 1

        total_duration_minutes += max(
            0.0,
            (pipeline.updated_at - pipeline.created_at).total_seconds() / 60.0,
        )

        for stage in pipeline.stages:
            stage_tokens = stage_total_tokens(stage) or 0
            total_tokens += stage_tokens
            if stage_tokens and stage.completed_at is not None and stage.completed_at.date() == today:
                bucket_key = stage.completed_at.strftime("%H:00")
                token_buckets[bucket_key] += stage_tokens
            duration = stage_duration_seconds(stage)
            if duration is not None:
                stage_duration_buckets[stage.stage_type].append(duration)

    pipeline_runs = []
    for offset, label in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        bucket = day_buckets[offset]
        pipeline_runs.append(
            {
                "day": label,
                "success": bucket["success"],
                "failed": bucket["failed"],
                "total": bucket["total"],
            }
        )

    current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
    token_usage = []
    for offset in range(6, -1, -1):
        bucket_time = current_hour - timedelta(hours=offset)
        label = bucket_time.strftime("%H:00")
        token_usage.append({"time": label, "tokens": token_buckets.get(label, 0)})

    stage_durations = []
    for stage_type in StageType:
        durations = sorted(stage_duration_buckets.get(stage_type, []))
        avg = round(sum(durations) / len(durations)) if durations else 0
        p95_index = max(0, round(len(durations) * 0.95) - 1) if durations else 0
        p95 = durations[p95_index] if durations else 0
        stage_name, _ = stage_type_label(stage_type)
        stage_durations.append({"stage": stage_name, "avg": avg, "p95": p95})

    agent_success_rates = []
    for stage_type in StageType:
        relevant = [
            stage
            for pipeline in pipelines
            for stage in pipeline.stages
            if stage.stage_type == stage_type
            and stage.status in {
                StageStatus.COMPLETED,
                StageStatus.APPROVED,
                StageStatus.WAITING_HUMAN,
                StageStatus.FAILED,
            }
        ]
        success_count = sum(
            1
            for stage in relevant
            if stage.status in {StageStatus.COMPLETED, StageStatus.APPROVED, StageStatus.WAITING_HUMAN}
        )
        stage_name, _ = stage_type_label(stage_type)
        agent_success_rates.append(
            {
                "name": stage_name,
                "rate": round((success_count / len(relevant)) * 100, 1) if relevant else 0.0,
            }
        )

    return FrontendAnalyticsOverview.model_validate(
        {
            "summary": {
                "totalRuns": len(pipelines),
                "totalSuccess": total_success,
                "totalTokens": total_tokens,
                "averageDurationMinutes": round(total_duration_minutes / len(pipelines), 1) if pipelines else 0,
                "mergedChanges": merged_changes,
            },
            "pipelineRuns": pipeline_runs,
            "tokenUsage": token_usage,
            "stageDurations": stage_durations,
            "agentSuccessRates": agent_success_rates,
        }
    )


async def list_persisted_checkpoints(service: PipelineService) -> list[FrontendCheckpoint]:
    checkpoints: list[FrontendCheckpoint] = []
    for pipeline in await service.list_pipelines():
        for index, stage_node in enumerate(pipeline.stages):
            if stage_node.stage_type not in CHECKPOINT_STAGE_TYPES:
                continue
            checkpoint = to_frontend_checkpoint(pipeline, stage_node.stage_type, index)
            if checkpoint is not None:
                checkpoints.append(checkpoint)
    checkpoints.sort(key=lambda item: item.createdAt, reverse=True)
    return checkpoints


async def find_persisted_checkpoint(
    checkpoint_id: str,
    service: PipelineService,
) -> tuple[Pipeline, int, FrontendCheckpoint] | None:
    for pipeline in await service.list_pipelines():
        for index, stage_node in enumerate(pipeline.stages):
            if stage_node.stage_type not in CHECKPOINT_STAGE_TYPES:
                continue
            if build_checkpoint_id(pipeline.id, stage_node.stage_type) != checkpoint_id:
                continue
            checkpoint = to_frontend_checkpoint(pipeline, stage_node.stage_type, index)
            if checkpoint is None:
                return None
            return pipeline, index, checkpoint
    return None
