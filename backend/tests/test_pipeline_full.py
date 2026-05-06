"""
FlowState Pipeline 连通性测试

测试整个研发流水线：需求 → 方案 → 编码 → 测试 → 评审 → 交付
无需人类干预，全自动模式检验端到端链路。
"""

import asyncio
import sys
import os

# 确保 src 目录在 Python 路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine import DevFlowEngine
from src.agents import (
    RequirementAgent,
    SolutionAgent,
    CodeAgent,
    TestAgent,
    ReviewAgent,
    DeliveryAgent,
)
from src.models.pipeline import StageType


def print_separator(title: str):
    """打印分隔线"""
    width = 72
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


async def test_pipeline_connectivity():
    """测试 Pipeline 全链路连通性"""
    print("🚀  FlowState DevFlow Engine — Pipeline 连通性测试")
    print("=" * 72)

    # ========== 1. 初始化引擎 ==========
    print_separator("1. 初始化 FlowState Engine")

    engine = DevFlowEngine()
    engine.register_agent(StageType.REQUIREMENT, RequirementAgent())
    engine.register_agent(StageType.SOLUTION, SolutionAgent())
    engine.register_agent(StageType.CODING, CodeAgent())
    engine.register_agent(StageType.TESTING, TestAgent())
    engine.register_agent(StageType.REVIEW, ReviewAgent())
    engine.register_agent(StageType.DELIVERY, DeliveryAgent())

    print("  ✅  6 个 Agent 已注册")
    print("  📋  Agent 列表:")
    for stage, agent in engine.agents.items():
        print(f"       - {stage.value:25s} → {agent.__class__.__name__}")
    print()

    # ========== 2. 创建 Pipeline ==========
    print_separator("2. 创建 Pipeline")

    requirement = """
    我们需要构建一个轻量级的任务管理系统（Todo App），
    支持：
    1. 用户注册和登录
    2. 创建、查看、编辑、删除任务
    3. 任务分类（待办、进行中、已完成）
    4. 基础的数据持久化
    """

    pipeline = await engine.create_pipeline(requirement, title="Todo App MVP")
    print(f"  ✅  Pipeline 已创建")
    print(f"  📋  Pipeline ID: {pipeline.id}")
    print(f"  📋  标题: {pipeline.title}")
    print(f"  📋  阶段数: {len(pipeline.stages)}")
    for i, stage in enumerate(pipeline.stages):
        print(f"       Stage {i+1}: {stage.stage_type.value}")
    print()

    # ========== 3. 运行全自动流水线 ==========
    print_separator("3. 执行全自动流水线")

    try:
        pipeline = await engine.run_fully_auto(requirement)
    except Exception as e:
        print(f"\n  ❌ 流水线执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ========== 4. 验证流水线结果 ==========
    print_separator("4. 验证流水线输出")

    checks = []

    # 4.1 检查 Pipeline 状态
    status_ok = pipeline.status.value == "completed"
    checks.append(("Pipeline 状态为 completed", status_ok, pipeline.status.value))

    # 4.2 检查各阶段状态
    all_stages_completed = all(
        s.status.value == "completed" for s in pipeline.stages
    )
    checks.append(("所有阶段均已完成", all_stages_completed, ", ".join(s.status.value for s in pipeline.stages)))

    # 4.3 检查需求文档
    has_requirement = pipeline.context.requirement_doc is not None
    checks.append(("需求文档已生成", has_requirement, 
                   f"长度: {len(pipeline.context.requirement_doc or '')} 字符"))

    # 4.4 检查方案文档
    has_solution = pipeline.context.solution_doc is not None
    checks.append(("技术方案已生成", has_solution,
                   f"长度: {len(pipeline.context.solution_doc or '')} 字符"))

    # 4.5 检查生成的代码
    has_code = pipeline.context.generated_code is not None
    code_count = len(pipeline.context.generated_code or {})
    checks.append(("代码已生成", has_code and code_count > 0,
                   f"共 {code_count} 个文件"))

    # 4.6 检查测试报告
    has_test = pipeline.context.test_report is not None
    checks.append(("测试报告已生成", has_test,
                   f"长度: {len(pipeline.context.test_report or '')} 字符"))

    # 4.7 检查评审报告
    has_review = pipeline.context.review_report is not None
    checks.append(("评审报告已生成", has_review,
                   f"长度: {len(pipeline.context.review_report or '')} 字符"))

    # 4.8 检查交付结果
    has_delivery = pipeline.context.delivery_result is not None
    checks.append(("交付结果已生成", has_delivery,
                   f"长度: {len(pipeline.context.delivery_result or '')} 字符"))

    # 打印检查结果
    all_pass = True
    for name, passed, detail in checks:
        icon = "✅" if passed else "❌"
        print(f"  {icon}  {name}")
        print(f"       {detail}")
        if not passed:
            all_pass = False

    print()

    # ========== 5. 打印代码清单 ==========
    print_separator("5. 生成的代码文件清单")

    if pipeline.context.generated_code:
        files = pipeline.context.generated_code
        for i, (fname, content) in enumerate(files.items(), 1):
            lines = content.count("\n") + 1
            print(f"  {i:2d}. 📄 {fname:40s} ({lines} 行)")
    print()

    # ========== 6. 打印交付摘要 ==========
    print_separator("6. 交付摘要")

    if pipeline.context.delivery_result:
        print(f"  {pipeline.context.delivery_result[:200]}...")
    print()

    # ========== 7. 最终结果 ==========
    print("=" * 72)
    if all_pass:
        print("  🎉  全链路连通性测试通过！")
        print()
        print("  📊 流水线执行摘要:")
        print(f"       Pipeline ID: {pipeline.id}")
        for i, stage in enumerate(pipeline.stages):
            icon = "✅" if stage.status.value == "completed" else "❌"
            print(f"       {icon}  Stage {i+1}: {stage.stage_type.value:25s}  {stage.status.value}")
    else:
        print("  ⚠️  部分检查未通过，请查看上方详情")
    print("=" * 72)

    return all_pass


def main():
    """入口函数"""
    success = asyncio.run(test_pipeline_connectivity())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
