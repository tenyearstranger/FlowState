"""
FlowState 手动测试脚本：从 Stage4 开始执行

用途：
- 跳过 requirement / solution / coding
- 直接读取现有项目目录中的代码文件
- 只跑 testing -> review -> delivery

示例：
    python backend/tests/manual_stage4_to_6.py --project-path C:/path/to/project
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agents import DeliveryAgent, ReviewAgent, TestAgent
from src.agents.base_agent import AgentInput, AgentOutput
from src.engine import DevFlowEngine
from src.models.pipeline import (
    Pipeline,
    PipelineContext,
    PipelineStatus,
    StageNode,
    StageStatus,
    StageType,
)


DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
    ".pytest_cache",
    "__pycache__",
    "coverage",
}

DEFAULT_EXCLUDE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".woff",
    ".woff2",
    ".ttf",
    ".lock",
}

DEFAULT_EXCLUDE_RELATIVE_FILES = {
    "main/requirements.md",
    "main/solution.md",
    "main/test_report.md",
    "main/review_report.md",
    "main/delivery.md",
}


def print_separator(title: str) -> None:
    width = 72
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def approve_stage_for_manual_continue(pipeline: Pipeline, stage_index: int) -> None:
    now = datetime.now()
    stage = pipeline.stages[stage_index]
    stage.status = StageStatus.APPROVED
    stage.completed_at = stage.completed_at or now
    pipeline.status = PipelineStatus.RUNNING
    pipeline.updated_at = now
    pipeline.logs.append(
        f"[{now.strftime('%H:%M:%S')}] 手动测试自动审批通过: {stage.stage_type.value}"
    )


def build_pipeline(project_path: str, generated_code: dict[str, str]) -> Pipeline:
    now = datetime.now()
    return Pipeline(
        title=f"Stage4+ Test - {Path(project_path).name}",
        status=PipelineStatus.PENDING,
        context=PipelineContext(
            project_path=project_path,
            generated_code=generated_code,
        ),
        stages=[
            StageNode(
                stage_type=StageType.REQUIREMENT,
                status=StageStatus.COMPLETED,
                completed_at=now,
                agent_output={"skipped": True, "reason": "manual stage4 start"},
            ),
            StageNode(
                stage_type=StageType.SOLUTION,
                status=StageStatus.COMPLETED,
                completed_at=now,
                agent_output={"skipped": True, "reason": "manual stage4 start"},
            ),
            StageNode(
                stage_type=StageType.CODING,
                status=StageStatus.COMPLETED,
                completed_at=now,
                agent_output={
                    "skipped": True,
                    "reason": "manual stage4 start",
                    "files": list(generated_code.keys()),
                },
            ),
            StageNode(stage_type=StageType.TESTING),
            StageNode(stage_type=StageType.REVIEW),
            StageNode(stage_type=StageType.DELIVERY),
        ],
        created_at=now,
        updated_at=now,
        logs=[
            f"[{now.strftime('%H:%M:%S')}] 手动从 Stage4 启动",
            f"[{now.strftime('%H:%M:%S')}] 项目目录: {project_path}",
            f"[{now.strftime('%H:%M:%S')}] 已加载代码文件: {len(generated_code)}",
        ],
    )


def load_project_code(project_path: Path, max_file_size_kb: int) -> dict[str, str]:
    generated_code: dict[str, str] = {}
    max_bytes = max_file_size_kb * 1024

    for file_path in sorted(project_path.rglob("*")):
        if not file_path.is_file():
            continue

        relative_path = file_path.relative_to(project_path)
        normalized_relative_path = str(relative_path).replace("\\", "/")
        if any(part in DEFAULT_EXCLUDE_DIRS for part in relative_path.parts):
            continue
        if normalized_relative_path in DEFAULT_EXCLUDE_RELATIVE_FILES:
            continue
        if file_path.suffix.lower() in DEFAULT_EXCLUDE_SUFFIXES:
            continue
        if file_path.stat().st_size > max_bytes:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        generated_code[normalized_relative_path] = content

    return generated_code


async def run_single_stage(
    engine: DevFlowEngine,
    pipeline: Pipeline,
    stage_index: int,
) -> AgentOutput:
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
    stage.status = (
        StageStatus.WAITING_HUMAN if output.needs_human_review else StageStatus.COMPLETED
    )
    engine._apply_stage_usage(stage, output)
    engine._update_context(pipeline, stage.stage_type, output.result, output)
    pipeline.updated_at = datetime.now()
    pipeline.logs.append(
        f"[{pipeline.updated_at.strftime('%H:%M:%S')}] {stage.stage_type.value}: {output.summary}"
    )

    if stage.status == StageStatus.WAITING_HUMAN:
        pipeline.status = PipelineStatus.WAITING_HUMAN
    return output


async def main() -> int:
    parser = argparse.ArgumentParser(description="跳过 stage1-3，直接测试 stage4-6")
    parser.add_argument("--project-path", required=True, help="已有代码的项目目录")
    parser.add_argument(
        "--max-file-size-kb",
        type=int,
        default=128,
        help="单文件最大读取体积，超过则跳过，默认 128KB",
    )
    parser.add_argument(
        "--auto-approve-testing",
        action="store_true",
        help="若 testing 阶段进入待审批，则自动批准后继续",
    )
    parser.add_argument(
        "--auto-approve-review",
        action="store_true",
        help="若 review 阶段进入待审批，则自动批准后继续到 delivery",
    )
    args = parser.parse_args()

    project_path = Path(args.project_path).expanduser().resolve()
    if not project_path.exists() or not project_path.is_dir():
        print(f"❌ 项目目录不存在或不是文件夹: {project_path}")
        return 1

    print("🚀 FlowState 手动测试：Stage4 -> Stage6")
    print(f"📂 项目目录: {project_path}")

    print_separator("1. 加载现有代码")
    generated_code = load_project_code(project_path, args.max_file_size_kb)
    if not generated_code:
        print("❌ 没有读取到可用代码文件。")
        print("   请检查目录路径，或调整 --max-file-size-kb。")
        return 1

    print(f"  ✅ 已加载 {len(generated_code)} 个文件")
    for index, path in enumerate(list(generated_code.keys())[:15], start=1):
        print(f"  {index:2d}. {path}")
    if len(generated_code) > 15:
        print(f"  ... 还有 {len(generated_code) - 15} 个文件")

    print_separator("2. 初始化引擎")
    engine = DevFlowEngine()
    engine.register_agent(StageType.TESTING, TestAgent())
    engine.register_agent(StageType.REVIEW, ReviewAgent())
    engine.register_agent(StageType.DELIVERY, DeliveryAgent())
    print("  ✅ 已注册 Test / Review / Delivery 三个 Agent")

    pipeline = build_pipeline(str(project_path), generated_code)

    print_separator("3. Stage4 - Testing")
    try:
        testing_output = await run_single_stage(engine, pipeline, 3)
        print(f"  ✅ {testing_output.summary}")
        print(f"  当前状态: {pipeline.stages[3].status.value}")
    except Exception as error:
        print(f"  ❌ Stage4 失败: {error}")
        return 1

    if pipeline.stages[3].status == StageStatus.WAITING_HUMAN:
        if args.auto_approve_testing:
            print("  ⚠️ 测试阶段进入待审批，已按参数自动批准并继续。")
            approve_stage_for_manual_continue(pipeline, 3)
        else:
            print("  ⚠️ 测试阶段要求人工确认，后续 Stage5/6 已停止。")
            if pipeline.context.test_report:
                print(pipeline.context.test_report[:800])
            return 0

    print_separator("4. Stage5 - Review")
    try:
        review_output = await run_single_stage(engine, pipeline, 4)
        print(f"  ✅ {review_output.summary}")
        print(f"  当前状态: {pipeline.stages[4].status.value}")
    except Exception as error:
        print(f"  ❌ Stage5 失败: {error}")
        return 1

    if pipeline.stages[4].status == StageStatus.WAITING_HUMAN:
        if args.auto_approve_review:
            print("  ⚠️ 评审阶段进入待审批，已按参数自动批准并继续。")
            approve_stage_for_manual_continue(pipeline, 4)
        else:
            print("  ⚠️ 评审阶段要求人工确认，Stage6 已停止。")
            if pipeline.context.review_report:
                print(pipeline.context.review_report[:800])
            return 0

    print_separator("5. Stage6 - Delivery")
    try:
        delivery_output = await run_single_stage(engine, pipeline, 5)
        print(f"  ✅ {delivery_output.summary}")
        print(f"  当前状态: {pipeline.stages[5].status.value}")
    except Exception as error:
        print(f"  ❌ Stage6 失败: {error}")
        return 1

    print_separator("6. 输出摘要")
    print(f"  测试报告: {'已生成' if pipeline.context.test_report else '未生成'}")
    print(f"  评审报告: {'已生成' if pipeline.context.review_report else '未生成'}")
    print(f"  交付结果: {'已生成' if pipeline.context.delivery_result else '未生成'}")
    print(f"  最终 Pipeline 状态: {pipeline.status.value}")

    if pipeline.context.delivery_result:
        print()
        print(pipeline.context.delivery_result[:1200])

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
