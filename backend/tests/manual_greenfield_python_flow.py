"""
FlowState 手动测试脚本：绿地 Python 项目闭环验证

用途：
- 在空目录里从 stage1 开始执行
- 强制需求/方案收敛到 Python + FastAPI + pytest
- 自动推进 requirement -> solution -> coding -> testing
- testing 失败时回退到 coding，并把测试结果作为修复反馈

示例：
    python backend/tests/manual_greenfield_python_flow.py ^
      --project-path C:/tmp/fs-python-demo ^
      --requirement "实现一个待办事项 API，支持增删改查"
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agents import (
    CodeAgent,
    DeliveryAgent,
    RequirementAgent,
    ReviewAgent,
    SolutionAgent,
    TestAgent,
)
from src.agents.base_agent import AgentInput, AgentOutput
from src.engine import DevFlowEngine
from src.models.pipeline import Pipeline, PipelineContext, PipelineStatus, StageNode, StageStatus, StageType


def print_separator(title: str) -> None:
    width = 72
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def build_requirement(raw_requirement: str) -> str:
    constraints = """

技术约束：
- 这是一个全新的 Python 项目，不要生成 Node.js / Electron / Vue / React / TypeScript 工程
- 后端框架固定使用 FastAPI
- 测试框架固定使用 pytest
- 依赖文件使用 requirements.txt
- 代码应可直接通过 pytest 执行测试
- 优先生成简洁、可运行、可测试的后端项目
""".strip()
    return f"{raw_requirement.strip()}\n\n{constraints}"


def build_project_summary(project_path: Path) -> str:
    files = [item.name for item in sorted(project_path.iterdir(), key=lambda p: p.name.lower()) if item_exists(item)]
    preview = "、".join(files[:8]) if files else "当前为空目录"
    return (
        "## 项目目录扫描\n\n"
        f"- 根目录：{project_path}\n"
        f"- 顶层文件预览：{preview}\n"
        "- 目标：在该空目录中生成全新的 Python/FastAPI 项目"
    )


def item_exists(path: Path) -> bool:
    return path.exists()


def build_pipeline(project_path: Path, requirement: str) -> Pipeline:
    now = datetime.now()
    return Pipeline(
        title=f"Greenfield Python - {project_path.name}",
        status=PipelineStatus.PENDING,
        context=PipelineContext(
            project_path=str(project_path),
            project_summary=build_project_summary(project_path),
            requirement_raw=build_requirement(requirement),
        ),
        stages=[
            StageNode(stage_type=StageType.REQUIREMENT),
            StageNode(stage_type=StageType.SOLUTION),
            StageNode(stage_type=StageType.CODING),
            StageNode(stage_type=StageType.TESTING),
            StageNode(stage_type=StageType.REVIEW),
            StageNode(stage_type=StageType.DELIVERY),
        ],
        created_at=now,
        updated_at=now,
        logs=[
            f"[{now.strftime('%H:%M:%S')}] 手动启动绿地 Python 闭环验证",
            f"[{now.strftime('%H:%M:%S')}] 项目目录: {project_path}",
        ],
    )


def write_generated_code(project_path: Path, files: dict[str, str]) -> list[Path]:
    written_files: list[Path] = []
    for relative_path, content in files.items():
        normalized = relative_path.strip().lstrip("/").replace("\\", "/")
        if not normalized or ".." in Path(normalized).parts:
            continue
        target_path = project_path / normalized
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        written_files.append(target_path)
    return written_files


def reset_stage(stage, *, keep_feedback: bool = False) -> None:
    stage.status = StageStatus.PENDING
    stage.agent_output = None
    stage.prompt_tokens = None
    stage.completion_tokens = None
    stage.total_tokens = None
    stage.model_name = None
    stage.human_approval = None
    stage.started_at = None
    stage.completed_at = None
    if not keep_feedback:
        stage.human_feedback = None


def build_testing_feedback(test_stage) -> str:
    report = ""
    errors: list[str] = []
    if isinstance(test_stage.agent_output, dict):
        report = str(test_stage.agent_output.get("report") or "").strip()
        test_results = test_stage.agent_output.get("test_results")
        if isinstance(test_results, dict):
            raw_errors = test_results.get("errors") or []
            errors = [str(item).strip() for item in raw_errors if str(item).strip()]

    sections = [
        "上一轮测试未通过，请修复代码并重新生成相关文件。",
        "请优先修复导入错误、缺失依赖、接口签名不一致、测试框架不兼容等问题。",
    ]
    if errors:
        sections.extend(["", "测试错误：", *[f"- {line}" for line in errors[:12]]])
    if report:
        sections.extend(["", "测试报告：", report[:4000]])
    return "\n".join(sections).strip()


def approve_stage_for_manual_continue(pipeline: Pipeline, stage_index: int) -> None:
    now = datetime.now()
    stage = pipeline.stages[stage_index]
    stage.status = StageStatus.APPROVED
    stage.completed_at = stage.completed_at or now
    pipeline.status = PipelineStatus.RUNNING
    pipeline.updated_at = now
    pipeline.logs.append(
        f"[{now.strftime('%H:%M:%S')}] 手动自动审批通过: {stage.stage_type.value}"
    )


async def run_single_stage(engine: DevFlowEngine, pipeline: Pipeline, stage_index: int) -> AgentOutput:
    stage = pipeline.stages[stage_index]
    agent = engine.agents.get(stage.stage_type)
    if not agent:
        raise ValueError(f"未注册 Agent: {stage.stage_type.value}")

    stage.status = StageStatus.RUNNING
    stage.started_at = datetime.now()
    pipeline.status = PipelineStatus.RUNNING
    pipeline.updated_at = datetime.now()

    input_data = AgentInput(
        task_description=f"执行阶段: {stage.stage_type.value}",
        context=pipeline.context.model_dump(),
        human_feedback=stage.human_feedback,
    )
    output = await agent.execute(input_data)

    stage.agent_output = output.result
    stage.completed_at = datetime.now()
    stage.status = StageStatus.WAITING_HUMAN if output.needs_human_review else StageStatus.COMPLETED
    engine._apply_stage_usage(stage, output)
    engine._update_context(pipeline, stage.stage_type, output.result, output)
    pipeline.updated_at = datetime.now()
    pipeline.logs.append(
        f"[{pipeline.updated_at.strftime('%H:%M:%S')}] {stage.stage_type.value}: {output.summary}"
    )
    if stage.status == StageStatus.WAITING_HUMAN:
        pipeline.status = PipelineStatus.WAITING_HUMAN
    return output


def reset_for_retry_from_coding(pipeline: Pipeline, feedback: str) -> None:
    coding_stage = pipeline.stages[2]
    coding_stage.retry_count += 1
    coding_stage.human_feedback = feedback
    reset_stage(coding_stage, keep_feedback=True)
    for stage in pipeline.stages[3:]:
        reset_stage(stage)
    pipeline.context.test_report = None
    pipeline.context.review_report = None
    pipeline.context.delivery_result = None
    pipeline.status = PipelineStatus.PENDING
    pipeline.updated_at = datetime.now()


async def main() -> int:
    parser = argparse.ArgumentParser(description="在空目录中执行绿地 Python/FastAPI/pytest 闭环验证")
    parser.add_argument("--project-path", required=True, help="目标空目录")
    parser.add_argument("--requirement", required=True, help="业务需求描述")
    parser.add_argument("--max-cycles", type=int, default=2, help="coding->testing 最大轮数，默认 2")
    parser.add_argument("--auto-approve-review", action="store_true", help="review 阶段待审批时自动通过")
    parser.add_argument("--auto-approve-delivery", action="store_true", help="delivery 阶段待审批时自动通过")
    args = parser.parse_args()

    project_path = Path(args.project_path).expanduser().resolve()
    project_path.mkdir(parents=True, exist_ok=True)

    pipeline = build_pipeline(project_path, args.requirement)

    print("🚀 FlowState 绿地 Python 闭环验证")
    print(f"📂 项目目录: {project_path}")
    print(f"📝 业务需求: {args.requirement}")

    print_separator("1. 初始化引擎")
    engine = DevFlowEngine()
    engine.register_agent(StageType.REQUIREMENT, RequirementAgent())
    engine.register_agent(StageType.SOLUTION, SolutionAgent())
    engine.register_agent(StageType.CODING, CodeAgent())
    engine.register_agent(StageType.TESTING, TestAgent())
    engine.register_agent(StageType.REVIEW, ReviewAgent())
    engine.register_agent(StageType.DELIVERY, DeliveryAgent())
    print("  ✅ 已注册 6 个阶段 Agent")

    print_separator("2. Stage1 - Requirement")
    try:
        requirement_output = await run_single_stage(engine, pipeline, 0)
        print(f"  ✅ {requirement_output.summary}")
    except Exception as error:
        print(f"  ❌ Stage1 失败: {error}")
        return 1

    if pipeline.stages[0].status == StageStatus.WAITING_HUMAN:
        approve_stage_for_manual_continue(pipeline, 0)
        print("  ⚠️ 已自动通过 requirement 检查点")

    print_separator("3. Stage2 - Solution")
    try:
        solution_output = await run_single_stage(engine, pipeline, 1)
        print(f"  ✅ {solution_output.summary}")
    except Exception as error:
        print(f"  ❌ Stage2 失败: {error}")
        return 1

    if pipeline.stages[1].status == StageStatus.WAITING_HUMAN:
        approve_stage_for_manual_continue(pipeline, 1)
        print("  ⚠️ 已自动通过 solution 检查点")

    for cycle in range(1, args.max_cycles + 1):
        print_separator(f"4.{cycle} Stage3 - Coding")
        try:
            coding_output = await run_single_stage(engine, pipeline, 2)
            print(f"  ✅ {coding_output.summary}")
        except Exception as error:
            print(f"  ❌ Stage3 失败: {error}")
            return 1

        generated_code = pipeline.context.generated_code or {}
        if not generated_code:
            print("  ❌ Stage3 未生成代码文件")
            return 1

        written_files = write_generated_code(project_path, generated_code)
        print(f"  ✅ 已写入 {len(written_files)} 个代码文件")

        print_separator(f"5.{cycle} Stage4 - Testing")
        try:
            testing_output = await run_single_stage(engine, pipeline, 3)
            print(f"  ✅ {testing_output.summary}")
            print(f"  当前状态: {pipeline.stages[3].status.value}")
        except Exception as error:
            print(f"  ❌ Stage4 失败: {error}")
            return 1

        if pipeline.stages[3].status == StageStatus.WAITING_HUMAN:
            if cycle >= args.max_cycles:
                print("  ⚠️ 测试阶段仍未通过，已达到最大重试轮数。")
                if pipeline.context.test_report:
                    print(pipeline.context.test_report[:1200])
                return 0

            print("  ⚠️ 测试阶段未通过，准备回退到 Stage3。")
            feedback = build_testing_feedback(pipeline.stages[3])
            reset_for_retry_from_coding(pipeline, feedback)
            continue

        break
    else:
        return 0

    print_separator("6. Stage5 - Review")
    try:
        review_output = await run_single_stage(engine, pipeline, 4)
        print(f"  ✅ {review_output.summary}")
        print(f"  当前状态: {pipeline.stages[4].status.value}")
    except Exception as error:
        print(f"  ❌ Stage5 失败: {error}")
        return 1

    if pipeline.stages[4].status == StageStatus.WAITING_HUMAN:
        if args.auto_approve_review:
            print("  ⚠️ 已自动通过 review 检查点")
            approve_stage_for_manual_continue(pipeline, 4)
        else:
            print("  ⚠️ review 阶段等待人工确认")
            if pipeline.context.review_report:
                print(pipeline.context.review_report[:1200])
            return 0

    print_separator("7. Stage6 - Delivery")
    try:
        delivery_output = await run_single_stage(engine, pipeline, 5)
        print(f"  ✅ {delivery_output.summary}")
        print(f"  当前状态: {pipeline.stages[5].status.value}")
    except Exception as error:
        print(f"  ❌ Stage6 失败: {error}")
        return 1

    if pipeline.stages[5].status == StageStatus.WAITING_HUMAN:
        if args.auto_approve_delivery:
            print("  ⚠️ 已自动通过 delivery 检查点")
            approve_stage_for_manual_continue(pipeline, 5)
        else:
            print("  ⚠️ delivery 阶段等待人工确认")
            if pipeline.context.delivery_result:
                print(pipeline.context.delivery_result[:1200])
            return 0

    print_separator("8. 输出摘要")
    print(f"  需求文档: {'已生成' if pipeline.context.requirement_doc else '未生成'}")
    print(f"  技术方案: {'已生成' if pipeline.context.solution_doc else '未生成'}")
    print(f"  测试报告: {'已生成' if pipeline.context.test_report else '未生成'}")
    print(f"  评审报告: {'已生成' if pipeline.context.review_report else '未生成'}")
    print(f"  交付结果: {'已生成' if pipeline.context.delivery_result else '未生成'}")
    print(f"  最终 Pipeline 状态: {pipeline.status.value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
