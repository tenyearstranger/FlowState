"""DevFlow Engine — AI 驱动研发流水线引擎核心"""

import asyncio
from typing import Optional, Callable, Dict
from datetime import datetime

from src.models.pipeline import (
    Pipeline,
    StageNode,
    StageType,
    StageStatus,
    PipelineStatus,
    PipelineContext,
    ApproveAction,
)
from src.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from src.store.state_store import StateStore
from src.config import get_config, get_stage_config, OutputMode


class DevFlowEngine:
    """
    AI 驱动研发流水线引擎

    职责：
    1. 编排多阶段 Pipeline（需求→方案→编码→测试→评审→交付）
    2. 管理每个 Agent 的生命周期
    3. 处理 Human-in-the-Loop 决策节点
    4. 持久化 Pipeline 状态
    """

    def __init__(self, state_store: Optional[StateStore] = None):
        self.agents: Dict[StageType, BaseAgent] = {}
        self.cfg = get_config()
        self.state_store = state_store or StateStore(storage_dir=self.cfg.pipeline.storage_dir)
        self._on_status_change: Optional[Callable] = None

    def register_agent(self, stage: StageType, agent: BaseAgent) -> None:
        """注册阶段 Agent"""
        self.agents[stage] = agent

    def on_status_change(self, callback: Callable) -> None:
        """注册状态变更回调（用于前端实时更新）"""
        self._on_status_change = callback

    # ------------------------------------------------------------
    # Pipeline 生命周期管理
    # ------------------------------------------------------------

    async def create_pipeline(
        self, requirement: str, title: str = ""
    ) -> Pipeline:
        """从需求描述创建新的流水线"""
        pipeline = Pipeline(
            title=title or requirement[:60],
            context=PipelineContext(requirement_raw=requirement),
            stages=[
                StageNode(stage_type=StageType.REQUIREMENT),
                StageNode(stage_type=StageType.SOLUTION),
                StageNode(stage_type=StageType.CODING),
                StageNode(stage_type=StageType.TESTING),
                StageNode(stage_type=StageType.REVIEW),
                StageNode(stage_type=StageType.DELIVERY),
            ],
        )
        await self.state_store.save(pipeline)
        return pipeline

    async def run_pipeline(self, pipeline: Pipeline) -> None:
        """
        执行完整流水线

        工作流：
        - 遍历所有阶段，依次执行
        - 如果某个阶段需要人类确认，暂停等待
        - 人类通过 approve_stage() 触发继续
        """
        pipeline.status = PipelineStatus.RUNNING
        await self._notify(pipeline)

        for idx, stage in enumerate(pipeline.stages):
            # 检查是否被取消
            if pipeline.status == PipelineStatus.CANCELLED:
                break

            # 跳过已完成的阶段（从暂停恢复时）
            if stage.status in (StageStatus.COMPLETED, StageStatus.APPROVED):
                continue

            await self._execute_stage(pipeline, stage, idx)

            # 如果需要人类确认，暂停流水线等待
            if stage.status == StageStatus.WAITING_HUMAN:
                pipeline.status = PipelineStatus.WAITING_HUMAN
                await self._notify(pipeline)
                await self.state_store.save(pipeline)
                return  # 等待外部调用 approve_stage()

        # 所有阶段执行完毕
        pipeline.status = PipelineStatus.COMPLETED
        pipeline.updated_at = datetime.now()
        await self._notify(pipeline)
        await self.state_store.save(pipeline)

    async def _execute_stage(
        self, pipeline: Pipeline, stage: StageNode, stage_index: int
    ) -> None:
        """执行单个阶段"""
        agent = self.agents.get(stage.stage_type)
        if not agent:
            raise ValueError(
                f"未注册 Agent 用于阶段: {stage.stage_type.value}"
            )

        stage.status = StageStatus.RUNNING
        stage.started_at = datetime.now()
        await self._notify(pipeline)

        try:
            input_data = AgentInput(
                task_description=f"执行阶段: {stage.stage_type.value}",
                context=pipeline.context.model_dump(),
                human_feedback=stage.human_feedback,
            )

            output = await agent.execute(input_data)
            stage.agent_output = output.result
            stage.completed_at = datetime.now()

            # 更新 Pipeline 上下文
            self._update_context(pipeline, stage.stage_type, output.result, output)

            # 判断是否需要人类确认：
            # 1. 全局配置为 AUTO 模式 → 跳过人工确认
            # 2. Agent 主动要求确认（needs_human_review）
            # 3. 该阶段的配置要求确认
            stage_cfg = get_stage_config(stage.stage_type.value)
            needs_human = (
                self.cfg.pipeline.output_mode != OutputMode.AUTO
                and (
                    output.needs_human_review
                    or stage_cfg.needs_human_review
                )
            )

            if needs_human:
                stage.status = StageStatus.WAITING_HUMAN
            else:
                stage.status = StageStatus.COMPLETED

        except Exception as e:
            stage.status = StageStatus.FAILED
            pipeline.error = f"[{stage.stage_type.value}] {str(e)}"
            pipeline.status = PipelineStatus.FAILED
            await self._notify(pipeline)
            await self.state_store.save(pipeline)
            raise

    # ------------------------------------------------------------
    # 人类决策节点
    # ------------------------------------------------------------

    async def approve_stage(
        self,
        pipeline_id: str,
        stage_index: int,
        action: ApproveAction,
        feedback: str = "",
    ) -> None:
        """
        人类对某个阶段的审批操作

        - APPROVE: 确认通过，继续执行下一阶段
        - REJECT: 驳回，终止流水线
        - REVISE: 需要修改，携带反馈重新执行当前阶段
        """
        pipeline = await self.state_store.load(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline 不存在: {pipeline_id}")

        stage = pipeline.stages[stage_index]
        stage.human_approval = action
        stage.human_feedback = feedback

        if action == ApproveAction.APPROVE:
            stage.status = StageStatus.APPROVED
            pipeline.status = PipelineStatus.RUNNING
            await self.state_store.save(pipeline)
            # 继续执行流水线
            await self.run_pipeline(pipeline)

        elif action == ApproveAction.REJECT:
            stage.status = StageStatus.REJECTED
            pipeline.status = PipelineStatus.FAILED
            pipeline.error = f"阶段 '{stage.stage_type.value}' 被人类驳回"
            await self._notify(pipeline)
            await self.state_store.save(pipeline)

        elif action == ApproveAction.REVISE:
            stage.status = StageStatus.PENDING
            stage.retry_count += 1
            stage.human_feedback = feedback
            pipeline.status = PipelineStatus.RUNNING
            await self.state_store.save(pipeline)
            # 重新执行当前阶段
            await self._execute_stage(pipeline, stage, stage_index)
            await self.run_pipeline(pipeline)

    # ------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------

    def _update_context(
        self,
        pipeline: Pipeline,
        stage: StageType,
        result: dict,
        agent_output: AgentOutput = None,
    ) -> None:
        """根据阶段输出更新 Pipeline 上下文"""
        stage_map = {
            StageType.REQUIREMENT: ("requirement_doc", "document"),
            StageType.SOLUTION: ("solution_doc", "design"),
            StageType.CODING: ("generated_code", "files"),
            StageType.TESTING: ("test_report", "report"),
            StageType.REVIEW: ("review_report", "report"),
            StageType.DELIVERY: ("delivery_result", "result"),
        }

        if stage in stage_map:
            ctx_field, result_key = stage_map[stage]
            if result_key in result:
                setattr(pipeline.context, ctx_field, result[result_key])
            elif agent_output and agent_output.details:
                setattr(pipeline.context, ctx_field, agent_output.details)

        if stage == StageType.SOLUTION and "structured_solution" in result:
            pipeline.context.solution_structured = result["structured_solution"]

        pipeline.updated_at = datetime.now()

    async def run_fully_auto(self, requirement: str) -> Pipeline:
        """
        全自动模式（无人类干预，直接运行到结束）
        适用于测试连通性
        """
        pipeline = await self.create_pipeline(requirement)

        for idx, stage in enumerate(pipeline.stages):
            agent = self.agents.get(stage.stage_type)
            if not agent:
                raise ValueError(f"未注册 Agent: {stage.stage_type.value}")

            stage.status = StageStatus.RUNNING
            stage.started_at = datetime.now()

            input_data = AgentInput(
                task_description=f"执行阶段: {stage.stage_type.value}",
                context=pipeline.context.model_dump(),
            )

            output = await agent.execute(input_data)
            stage.agent_output = output.result
            stage.completed_at = datetime.now()
            stage.status = StageStatus.COMPLETED  # 全自动模式下直接完成

            self._update_context(pipeline, stage.stage_type, output.result, output)
            pipeline.updated_at = datetime.now()

            print(
                f"  [{idx + 1}/{len(pipeline.stages)}] "
                f"{stage.stage_type.value:25s} "
                f"✅  {output.summary}"
            )

        pipeline.status = PipelineStatus.COMPLETED
        await self.state_store.save(pipeline)
        return pipeline

    async def _notify(self, pipeline: Pipeline) -> None:
        """触发状态变更通知"""
        if self._on_status_change:
            if asyncio.iscoroutinefunction(self._on_status_change):
                await self._on_status_change(pipeline)
            else:
                self._on_status_change(pipeline)
