"""Small service layer that keeps the API decoupled from runtime details."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from src.agents.base_agent import AgentInput
from src.agents.code_agent import CodeAgent
from src.agents.requirement_agent import RequirementAgent
from src.agents.solution_agent import SolutionAgent
from src.models.pipeline import (
    ApproveAction,
    Pipeline,
    PipelineContext,
    PipelineStatus,
    StageNode,
    StageStatus,
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


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


class PipelineValidationError(ValueError):
    """Raised when incoming pipeline creation data is invalid."""


def _resolve_project_path(project_path: str) -> Path | None:
    if not project_path.strip():
        return None

    resolved_path = Path(project_path).expanduser().resolve()
    if not resolved_path.exists():
        raise PipelineValidationError(f"项目目录不存在: {resolved_path}")
    if not resolved_path.is_dir():
        raise PipelineValidationError(f"项目路径不是文件夹: {resolved_path}")
    return resolved_path


def _summarize_project_path(project_path: Path) -> str:
    top_level_dirs: list[str] = []
    top_level_files: list[str] = []
    for item in sorted(project_path.iterdir(), key=lambda entry: (not entry.is_dir(), entry.name.lower())):
        if item.is_dir():
            top_level_dirs.append(item.name)
        else:
            top_level_files.append(item.name)

    total_dirs = 0
    total_files = 0
    for _, dirnames, filenames in os.walk(project_path):
        total_dirs += len(dirnames)
        total_files += len(filenames)

    key_files = [
        name for name in (
            "package.json",
            "pnpm-lock.yaml",
            "package-lock.json",
            "yarn.lock",
            "pyproject.toml",
            "requirements.txt",
            "Cargo.toml",
            "go.mod",
            "Dockerfile",
            "README.md",
        )
        if (project_path / name).exists()
    ]

    preview_dirs = "、".join(top_level_dirs[:6]) if top_level_dirs else "无"
    preview_files = "、".join(top_level_files[:6]) if top_level_files else "无"
    preview_key_files = "、".join(key_files) if key_files else "未识别到常见入口文件"

    return (
        "## 项目目录扫描\n\n"
        f"- 根目录：{project_path}\n"
        f"- 顶层目录：{preview_dirs}\n"
        f"- 顶层文件：{preview_files}\n"
        f"- 关键文件：{preview_key_files}\n"
        f"- 目录总数：{total_dirs}\n"
        f"- 文件总数：{total_files}"
    )


def _write_project_doc(project_path: str, filename: str, content: str) -> Path:
    if not project_path:
        raise PipelineValidationError("缺少项目目录，无法写入阶段文档")

    main_dir = Path(project_path) / "main"
    main_dir.mkdir(parents=True, exist_ok=True)
    doc_path = main_dir / filename
    doc_path.write_text(content, encoding="utf-8")
    return doc_path


def _normalize_generated_filepath(filepath: str) -> Path:
    cleaned = filepath.strip().lstrip("/").replace("\\", "/")
    relative_path = Path(cleaned)
    if not cleaned or any(part == ".." for part in relative_path.parts):
        raise PipelineValidationError(f"生成了非法文件路径: {filepath}")
    return relative_path


def _write_generated_code(project_path: str, files: dict[str, str]) -> list[str]:
    if not project_path:
        raise PipelineValidationError("缺少项目目录，无法写入生成代码")

    base_dir = Path(project_path)
    written_files: list[str] = []
    for filepath, content in files.items():
        relative_path = _normalize_generated_filepath(filepath)
        target_path = base_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        written_files.append(str(target_path))
    return written_files


class PipelineService:
    """A tiny adapter around either an injected engine or local persistence."""

    def __init__(self, engine=None, state_store: StateStore | None = None):
        self.engine = engine
        self.state_store = state_store or getattr(engine, "state_store", None) or StateStore()

    async def create_pipeline(
        self,
        *,
        title: str,
        requirement: str,
        project_path: str = "",
        start_immediately: bool = False,
    ) -> Pipeline:
        resolved_project_path = _resolve_project_path(project_path)
        normalized_project_path = str(resolved_project_path) if resolved_project_path else project_path.strip()
        project_summary = (
            _summarize_project_path(resolved_project_path)
            if resolved_project_path is not None
            else None
        )

        if self.engine is not None:
            pipeline = await self.engine.create_pipeline(requirement=requirement, title=title)
            pipeline.context.project_path = normalized_project_path
            pipeline.context.project_summary = project_summary
        else:
            now = datetime.now()
            pipeline = Pipeline(
                title=title or requirement[:60],
                status=PipelineStatus.PENDING,
                context=PipelineContext(
                    project_path=normalized_project_path,
                    project_summary=project_summary,
                    requirement_raw=requirement,
                ),
                stages=_build_default_stages(),
                created_at=now,
                updated_at=now,
            )

        if not pipeline.logs:
            pipeline.logs = [
                f"[{_timestamp()}] Pipeline 已创建",
                *([f"[{_timestamp()}] 工作目录: {normalized_project_path}"] if normalized_project_path else []),
                *([f"[{_timestamp()}] 已接收需求: {requirement[:80]}"] if requirement else []),
                *([f"[{_timestamp()}] 项目目录扫描完成"] if project_summary else []),
            ]

        if start_immediately and pipeline.stages:
            now = datetime.now()
            pipeline.status = PipelineStatus.RUNNING
            pipeline.updated_at = now
            pipeline.stages[0].status = StageStatus.RUNNING
            pipeline.stages[0].started_at = now
            pipeline.stages[0].agent_output = {
                "text": (
                    "## 已接收任务\n\n"
                    f"项目目录：{normalized_project_path or '未提供'}\n\n"
                    f"需求描述：{requirement}\n\n"
                    f"{project_summary or '未执行项目目录扫描。'}"
                )
            }
            if not any("RequirementsAgent 正在分析需求" in item for item in pipeline.logs):
                pipeline.logs.append(f"[{_timestamp()}] RequirementsAgent 正在分析需求...")

            await self._run_requirement_analysis(pipeline)

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

    async def approve_stage(self, pipeline_id: str, stage_index: int) -> Pipeline:
        pipeline = await self.state_store.load(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        if stage_index < 0 or stage_index >= len(pipeline.stages):
            raise ValueError(f"Invalid stage index: {stage_index}")

        stage = pipeline.stages[stage_index]
        if stage.status != StageStatus.WAITING_HUMAN:
            raise ValueError("当前阶段不处于待审批状态")

        now = datetime.now()
        stage.human_approval = ApproveAction.APPROVE
        stage.status = StageStatus.APPROVED
        stage.completed_at = stage.completed_at or now
        pipeline.updated_at = now
        pipeline.logs.append(f"[{_timestamp()}] 人工审批通过: {stage.stage_type.value}")

        if stage.stage_type == StageType.REQUIREMENT:
            pipeline.logs.append(f"[{_timestamp()}] 已推进到下一阶段: {StageType.SOLUTION.value}")
            await self._run_solution_design(pipeline)
        elif stage.stage_type == StageType.SOLUTION:
            pipeline.logs.append(f"[{_timestamp()}] 已推进到下一阶段: {StageType.CODING.value}")
            await self._run_code_generation(pipeline)
        else:
            next_stage = pipeline.stages[stage_index + 1] if stage_index + 1 < len(pipeline.stages) else None
            if next_stage is not None:
                next_stage.status = StageStatus.RUNNING
                next_stage.started_at = now
                if not next_stage.agent_output:
                    next_stage.agent_output = {
                        "text": (
                            f"## {next_stage.stage_type.value} 已进入执行队列\n\n"
                            "上一阶段审批已通过，当前阶段已被调度。"
                        )
                    }
                pipeline.status = PipelineStatus.RUNNING
                pipeline.logs.append(f"[{_timestamp()}] 已推进到下一阶段: {next_stage.stage_type.value}")
            else:
                pipeline.status = PipelineStatus.COMPLETED
                pipeline.logs.append(f"[{_timestamp()}] 所有阶段已完成")

            await self.state_store.save(pipeline)
        return pipeline

    async def reject_stage(self, pipeline_id: str, stage_index: int, reason: str) -> Pipeline:
        pipeline = await self.state_store.load(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        if stage_index < 0 or stage_index >= len(pipeline.stages):
            raise ValueError(f"Invalid stage index: {stage_index}")

        stage = pipeline.stages[stage_index]
        if stage.status != StageStatus.WAITING_HUMAN:
            raise ValueError("当前阶段不处于待审批状态")

        now = datetime.now()
        stage.human_approval = ApproveAction.REJECT
        stage.human_feedback = reason
        stage.status = StageStatus.REJECTED
        stage.completed_at = stage.completed_at or now
        pipeline.updated_at = now
        pipeline.status = PipelineStatus.WAITING_HUMAN
        pipeline.logs.append(f"[{_timestamp()}] 人工审批拒绝: {stage.stage_type.value}")
        if reason:
            pipeline.logs.append(f"[{_timestamp()}] 拒绝原因: {reason}")

        await self.state_store.save(pipeline)
        return pipeline

    async def _run_requirement_analysis(self, pipeline: Pipeline) -> None:
        """执行需求分析阶段，生成第一版结构化需求文档。"""
        if not pipeline.stages:
            return

        requirement_stage = pipeline.stages[0]
        try:
            if self.engine is not None and StageType.REQUIREMENT in getattr(self.engine, "agents", {}):
                agent = self.engine.agents[StageType.REQUIREMENT]
            else:
                agent = RequirementAgent()

            input_data = AgentInput(
                task_description="执行阶段: requirement_analysis",
                context=pipeline.context.model_dump(),
            )
            output = await agent.execute(input_data)
            now = datetime.now()
            requirement_stage.agent_output = output.result
            requirement_stage.status = (
                StageStatus.WAITING_HUMAN
                if output.needs_human_review
                else StageStatus.COMPLETED
            )
            requirement_stage.completed_at = now
            requirement_doc = output.result.get("document") or output.details
            pipeline.context.requirement_doc = requirement_doc
            if requirement_doc:
                requirement_doc_path = _write_project_doc(
                    pipeline.context.project_path,
                    "requirements.md",
                    requirement_doc,
                )
                pipeline.context.requirement_doc_path = str(requirement_doc_path)
            pipeline.updated_at = now
            pipeline.status = (
                PipelineStatus.WAITING_HUMAN
                if output.needs_human_review
                else PipelineStatus.PENDING
            )
            pipeline.logs.append(f"[{_timestamp()}] {output.summary}")
            if pipeline.context.requirement_doc_path:
                pipeline.logs.append(
                    f"[{_timestamp()}] 需求文档已写入: {pipeline.context.requirement_doc_path}"
                )
            if output.needs_human_review:
                pipeline.logs.append(f"[{_timestamp()}] 需求分析进入人工确认，等待审批")
        except Exception as error:
            requirement_stage.status = StageStatus.FAILED
            requirement_stage.completed_at = datetime.now()
            pipeline.status = PipelineStatus.FAILED
            pipeline.error = f"[requirement_analysis] {error}"
            pipeline.logs.append(f"[{_timestamp()}] 需求分析失败: {error}")
            raise

    async def _run_solution_design(self, pipeline: Pipeline) -> None:
        if len(pipeline.stages) < 2:
            return

        solution_stage = pipeline.stages[1]
        now = datetime.now()
        solution_stage.status = StageStatus.RUNNING
        solution_stage.started_at = now
        solution_stage.agent_output = {
            "text": (
                "## 正在生成技术方案\n\n"
                "需求分析已审批通过，正在根据需求文档和项目上下文生成方案设计。"
            )
        }
        pipeline.status = PipelineStatus.RUNNING
        pipeline.updated_at = now
        pipeline.logs.append(f"[{_timestamp()}] SolutionAgent 正在生成技术方案...")

        try:
            if self.engine is not None and StageType.SOLUTION in getattr(self.engine, "agents", {}):
                agent = self.engine.agents[StageType.SOLUTION]
            else:
                agent = SolutionAgent()

            input_data = AgentInput(
                task_description="执行阶段: solution_design",
                context=pipeline.context.model_dump(),
                human_feedback=solution_stage.human_feedback,
            )
            output = await agent.execute(input_data)
            now = datetime.now()
            solution_stage.agent_output = output.result
            solution_stage.status = (
                StageStatus.WAITING_HUMAN
                if output.needs_human_review
                else StageStatus.COMPLETED
            )
            solution_stage.completed_at = now
            solution_doc = output.result.get("design") or output.details
            pipeline.context.solution_doc = solution_doc
            structured_solution = output.result.get("structured_solution")
            if isinstance(structured_solution, dict):
                pipeline.context.solution_structured = structured_solution
            if solution_doc:
                solution_doc_path = _write_project_doc(
                    pipeline.context.project_path,
                    "solution.md",
                    solution_doc,
                )
                pipeline.context.solution_doc_path = str(solution_doc_path)
            pipeline.updated_at = now
            pipeline.status = (
                PipelineStatus.WAITING_HUMAN
                if output.needs_human_review
                else PipelineStatus.PENDING
            )
            pipeline.logs.append(f"[{_timestamp()}] {output.summary}")
            if pipeline.context.solution_doc_path:
                pipeline.logs.append(
                    f"[{_timestamp()}] 技术方案文档已写入: {pipeline.context.solution_doc_path}"
                )
            if output.needs_human_review:
                pipeline.logs.append(f"[{_timestamp()}] 方案设计进入人工确认，等待审批")
            await self.state_store.save(pipeline)
        except Exception as error:
            solution_stage.status = StageStatus.FAILED
            solution_stage.completed_at = datetime.now()
            pipeline.status = PipelineStatus.FAILED
            pipeline.error = f"[solution_design] {error}"
            pipeline.logs.append(f"[{_timestamp()}] 方案设计失败: {error}")
            await self.state_store.save(pipeline)
            raise

    async def _run_code_generation(self, pipeline: Pipeline) -> None:
        if len(pipeline.stages) < 3:
            return

        coding_stage = pipeline.stages[2]
        now = datetime.now()
        coding_stage.status = StageStatus.RUNNING
        coding_stage.started_at = now
        coding_stage.agent_output = {
            "text": (
                "## 正在生成代码\n\n"
                "方案设计已审批通过，正在根据技术方案生成项目代码。"
            )
        }
        pipeline.status = PipelineStatus.RUNNING
        pipeline.updated_at = now
        pipeline.logs.append(f"[{_timestamp()}] CodeAgent 正在生成代码...")

        try:
            if self.engine is not None and StageType.CODING in getattr(self.engine, "agents", {}):
                agent = self.engine.agents[StageType.CODING]
            else:
                agent = CodeAgent()

            input_data = AgentInput(
                task_description="执行阶段: coding",
                context=pipeline.context.model_dump(),
                human_feedback=coding_stage.human_feedback,
            )
            output = await agent.execute(input_data)
            now = datetime.now()
            coding_stage.agent_output = output.result
            coding_stage.status = StageStatus.COMPLETED
            coding_stage.completed_at = now

            generated_files = output.result.get("files")
            if isinstance(generated_files, dict):
                pipeline.context.generated_code = generated_files
                written_files = _write_generated_code(
                    pipeline.context.project_path,
                    generated_files,
                )
            else:
                written_files = []

            pipeline.updated_at = now
            pipeline.status = PipelineStatus.PENDING
            pipeline.logs.append(f"[{_timestamp()}] {output.summary}")
            if written_files:
                preview = "、".join(Path(path).name for path in written_files[:5])
                pipeline.logs.append(f"[{_timestamp()}] 生成代码已写入: {preview}")
            await self.state_store.save(pipeline)
        except Exception as error:
            coding_stage.status = StageStatus.FAILED
            coding_stage.completed_at = datetime.now()
            pipeline.status = PipelineStatus.FAILED
            pipeline.error = f"[coding] {error}"
            pipeline.logs.append(f"[{_timestamp()}] 代码生成失败: {error}")
            await self.state_store.save(pipeline)
            raise
