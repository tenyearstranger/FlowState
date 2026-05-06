"""
FlowState Pipeline 测试：stage1 → stage2 → stage3

需求：自律 App
项目路径：/Users/yuki/code/demo
目标：跑完代码生成阶段，把多文件代码写入本地磁盘
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agents import CodeAgent, RequirementAgent, SolutionAgent
from src.agents.base_agent import AgentInput, AgentOutput
from src.engine import DevFlowEngine
from src.models.pipeline import Pipeline, PipelineContext, StageType, StageStatus


PROJECT_PATH = "/Users/yuki/code/demo"
REQUIREMENT = """
我需要开发一个自律管理 App，帮助用户养成好习惯、管理每日任务。

核心功能：
1. 习惯打卡：用户可以创建每日习惯（如早起、运动、阅读），每天打卡记录
2. 待办任务：支持创建、编辑、删除、完成待办事项，支持优先级排序
3. 专注计时：番茄钟模式，支持自定义专注/休息时长，记录专注时间
4. 数据统计：展示每日/每周/每月的打卡率、任务完成率、专注时长统计图表
5. 激励系统：连续打卡天数、成就徽章、每日金句

技术要求：
- 前端使用 React + TypeScript + Tailwind CSS
- 后端使用 Python FastAPI
- 数据库使用 SQLite（本地轻量）
- 项目结构清晰，前后端分离
"""


def print_separator(title: str):
    width = 72
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def write_generated_code(project_path: str, files: dict[str, str]) -> list[str]:
    """把生成的代码写入项目目录"""
    base_dir = Path(project_path)
    written: list[str] = []
    for filepath, content in files.items():
        cleaned = filepath.strip().lstrip("/").replace("\\", "/")
        target = base_dir / cleaned
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(str(target))
    return written


async def run_stage(
    engine: DevFlowEngine,
    pipeline: Pipeline,
    stage_index: int,
) -> AgentOutput:
    """手动执行单个阶段并更新上下文"""
    stage = pipeline.stages[stage_index]
    stage_type = stage.stage_type
    agent = engine.agents.get(stage_type)
    if not agent:
        raise ValueError(f"未注册 Agent: {stage_type.value}")

    stage.status = StageStatus.RUNNING
    stage.started_at = datetime.now()

    input_data = AgentInput(
        task_description=f"执行阶段: {stage_type.value}",
        context=pipeline.context.model_dump(),
    )

    output = await agent.execute(input_data)

    stage.agent_output = output.result
    stage.completed_at = datetime.now()
    stage.status = StageStatus.COMPLETED

    engine._update_context(pipeline, stage_type, output.result, output)
    pipeline.updated_at = datetime.now()

    return output


async def main():
    print("🚀  FlowState Pipeline 测试：自律 App（stage1 → stage2 → stage3）")
    print(f"📂  目标项目路径：{PROJECT_PATH}")
    print("=" * 72)

    Path(PROJECT_PATH).mkdir(parents=True, exist_ok=True)

    # 初始化引擎
    print_separator("1. 初始化引擎")
    engine = DevFlowEngine()
    engine.register_agent(StageType.REQUIREMENT, RequirementAgent())
    engine.register_agent(StageType.SOLUTION, SolutionAgent())
    engine.register_agent(StageType.CODING, CodeAgent())
    print("  ✅ 3 个 Agent 已注册（Requirement / Solution / Code）")

    # 创建 Pipeline
    print_separator("2. 创建 Pipeline")
    pipeline = await engine.create_pipeline(
        requirement=REQUIREMENT,
        title="自律管理 App",
    )
    pipeline.context.project_path = PROJECT_PATH
    print(f"  ✅ Pipeline 已创建: {pipeline.id}")
    print(f"  📋 标题: {pipeline.title}")

    # Stage 1：需求分析
    print_separator("3. Stage 1 — 需求分析")
    print("  ⏳ RequirementsAgent 正在分析需求...")
    try:
        output1 = await run_stage(engine, pipeline, 0)
        print(f"  ✅ {output1.summary}")
        if pipeline.context.requirement_doc:
            doc_path = Path(PROJECT_PATH) / "main" / "requirements.md"
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            doc_path.write_text(pipeline.context.requirement_doc, encoding="utf-8")
            print(f"  📄 需求文档已写入: {doc_path}")
    except Exception as e:
        print(f"  ❌ 需求分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Stage 2：方案设计
    print_separator("4. Stage 2 — 方案设计")
    print("  ⏳ SolutionAgent 正在设计技术方案...")
    try:
        output2 = await run_stage(engine, pipeline, 1)
        print(f"  ✅ {output2.summary}")
        if pipeline.context.solution_doc:
            doc_path = Path(PROJECT_PATH) / "main" / "solution.md"
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            doc_path.write_text(pipeline.context.solution_doc, encoding="utf-8")
            print(f"  📄 方案文档已写入: {doc_path}")
        if pipeline.context.solution_structured:
            file_plan = pipeline.context.solution_structured.get("file_plan", [])
            print(f"  📋 文件计划: {len(file_plan)} 个文件")
            for f in file_plan[:10]:
                mark = "✓" if f.get("must_generate") else "○"
                print(f"     {mark} {f['path']}  ({f.get('purpose', '')})")
            if len(file_plan) > 10:
                print(f"     ... 还有 {len(file_plan) - 10} 个文件")
        else:
            print("  ⚠️  solution_structured 为空，stage3 可能失败！")
    except Exception as e:
        print(f"  ❌ 方案设计失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Stage 3：代码生成
    print_separator("5. Stage 3 — 代码生成")
    print("  ⏳ CodeAgent 正在生成代码（可能需要较长时间）...")
    try:
        output3 = await run_stage(engine, pipeline, 2)
        print(f"  ✅ {output3.summary}")
    except Exception as e:
        print(f"  ❌ 代码生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 写入生成的代码到磁盘
    print_separator("6. 写入代码到磁盘")
    generated_code = pipeline.context.generated_code
    if not generated_code:
        print("  ❌ 没有生成任何代码文件！")
        return False

    written_files = write_generated_code(PROJECT_PATH, generated_code)
    print(f"  ✅ 共写入 {len(written_files)} 个文件到 {PROJECT_PATH}")
    for i, fpath in enumerate(written_files, 1):
        rel = os.path.relpath(fpath, PROJECT_PATH)
        lines = Path(fpath).read_text(encoding="utf-8").count("\n") + 1
        print(f"  {i:3d}. 📄 {rel:50s} ({lines} 行)")

    # 保存 pipeline 状态
    await engine.state_store.save(pipeline)

    # 最终总结
    print_separator("7. 测试总结")
    print(f"  Pipeline ID: {pipeline.id}")
    print(f"  项目路径:    {PROJECT_PATH}")
    print(f"  需求文档:    {len(pipeline.context.requirement_doc or '')} 字符")
    print(f"  方案文档:    {len(pipeline.context.solution_doc or '')} 字符")
    print(f"  生成代码:    {len(generated_code)} 个文件")
    print()
    print("  🎉 Stage1 → Stage2 → Stage3 全部通过！")
    print("=" * 72)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
