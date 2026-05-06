"""
模拟 Stage 1~4 完整流水线，不需要启动 FastAPI server。
用法：python simulate_pipeline.py
"""
from __future__ import annotations
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.api.service import PipelineService
from src.models.pipeline import StageStatus


REQUIREMENT = "请生成一个自律app，目录是/Users/yuki/code/demo3"
PROJECT_PATH = "/Users/yuki/code/demo3"
TITLE = "自律App"

# Stage 名称映射
STAGE_NAMES = ["需求分析", "技术方案", "代码生成", "测试验证", "代码评审", "交付打包"]


def _sep(label: str):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print('='*60)


def _print_stage(stage, idx: int):
    _sep(f"Stage {idx+1}: {STAGE_NAMES[idx]} — {stage.status.value}")
    if stage.agent_output:
        out = stage.agent_output
        # 打印关键字段
        for key in ("summary", "document", "report", "pass_rate", "structure", "score"):
            if key in out:
                val = out[key]
                if isinstance(val, list):
                    print(f"[{key}] {val[:5]}")  # cap list display
                elif isinstance(val, str):
                    print(f"[{key}] {val[:400]}")
                else:
                    print(f"[{key}] {val}")
        if "files" in out:
            files = out["files"]
            print(f"[files] {list(files.keys())}")
        if "test_files" in out:
            tf = out["test_files"]
            print(f"[test_files] {list(tf.keys())}")
    if stage.total_tokens:
        print(f"[tokens] prompt={stage.prompt_tokens} completion={stage.completion_tokens} total={stage.total_tokens}")
    if stage.model_name:
        print(f"[model] {stage.model_name}")


async def main():
    service = PipelineService()

    _sep("创建 Pipeline")
    print(f"需求: {REQUIREMENT}")
    print(f"项目目录: {PROJECT_PATH}")

    pipeline = await service.create_pipeline(
        title=TITLE,
        requirement=REQUIREMENT,
        project_path=PROJECT_PATH,
        start_immediately=False,
    )
    print(f"Pipeline ID: {pipeline.id}")

    # ── Stage 1: 需求分析 ──────────────────────────────────────
    _sep("运行 Stage 1: 需求分析")
    await service._run_requirement_analysis(pipeline)
    _print_stage(pipeline.stages[0], 0)

    if pipeline.stages[0].status == StageStatus.FAILED:
        print("Stage 1 失败，终止")
        return

    # ── Stage 2: 技术方案 ──────────────────────────────────────
    _sep("运行 Stage 2: 技术方案设计")
    await service._run_solution_design(pipeline)
    _print_stage(pipeline.stages[1], 1)

    if pipeline.stages[1].status == StageStatus.FAILED:
        print("Stage 2 失败，终止")
        return

    # ── Stage 3: 代码生成 ──────────────────────────────────────
    _sep("运行 Stage 3: 代码生成")
    await service._run_code_generation(pipeline)
    _print_stage(pipeline.stages[2], 2)

    if pipeline.stages[2].status == StageStatus.FAILED:
        print("Stage 3 失败，终止")
        return

    # ── Stage 4: 测试验证 ──────────────────────────────────────
    _sep("运行 Stage 4: 测试验证")
    await service._run_testing(pipeline)
    _print_stage(pipeline.stages[3], 3)

    _sep("流水线日志（最后20条）")
    for log in pipeline.logs[-20:]:
        print(log)

    _sep("完成")
    print(f"最终状态: {pipeline.status.value}")


if __name__ == "__main__":
    asyncio.run(main())
