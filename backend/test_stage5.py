"""
Stage 5 (代码评审) 测试脚本
===================================================
模拟 Stage 1-4 已完成（注入假数据），直接测试 Stage 5 评审逻辑：
  - ReviewAgent LLM 调用
  - 生成结构化评审报告（score/issues/strengths/suggestions）
  - 写入 review_report.md
  - 进入 WAITING_HUMAN 等待人工审批

用法:
  cd backend
  python test_stage5.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from src.api.service import PipelineService
from src.models.pipeline import (
    ApproveAction,
    Pipeline,
    PipelineContext,
    PipelineStatus,
    StageNode,
    StageStatus,
    StageType,
)

# ──────────────────────────────────────────────────────────
# 假数据（复用 test_stage4 里的时间管理 app）
# ──────────────────────────────────────────────────────────

PROJECT_PATH = "/tmp/flowstate-test-stage5"

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

SOLUTION_STRUCTURED = {
    "architecture_overview": "单进程 Python CLI，三层结构：CLI→业务→存储，JSON 文件持久化。",
    "resolved_stack": {
        "frontend": "argparse CLI",
        "backend": "Python",
        "database": "JSON file",
        "state_management": "in-memory dict",
        "notifications": "none",
        "testing": "pytest",
    },
    "file_plan": [
        {"path": "models.py",       "layer": "domain",  "purpose": "Task 数据类",      "must_generate": True},
        {"path": "storage.py",      "layer": "infra",   "purpose": "JSON 读写",         "must_generate": True},
        {"path": "task_manager.py", "layer": "service", "purpose": "CRUD 业务逻辑",     "must_generate": True},
        {"path": "main.py",         "layer": "cli",     "purpose": "argparse CLI 入口", "must_generate": True},
    ],
    "api_design": [],
    "data_models": [{"name": "Task", "fields": [
        {"name": "id", "type": "str"}, {"name": "title", "type": "str"},
        {"name": "priority", "type": "int"}, {"name": "due_date", "type": "str|None"},
        {"name": "done", "type": "bool"},
    ]}],
}

GENERATED_CODE = {
    "models.py": """\
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import uuid

@dataclass
class Task:
    title: str
    priority: int = 3
    due_date: Optional[str] = None
    done: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "priority": self.priority,
                "due_date": self.due_date, "done": self.done}

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(id=data["id"], title=data["title"], priority=data.get("priority", 3),
                   due_date=data.get("due_date"), done=data.get("done", False))
""",
    "storage.py": """\
from __future__ import annotations
import json
from pathlib import Path
from typing import List
from models import Task

DEFAULT_PATH = Path("tasks.json")

def load_tasks(path: Path = DEFAULT_PATH) -> List[Task]:
    if not path.exists():
        return []
    return [Task.from_dict(item) for item in json.loads(path.read_text(encoding="utf-8"))]

def save_tasks(tasks: List[Task], path: Path = DEFAULT_PATH) -> None:
    path.write_text(json.dumps([t.to_dict() for t in tasks], ensure_ascii=False, indent=2), encoding="utf-8")
""",
    "task_manager.py": """\
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from models import Task
from storage import load_tasks, save_tasks

class TaskManager:
    def __init__(self, store_path: Path = Path("tasks.json")):
        self._path = store_path
        self._tasks: List[Task] = load_tasks(self._path)

    def _save(self) -> None:
        save_tasks(self._tasks, self._path)

    def add(self, title: str, priority: int = 3, due_date: Optional[str] = None) -> Task:
        if not title.strip():
            raise ValueError("任务标题不能为空")
        if not (1 <= priority <= 5):
            raise ValueError("优先级必须在 1-5 之间")
        task = Task(title=title.strip(), priority=priority, due_date=due_date)
        self._tasks.append(task)
        self._save()
        return task

    def list(self, sort_by: str = "priority") -> List[Task]:
        return sorted(self._tasks, key=lambda t: -t.priority) if sort_by == "priority" else list(self._tasks)

    def complete(self, task_id: str) -> Task:
        for task in self._tasks:
            if task.id == task_id:
                task.done = True
                self._save()
                return task
        raise KeyError(f"任务 {task_id!r} 不存在")

    def delete(self, task_id: str) -> bool:
        original = len(self._tasks)
        self._tasks = [t for t in self._tasks if t.id != task_id]
        if len(self._tasks) < original:
            self._save()
            return True
        return False
""",
    "main.py": """\
from __future__ import annotations
import argparse
from task_manager import TaskManager

def main():
    parser = argparse.ArgumentParser(description="时间管理 CLI")
    sub = parser.add_subparsers(dest="cmd")
    add_p = sub.add_parser("add"); add_p.add_argument("title")
    add_p.add_argument("-p", "--priority", type=int, default=3)
    add_p.add_argument("-d", "--due-date")
    sub.add_parser("list")
    done_p = sub.add_parser("done"); done_p.add_argument("id")
    del_p = sub.add_parser("delete"); del_p.add_argument("id")
    args = parser.parse_args()
    tm = TaskManager()
    if args.cmd == "add":
        t = tm.add(args.title, args.priority, args.due_date)
        print(f"✅ [{t.id}] {t.title} (P{t.priority})")
    elif args.cmd == "list":
        for t in tm.list(): print(f"  {'✓' if t.done else '○'} [{t.id}] P{t.priority} {t.title}")
    elif args.cmd == "done":
        print(f"✅ {tm.complete(args.id).title}")
    elif args.cmd == "delete":
        print("🗑️ 已删除" if tm.delete(args.id) else "❌ 未找到")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
""",
}

# 模拟 Stage 4 产出的测试报告
TEST_REPORT = """
## 测试报告

- 总计: 8 项测试
- 通过: 8 ✅
- 失败: 0 ❌
- 代码覆盖率: N/A%

### 覆盖模块
- test_models.py: Task 数据类创建、序列化、反序列化
- test_task_manager.py: add/list/complete/delete 完整 CRUD + 异常边界
""".strip()

# 模拟 Stage 4 生成的测试文件
TEST_FILES = {
    "tests/test_models.py": """\
import pytest
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import Task

def test_task_default_values():
    t = Task(title="买牛奶")
    assert t.priority == 3
    assert t.done is False
    assert t.due_date is None
    assert len(t.id) == 8

def test_task_to_dict():
    t = Task(title="写代码", priority=5, id="abc12345")
    d = t.to_dict()
    assert d["title"] == "写代码"
    assert d["priority"] == 5

def test_task_from_dict():
    data = {"id": "x1y2z3w4", "title": "跑步", "priority": 2, "due_date": None, "done": True}
    t = Task.from_dict(data)
    assert t.done is True
    assert t.title == "跑步"
""",
    "tests/test_task_manager.py": """\
import pytest, sys, os, tempfile
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from task_manager import TaskManager

@pytest.fixture
def tm(tmp_path):
    return TaskManager(store_path=tmp_path / "tasks.json")

def test_add_task(tm):
    t = tm.add("写文档", priority=4)
    assert t.title == "写文档"
    assert t.priority == 4

def test_add_empty_title(tm):
    with pytest.raises(ValueError):
        tm.add("")

def test_add_invalid_priority(tm):
    with pytest.raises(ValueError):
        tm.add("测试", priority=6)

def test_list_sorted(tm):
    tm.add("低优先级", priority=1)
    tm.add("高优先级", priority=5)
    tasks = tm.list()
    assert tasks[0].priority == 5

def test_complete(tm):
    t = tm.add("完成我")
    tm.complete(t.id)
    assert tm.get(t.id).done is True

def test_complete_not_found(tm):
    with pytest.raises(KeyError):
        tm.complete("不存在的ID")

def test_delete(tm):
    t = tm.add("删除我")
    assert tm.delete(t.id) is True
    assert tm.get(t.id) is None

def test_delete_not_found(tm):
    assert tm.delete("不存在") is False
""",
}


# ──────────────────────────────────────────────────────────
# 工具
# ──────────────────────────────────────────────────────────

def sep(label: str = "", char: str = "─", width: int = 62) -> None:
    if label:
        pad = max(0, width - len(label) - 2)
        print(f"\n{char * (pad // 2)} {label} {char * (pad - pad // 2)}")
    else:
        print(char * width)


def print_stage(stage: StageNode, index: int) -> None:
    icons = {
        StageStatus.COMPLETED: "✅", StageStatus.WAITING_HUMAN: "⏸️ ",
        StageStatus.RUNNING: "🔄", StageStatus.FAILED: "❌",
        StageStatus.PENDING: "⬜", StageStatus.APPROVED: "✅",
    }
    print(f"  {icons.get(stage.status, '?')}  Stage {index + 1}: {stage.stage_type.value}  [{stage.status.value}]")
    if stage.agent_output:
        out = stage.agent_output
        if "score" in out:
            print(f"       score    = {out['score']}/100")
        if "issues" in out:
            issues = out["issues"]
            critical = sum(1 for i in issues if i.get("severity") == "critical")
            high = sum(1 for i in issues if i.get("severity") == "high")
            print(f"       issues   = {len(issues)} 个（critical={critical}, high={high}）")
        if "report" in out and isinstance(out["report"], str):
            print(f"       report[:120] = {out['report'][:120].replace(chr(10), ' ')}")


def write_code_files(project_path: str, files: dict[str, str]) -> None:
    root = Path(project_path)
    root.mkdir(parents=True, exist_ok=True)
    for rel_path, content in files.items():
        dest = root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")


def build_fake_pipeline() -> Pipeline:
    now = datetime.now()

    # Stage 4 (testing) agent_output — 包含测试文件和报告
    testing_output = {
        "test_files": TEST_FILES,
        "deps_manifest": {"pip_packages": ["pytest"], "npm_packages": []},
        "test_results": {"total": 8, "passed": 8, "failed": 0, "errors": [], "ran": True},
        "report": TEST_REPORT,
        "pass_rate": "8/8",
    }

    stages = [
        StageNode(stage_type=StageType.REQUIREMENT, status=StageStatus.COMPLETED,
                  started_at=now, completed_at=now,
                  agent_output={"document": REQUIREMENT_DOC}, human_approval=ApproveAction.APPROVE),
        StageNode(stage_type=StageType.SOLUTION, status=StageStatus.COMPLETED,
                  started_at=now, completed_at=now,
                  agent_output={"design": SOLUTION_DOC}, human_approval=ApproveAction.APPROVE),
        StageNode(stage_type=StageType.CODING, status=StageStatus.COMPLETED,
                  started_at=now, completed_at=now,
                  agent_output={"files": GENERATED_CODE, "structure": list(GENERATED_CODE.keys()),
                                "resolved_stack": SOLUTION_STRUCTURED["resolved_stack"]}),
        StageNode(stage_type=StageType.TESTING, status=StageStatus.APPROVED,
                  started_at=now, completed_at=now,
                  agent_output=testing_output, human_approval=ApproveAction.APPROVE),
        StageNode(stage_type=StageType.REVIEW,   status=StageStatus.PENDING),
        StageNode(stage_type=StageType.DELIVERY, status=StageStatus.PENDING),
    ]

    context = PipelineContext(
        requirement_raw="请生成一个时间管理 CLI app",
        project_path=PROJECT_PATH,
        requirement_doc=REQUIREMENT_DOC,
        solution_doc=SOLUTION_DOC,
        solution_structured=SOLUTION_STRUCTURED,
        generated_code=GENERATED_CODE,
        test_report=TEST_REPORT,
    )

    return Pipeline(
        id="test-stage5-local",
        title="时间管理 CLI App（Stage 5 测试）",
        status=PipelineStatus.RUNNING,
        context=context,
        stages=stages,
        created_at=now,
        updated_at=now,
        logs=["[test] Stage 1-4 已模拟完成，进入 Stage 5 评审"],
    )


# ──────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────

async def main() -> None:
    sep("Stage 5 代码评审测试", "═")

    # 1. 写入代码文件到项目目录
    write_code_files(PROJECT_PATH, GENERATED_CODE)
    # 也写入测试文件
    for rel_path, content in TEST_FILES.items():
        dest = Path(PROJECT_PATH) / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    print(f"  📁 项目目录: {PROJECT_PATH}")

    # 2. 构建并保存假 Pipeline
    sep("Step 1: 构建假 Pipeline（Stage 1-4 已完成）")
    service = PipelineService()
    pipeline = build_fake_pipeline()
    await service.state_store.save(pipeline)
    print(f"  Pipeline ID: {pipeline.id}")
    for i, stage in enumerate(pipeline.stages):
        print_stage(stage, i)

    # 3. 运行 Stage 5
    sep("Step 2: 运行 Stage 5 ReviewAgent")
    print("  ⏳ 调用 ReviewAgent，等待 LLM 响应...\n")
    await service._run_review(pipeline)

    # 4. 重新加载查看结果
    pipeline = await service.state_store.load(pipeline.id)
    assert pipeline is not None
    review_stage = pipeline.stages[4]

    sep("评审结果")
    print_stage(review_stage, 4)

    if review_stage.status == StageStatus.FAILED:
        print(f"\n  ❌ 评审失败: {pipeline.error}")
        return

    out = review_stage.agent_output or {}

    # 展示结构化数据
    sep("结构化评审数据")
    print(f"  评分: {out.get('score', '?')}/100")
    review_data = out.get("review", {})
    print(f"  总评: {review_data.get('summary', '—')}")

    strengths = review_data.get("strengths", [])
    print(f"\n  ✅ 优点 ({len(strengths)} 项):")
    for s in strengths:
        print(f"    · {s}")

    issues = out.get("issues", review_data.get("issues", []))
    print(f"\n  ⚠️  问题 ({len(issues)} 项):")
    sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
    for issue in issues:
        icon = sev_icon.get(issue.get("severity", ""), "⚪")
        print(f"    {icon} [{issue.get('severity')}] {issue.get('file', '?')}:{issue.get('line', '?')} — {issue.get('message', '')}")

    suggestions = review_data.get("suggestions", [])
    print(f"\n  💡 建议 ({len(suggestions)} 项):")
    for s in suggestions:
        print(f"    · {s}")

    # 完整报告
    sep("评审报告（Markdown）")
    report = out.get("report", "")
    if report:
        print(report[:2000])
        review_md = Path(PROJECT_PATH) / "review_report.md"
        if review_md.exists():
            print(f"\n  📄 已写入: {review_md}")

    # 5. 确认状态正确
    sep("状态检查")
    assert review_stage.status == StageStatus.WAITING_HUMAN, \
        f"❌ 期望 WAITING_HUMAN，实际 {review_stage.status.value}"
    print(f"  ✅ status = WAITING_HUMAN（正确，等待人工审批）")
    print(f"  ✅ pipeline.status = {pipeline.status.value}")

    # 6. 模拟审批
    sep("Step 3: 模拟人工审批")
    score = out.get("score", 0)
    critical_count = sum(1 for i in issues if i.get("severity") == "critical")
    print(f"  评分: {score}/100  Critical 问题: {critical_count} 个")
    answer = input("\n  ▶ 审批决策 [a=通过 / r=拒绝 / q=退出]: ").strip().lower()

    if answer == "q":
        print("  已退出。")
        return
    elif answer == "r":
        reason = input("  拒绝原因: ").strip() or "需要改进代码质量"
        updated = await service.reject_stage(pipeline.id, stage_index=4, reason=reason)
        print(f"  ✅ 已拒绝，status = {updated.stages[4].status.value}")
        print(f"  （reject 后 retry_stage 会在真实场景中由路由 create_task 触发）")
    elif answer == "a":
        updated = await service.approve_stage(pipeline.id, stage_index=4)
        print(f"  ✅ 已审批，status = {updated.stages[4].status.value}")
        print(f"  （approve 后 continue_after_approval 会触发 Stage 6 Delivery）")

    sep("Pipeline 最终日志")
    pipeline = await service.state_store.load(pipeline.id)
    assert pipeline is not None
    for log in pipeline.logs[-12:]:
        print(f"  {log}")

    sep("✅ Stage 5 测试完成", "═")


if __name__ == "__main__":
    asyncio.run(main())
