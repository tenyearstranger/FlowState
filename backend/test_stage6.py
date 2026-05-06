"""
Stage 6 (交付集成) 测试脚本
===================================================
模拟 Stage 1-5 已完成（注入假数据），直接测试 Stage 6 交付逻辑：
  - DeliveryAgent LLM 调用
  - 生成 PR 标题/描述/commit message/changelog/deployment_notes
  - 写入 delivery.md / pr.md
  - 生成 gh pr create 命令
  - 进入 WAITING_HUMAN 等待人工审批

用法:
  cd backend
  python test_stage6.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from src.api.service import PipelineService
from src.models.pipeline import (
    ApproveAction,
    GitContext,
    GitMode,
    Pipeline,
    PipelineContext,
    PipelineStatus,
    StageCommit,
    StageNode,
    StageStatus,
    StageType,
)

# ──────────────────────────────────────────────────────────
# 假数据（时间管理 CLI App）
# ──────────────────────────────────────────────────────────

PROJECT_PATH = "/tmp/flowstate-test-stage6"

REQUIREMENT_DOC = """
## 需求文档：时间管理 CLI App
帮助用户通过命令行管理每日任务列表，支持增删查改与优先级排序。
核心需求：添加/列出/完成/删除任务，JSON 文件持久化。
""".strip()

SOLUTION_DOC = """
## 技术方案：时间管理 CLI App
- 语言: Python 3.11 / CLI: argparse / 存储: JSON / 测试: pytest
- 文件: models.py / storage.py / task_manager.py / main.py
""".strip()

GENERATED_CODE = {
    "models.py": "from dataclasses import dataclass\n@dataclass\nclass Task:\n    id: str\n    title: str\n    done: bool = False\n",
    "storage.py": "import json\ndef load(path): return json.loads(open(path).read()) if open(path,'a') else []\n",
    "task_manager.py": "from models import Task\nfrom storage import load\ndef add_task(title): pass\n",
    "main.py": "import argparse\ndef main(): pass\nif __name__ == '__main__': main()\n",
}

TEST_REPORT = """
## 测试报告

**测试框架:** pytest
**测试文件:** tests/test_task_manager.py
**通过/总数:** 8/8 ✅

### 测试摘要
- `test_add_task` ✅
- `test_list_tasks` ✅
- `test_complete_task` ✅
- `test_delete_task` ✅
- `test_priority_sort` ✅
- `test_persistence` ✅
- `test_empty_list` ✅
- `test_invalid_id` ✅

所有测试通过，代码质量符合预期。
""".strip()

REVIEW_REPORT = """
## 代码评审报告

**评审得分:** 82/100
**评审结论:** 代码整体质量良好，可以合并。

### 优点
- 代码结构清晰，模块职责明确
- 测试覆盖率高，边界条件处理完整

### 待改进
- storage.py 中文件读写缺少异常处理
- task_manager.py 缺少类型注解

### 建议
建议在合并前补充 storage.py 的异常处理逻辑。
""".strip()

CODE_DIFF = """
diff --git a/models.py b/models.py
new file mode 100644
--- /dev/null
+++ b/models.py
@@ -0,0 +1,5 @@
+from dataclasses import dataclass
+@dataclass
+class Task:
+    id: str
+    title: str
+    done: bool = False

diff --git a/task_manager.py b/task_manager.py
new file mode 100644
--- /dev/null
+++ b/task_manager.py
@@ -0,0 +1,3 @@
+from models import Task
+from storage import load
+def add_task(title): pass
""".strip()


def build_fake_pipeline() -> Pipeline:
    now = datetime.now()
    project_path = PROJECT_PATH
    Path(project_path).mkdir(parents=True, exist_ok=True)
    Path(f"{project_path}/docs").mkdir(exist_ok=True)

    stages = [
        StageNode(
            stage_type=StageType.REQUIREMENT,
            status=StageStatus.APPROVED,
            human_approval=ApproveAction.APPROVE,
            agent_output={"document": REQUIREMENT_DOC},
            started_at=now,
            completed_at=now,
        ),
        StageNode(
            stage_type=StageType.SOLUTION,
            status=StageStatus.APPROVED,
            human_approval=ApproveAction.APPROVE,
            agent_output={"design": SOLUTION_DOC},
            started_at=now,
            completed_at=now,
        ),
        StageNode(
            stage_type=StageType.CODING,
            status=StageStatus.COMPLETED,
            agent_output={"files": GENERATED_CODE, "summary": "生成了 4 个文件"},
            started_at=now,
            completed_at=now,
        ),
        StageNode(
            stage_type=StageType.TESTING,
            status=StageStatus.APPROVED,
            human_approval=ApproveAction.APPROVE,
            sub_phase=None,
            agent_output={
                "test_files": {"tests/test_task_manager.py": "def test_add_task(): pass"},
                "deps_manifest": {"pip_packages": ["pytest"]},
                "pass_rate": "8/8",
                "report": TEST_REPORT,
            },
            started_at=now,
            completed_at=now,
        ),
        StageNode(
            stage_type=StageType.REVIEW,
            status=StageStatus.APPROVED,
            human_approval=ApproveAction.APPROVE,
            agent_output={
                "report": REVIEW_REPORT,
                "score": 82,
                "issues": [
                    {"severity": "medium", "file": "storage.py", "line": 2, "message": "缺少异常处理"},
                    {"severity": "low", "file": "task_manager.py", "line": 3, "message": "缺少类型注解"},
                ],
            },
            started_at=now,
            completed_at=now,
        ),
        StageNode(
            stage_type=StageType.DELIVERY,
            status=StageStatus.PENDING,
        ),
    ]

    pipeline = Pipeline(
        id="pipe_test_stage6",
        title="时间管理 CLI App",
        status=PipelineStatus.RUNNING,
        context=PipelineContext(
            project_path=project_path,
            requirement_raw="帮助用户通过命令行管理每日任务列表，支持增删查改与优先级排序。",
            requirement_doc=REQUIREMENT_DOC,
            solution_doc=SOLUTION_DOC,
            generated_code=GENERATED_CODE,
            test_report=TEST_REPORT,
            review_report=REVIEW_REPORT,
            code_diff=CODE_DIFF,
            # No git context (disabled) - simpler test
            git=GitContext(mode=GitMode.DISABLED, enabled=False),
        ),
        stages=stages,
        logs=[
            "[TEST] Pipeline 创建（Stage 1-5 假数据已注入）",
            "[TEST] 直接测试 Stage 6 交付集成...",
        ],
        created_at=now,
        updated_at=now,
    )
    return pipeline


async def main() -> None:
    print("\n" + "=" * 60)
    print("Stage 6 测试: 交付集成 (DeliveryAgent)")
    print("=" * 60)

    pipeline = build_fake_pipeline()
    service = PipelineService()

    # 保存初始 pipeline
    await service.state_store.save(pipeline)
    print(f"✅ Pipeline 已创建: {pipeline.id}")
    print(f"   项目路径: {pipeline.context.project_path}")

    # 触发 Stage 6
    print("\n[Stage 6] 正在调用 DeliveryAgent...")
    t0 = datetime.now()
    await service._run_delivery(pipeline)
    elapsed = (datetime.now() - t0).total_seconds()

    # 重新加载（service 内部会 save）
    updated = await service.state_store.load(pipeline.id)
    assert updated is not None, "Pipeline not found after run"

    delivery_stage = updated.stages[5]
    print(f"\n[Stage 6] 耗时: {elapsed:.1f}s")
    print(f"[Stage 6] Stage 状态: {delivery_stage.status}")
    print(f"[Stage 6] Token 消耗: {delivery_stage.total_tokens}")

    out = delivery_stage.agent_output or {}
    print(f"\n{'─' * 50}")
    print("PR 标题:")
    print(f"  {out.get('pr_title', '（未生成）')}")

    print(f"\n{'─' * 50}")
    print("Commit Message:")
    print(f"  {out.get('commit_message', '（未生成）')}")

    print(f"\n{'─' * 50}")
    print("CHANGELOG:")
    changelog = out.get("changelog", "（未生成）")
    print(changelog[:300] if len(changelog) > 300 else changelog)

    print(f"\n{'─' * 50}")
    print("Deployment Notes:")
    print(out.get("deployment_notes", "（未生成）"))

    print(f"\n{'─' * 50}")
    print("PR 描述 (前 400 字):")
    pr_desc = out.get("pr_description", "（未生成）")
    print(pr_desc[:400] if len(pr_desc) > 400 else pr_desc)

    print(f"\n{'─' * 50}")
    print("交付文档 (result 字段, 前 500 字):")
    result_text = out.get("result", "（未生成）")
    print(result_text[:500] if len(result_text) > 500 else result_text)

    print(f"\n{'─' * 50}")
    print(f"变更文件数: {out.get('changes', 0)}")
    print(f"文件列表: {out.get('files_changed', [])}")
    print(f"生成时间: {out.get('generated_at', '')}")

    # Git context
    git_ctx = updated.context.git
    print(f"\n{'─' * 50}")
    print("Git 上下文:")
    print(f"  enabled: {git_ctx.enabled}")
    print(f"  pr_title: {git_ctx.pr_title}")
    print(f"  pr_command: {git_ctx.pr_command}")
    print(f"  pr_url: {git_ctx.pr_url}")

    # Check docs written
    docs_dir = Path(pipeline.context.project_path) / "docs"
    for doc_name in ("delivery.md", "pr.md"):
        doc_path = docs_dir / doc_name
        if doc_path.exists():
            size = doc_path.stat().st_size
            print(f"\n✅ {doc_name} 已写入 ({size} bytes)")
        else:
            print(f"\n⚠️  {doc_name} 未写入")

    # Logs
    print(f"\n{'─' * 50}")
    print("Pipeline 日志 (最后 8 条):")
    for log in updated.logs[-8:]:
        print(f"  {log}")

    # Final status
    print(f"\n{'─' * 50}")
    print(f"Pipeline 状态: {updated.status}")
    if delivery_stage.status == StageStatus.WAITING_HUMAN:
        print("✅ Stage 6 已进入 WAITING_HUMAN，等待人工审批")
    else:
        print(f"⚠️  Stage 状态异常: {delivery_stage.status}")

    print("\n" + "=" * 60)
    print("Stage 6 测试完成")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
