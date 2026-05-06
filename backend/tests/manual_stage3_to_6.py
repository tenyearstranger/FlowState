"""
FlowState 手动测试脚本：从 Stage3 开始执行并验证 stage4 失败回退闭环

用途：
- 读取已有 pipeline JSON，复用其中的 requirement_doc / solution_structured
- 从 coding -> testing 开始执行
- testing 未通过时，自动把失败摘要反馈回 coding，再次生成代码
- 可选继续执行 review / delivery

示例：
    python backend/tests/manual_stage3_to_6.py ^
      --project-path C:/path/to/project ^
      --pipeline-json C:/mfk/FlowState/backend/flow_state/pipe_xxx.json
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agents import CodeAgent, DeliveryAgent, ReviewAgent, TestAgent
from src.agents.base_agent import AgentInput, AgentOutput
from src.engine import DevFlowEngine
from src.models.pipeline import Pipeline, PipelineStatus, StageStatus, StageType


def print_separator(title: str) -> None:
    width = 72
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def load_pipeline_from_json(pipeline_json: Path) -> Pipeline:
    return Pipeline.model_validate_json(pipeline_json.read_text(encoding="utf-8"))


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


def prepare_pipeline_for_stage3(pipeline: Pipeline, project_path: Path) -> None:
    pipeline.context.project_path = str(project_path)
    pipeline.status = PipelineStatus.PENDING
    pipeline.error = None
    pipeline.context.test_report = None
    pipeline.context.review_report = None
    pipeline.context.delivery_result = None

    for stage in pipeline.stages[2:]:
        reset_stage(stage)

    pipeline.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 手动从 Stage3 启动闭环验证")
    pipeline.updated_at = datetime.now()


def build_testing_feedback(test_stage) -> str:
    report = ""
    errors: list[str] = []
    if isinstance(test_stage.agent_output, dict):
        report = str(test_stage.agent_output.get("report") or "").strip()
        test_results = test_stage.agent_output.get("test_results")
        if isinstance(test_results, dict):
            raw_errors = test_results.get("errors") or []
            errors = [str(item).strip() for item in raw_errors if str(item).strip()]

    sections = ["上一轮测试失败，请修复代码并重新生成相关文件。"]
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
        f"[{now.strftime('%H:%M:%S')}] 手动测试自动审批通过: {stage.stage_type.value}"
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


def validate_pipeline_context(pipeline: Pipeline) -> None:
    if not pipeline.context.requirement_doc:
        raise ValueError("pipeline context 缺少 requirement_doc，无法从 stage3 开始")
    if not pipeline.context.solution_structured:
        raise ValueError("pipeline context 缺少 solution_structured，无法从 stage3 开始")
    file_plan = pipeline.context.solution_structured.get("file_plan")
    if not isinstance(file_plan, list) or not file_plan:
        raise ValueError("solution_structured.file_plan 为空，CodeAgent 无法执行")


async def main() -> int:
    parser = argparse.ArgumentParser(description="从 stage3 开始执行并验证测试失败回退闭环")
    parser.add_argument("--project-path", required=True, help="目标项目目录")
    parser.add_argument("--pipeline-json", required=True, help="已有 pipeline JSON 文件路径")
    parser.add_argument("--max-cycles", type=int, default=2, help="coding->testing 最大重试轮数，默认 2")
    parser.add_argument("--auto-approve-review", action="store_true", help="review 阶段待审批时自动通过")
    args = parser.parse_args()

    project_path = Path(args.project_path).expanduser().resolve()
    pipeline_json = Path(args.pipeline_json).expanduser().resolve()

    if not project_path.exists() or not project_path.is_dir():
        print(f"❌ 项目目录不存在或不是文件夹: {project_path}")
        return 1
    if not pipeline_json.exists() or not pipeline_json.is_file():
        print(f"❌ pipeline JSON 不存在: {pipeline_json}")
        return 1

    pipeline = load_pipeline_from_json(pipeline_json)
    validate_pipeline_context(pipeline)
    prepare_pipeline_for_stage3(pipeline, project_path)

    print("🚀 FlowState 手动测试：Stage3 -> Stage6 闭环验证")
    print(f"📂 项目目录: {project_path}")
    print(f"🧾 Pipeline: {pipeline_json.name}")

    print_separator("1. 初始化引擎")
    engine = DevFlowEngine()
    engine.register_agent(StageType.CODING, CodeAgent())
    engine.register_agent(StageType.TESTING, TestAgent())
    engine.register_agent(StageType.REVIEW, ReviewAgent())
    engine.register_agent(StageType.DELIVERY, DeliveryAgent())
    print("  ✅ 已注册 Code / Test / Review / Delivery 四个 Agent")

    for cycle in range(1, args.max_cycles + 1):
        print_separator(f"2.{cycle} Stage3 - Coding")
        try:
            coding_output = await run_single_stage(engine, pipeline, 2)
            print(f"  ✅ {coding_output.summary}")
        except Exception as error:
            print(f"  ❌ Stage3 失败: {error}")
            return 1

        generated_code = pipeline.context.generated_code or {}
        if generated_code:
            written_files = write_generated_code(project_path, generated_code)
            print(f"  ✅ 已写入 {len(written_files)} 个代码文件")
        else:
            print("  ❌ Stage3 未生成代码文件")
            return 1

        print_separator(f"3.{cycle} Stage4 - Testing")
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

            print("  ⚠️ 测试阶段未通过，准备回退到 Stage3 重新生成代码。")
            feedback = build_testing_feedback(pipeline.stages[3])
            reset_for_retry_from_coding(pipeline, feedback)
            continue

        break
    else:
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
                print(pipeline.context.review_report[:1200])
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
