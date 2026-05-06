"""
Stage 4 两阶段测试脚本
===================================================
跳过 Stage 1-3（注入假数据），直接测试 Stage 4 的完整流程：
  Phase 1 → LLM 生成测试文件 + deps manifest → 等待用户确认
  Phase 2 → 安装依赖 + 执行测试 → 输出报告

用法:
  cd backend
  python test_stage4.py
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
# 假数据：一个简单的 Python 时间管理 CLI app
# ──────────────────────────────────────────────────────────

PROJECT_PATH = "/tmp/flowstate-test-stage4"

REQUIREMENT_DOC = """
## 需求文档：时间管理 CLI App

### 功能目标
帮助用户通过命令行管理每日任务列表，支持增删查改与优先级排序。

### 核心需求
1. 添加任务（标题、优先级 1-5、截止日期）
2. 列出全部任务，支持按优先级排序
3. 标记任务为完成
4. 删除任务
5. 数据持久化存储（JSON 文件）
""".strip()

SOLUTION_DOC = """
## 技术方案：时间管理 CLI App

### 技术栈
- 语言: Python 3.11
- 数据存储: JSON 文件（本地持久化）
- CLI 框架: argparse（标准库）
- 测试框架: pytest

### 文件结构
- `models.py`：Task 数据模型
- `storage.py`：JSON 持久化读写
- `task_manager.py`：业务逻辑（CRUD）
- `main.py`：CLI 入口

### 核心接口
- `TaskManager.add(title, priority, due_date) -> Task`
- `TaskManager.list(sort_by="priority") -> list[Task]`
- `TaskManager.complete(task_id) -> Task`
- `TaskManager.delete(task_id) -> bool`
""".strip()

SOLUTION_STRUCTURED = {
    "architecture_overview": "单进程 Python CLI，三层结构：CLI层→业务层→存储层，JSON文件持久化。",
    "resolved_stack": {
        "frontend": "argparse CLI",
        "backend": "Python",
        "database": "JSON file",
        "state_management": "in-memory dict",
        "notifications": "none",
        "testing": "pytest",
    },
    "file_plan": [
        {"path": "models.py",       "layer": "domain",   "purpose": "Task 数据类",          "must_generate": True},
        {"path": "storage.py",      "layer": "infra",    "purpose": "JSON 读写持久化",       "must_generate": True},
        {"path": "task_manager.py", "layer": "service",  "purpose": "CRUD 业务逻辑",         "must_generate": True},
        {"path": "main.py",         "layer": "cli",      "purpose": "argparse CLI 入口",     "must_generate": True},
    ],
    "api_design": [],
    "data_models": [
        {
            "name": "Task",
            "fields": [
                {"name": "id",       "type": "str",      "description": "UUID"},
                {"name": "title",    "type": "str",      "description": "任务标题"},
                {"name": "priority", "type": "int",      "description": "1-5，越大越高"},
                {"name": "due_date", "type": "str|None", "description": "截止日期 YYYY-MM-DD"},
                {"name": "done",     "type": "bool",     "description": "是否完成"},
            ],
        }
    ],
}

# 实际写入项目目录的代码文件
GENERATED_CODE: dict[str, str] = {
    "models.py": """\
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class Task:
    title: str
    priority: int = 3          # 1-5
    due_date: Optional[str] = None
    done: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "due_date": self.due_date,
            "done": self.done,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            priority=data.get("priority", 3),
            due_date=data.get("due_date"),
            done=data.get("done", False),
        )
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
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Task.from_dict(item) for item in data]


def save_tasks(tasks: List[Task], path: Path = DEFAULT_PATH) -> None:
    path.write_text(
        json.dumps([t.to_dict() for t in tasks], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
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
        if sort_by == "priority":
            return sorted(self._tasks, key=lambda t: -t.priority)
        return list(self._tasks)

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

    def get(self, task_id: str) -> Optional[Task]:
        return next((t for t in self._tasks if t.id == task_id), None)
""",

    "main.py": """\
from __future__ import annotations
import argparse
import sys
from task_manager import TaskManager


def main():
    parser = argparse.ArgumentParser(description="时间管理 CLI")
    sub = parser.add_subparsers(dest="cmd")

    add_p = sub.add_parser("add", help="添加任务")
    add_p.add_argument("title")
    add_p.add_argument("-p", "--priority", type=int, default=3)
    add_p.add_argument("-d", "--due-date")

    sub.add_parser("list", help="列出任务")

    done_p = sub.add_parser("done", help="标记完成")
    done_p.add_argument("id")

    del_p = sub.add_parser("delete", help="删除任务")
    del_p.add_argument("id")

    args = parser.parse_args()
    tm = TaskManager()

    if args.cmd == "add":
        task = tm.add(args.title, args.priority, args.due_date)
        print(f"✅ 已添加: [{task.id}] {task.title} (优先级 {task.priority})")
    elif args.cmd == "list":
        tasks = tm.list()
        if not tasks:
            print("（暂无任务）")
        for t in tasks:
            status = "✓" if t.done else "○"
            print(f"  {status} [{t.id}] P{t.priority} {t.title}")
    elif args.cmd == "done":
        task = tm.complete(args.id)
        print(f"✅ 已完成: {task.title}")
    elif args.cmd == "delete":
        ok = tm.delete(args.id)
        print("🗑️ 已删除" if ok else "❌ 未找到")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
""",
}


# ──────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────

def sep(label: str = "", char: str = "─", width: int = 62) -> None:
    if label:
        pad = max(0, width - len(label) - 2)
        left = pad // 2
        right = pad - left
        print(f"\n{char * left} {label} {char * right}")
    else:
        print(char * width)


def print_stage(stage: StageNode, index: int, name: str) -> None:
    status_icon = {
        StageStatus.COMPLETED: "✅",
        StageStatus.WAITING_HUMAN: "⏸️ ",
        StageStatus.RUNNING: "🔄",
        StageStatus.FAILED: "❌",
        StageStatus.PENDING: "⬜",
        StageStatus.APPROVED: "✅",
    }.get(stage.status, "?")
    print(f"  {status_icon}  Stage {index + 1}: {name}  [{stage.status.value}]")
    if stage.sub_phase:
        print(f"       sub_phase = {stage.sub_phase!r}")
    if stage.agent_output:
        out = stage.agent_output
        for key in ("report", "pass_rate", "summary"):
            if key in out and isinstance(out[key], str):
                preview = out[key][:200].replace("\n", " ")
                print(f"       {key}: {preview}")
        if "deps_manifest" in out:
            dm = out["deps_manifest"]
            print(f"       deps_manifest: pip={dm.get('pip_packages', [])}  npm={dm.get('npm_packages', [])}")
        if "test_files" in out:
            print(f"       test_files: {list(out['test_files'].keys())}")


def write_code_files(project_path: str, files: dict[str, str]) -> None:
    root = Path(project_path)
    root.mkdir(parents=True, exist_ok=True)
    for rel_path, content in files.items():
        dest = root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        print(f"  📄 写入: {dest}")


def build_fake_pipeline() -> Pipeline:
    now = datetime.now()
    stages = [
        StageNode(
            stage_type=StageType.REQUIREMENT,
            status=StageStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            agent_output={"document": REQUIREMENT_DOC},
            human_approval=ApproveAction.APPROVE,
        ),
        StageNode(
            stage_type=StageType.SOLUTION,
            status=StageStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            agent_output={"design": SOLUTION_DOC},
            human_approval=ApproveAction.APPROVE,
        ),
        StageNode(
            stage_type=StageType.CODING,
            status=StageStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            agent_output={
                "files": GENERATED_CODE,
                "structure": list(GENERATED_CODE.keys()),
                "language": "Python",
                "framework": "argparse CLI",
                "resolved_stack": SOLUTION_STRUCTURED["resolved_stack"],
            },
        ),
        StageNode(stage_type=StageType.TESTING,  status=StageStatus.PENDING),
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
    )

    return Pipeline(
        id="test-stage4-local",
        title="时间管理 CLI App（Stage 4 测试）",
        status=PipelineStatus.RUNNING,
        context=context,
        stages=stages,
        created_at=now,
        updated_at=now,
        logs=["[test] 假数据 pipeline 已就绪，Stage 1-3 已模拟完成"],
    )


# ──────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────

async def main() -> None:
    sep("Stage 4 两阶段测试", "═")

    # 1. 写入假代码文件到项目目录
    sep("Step 0: 写入假代码文件到项目目录")
    write_code_files(PROJECT_PATH, GENERATED_CODE)

    # 2. 构建 Pipeline 并保存
    sep("Step 1: 构建假 Pipeline（Stage 1-3 已完成）")
    service = PipelineService()
    pipeline = build_fake_pipeline()
    await service.state_store.save(pipeline)
    print(f"  Pipeline ID: {pipeline.id}")
    for i, stage in enumerate(pipeline.stages):
        name = stage.stage_type.value
        print_stage(stage, i, name)

    # ──────────────────────────────────────────
    # Phase 1: LLM 生成测试文件 + deps manifest
    # ──────────────────────────────────────────
    sep("Step 2: 运行 Stage 4 Phase 1（LLM 生成测试 + deps）")
    print("  ⏳ 调用 TestAgent，等待 LLM 响应...\n")

    await service._run_testing(pipeline)

    # 重新加载（service 内部 save 了新状态）
    pipeline = await service.state_store.load(pipeline.id)
    assert pipeline is not None

    testing_stage = pipeline.stages[3]
    sep("Phase 1 结果")
    print_stage(testing_stage, 3, "测试验证")

    if testing_stage.status != StageStatus.WAITING_HUMAN:
        print(f"\n❌ 预期 WAITING_HUMAN，实际 {testing_stage.status.value}")
        print(f"   错误信息: {pipeline.error}")
        return

    deps = testing_stage.agent_output.get("deps_manifest", {})
    test_files = testing_stage.agent_output.get("test_files", {})
    print(f"\n  📦 deps_manifest:")
    print(f"     pip_packages : {deps.get('pip_packages', [])}")
    print(f"     npm_packages : {deps.get('npm_packages', [])}")
    if deps.get("install_commands"):
        print(f"     install_cmds : {deps['install_commands']}")
    print(f"\n  📝 生成的测试文件: {list(test_files.keys())}")
    for fname, content in test_files.items():
        preview = content[:300].replace("\n", "\n    ")
        print(f"\n  ── {fname} ──\n    {preview}")

    # ──────────────────────────────────────────
    # 等待用户确认（模拟 human-in-loop）
    # ──────────────────────────────────────────
    sep("Step 3: 等待用户确认（模拟 Human-in-Loop）")
    print("  上面是 Phase 1 生成的测试文件和依赖清单。")
    print("  在真实界面中，用户会在 CheckpointReview 页点击「确认安装并运行测试」。")
    answer = input("\n  ▶ 是否继续执行 Phase 2（安装依赖并运行测试）？[y/N] ").strip().lower()
    if answer not in ("y", "yes", "1"):
        print("  已取消，脚本退出。")
        return

    # ──────────────────────────────────────────
    # Phase 2: confirm_testing_deps → _run_testing_phase2
    # ──────────────────────────────────────────
    sep("Step 4: confirm_testing_deps（模拟点击确认按钮）")
    pipeline = await service.confirm_testing_deps(pipeline.id, stage_index=3)
    testing_stage = pipeline.stages[3]
    print(f"  status   = {testing_stage.status.value}")
    print(f"  sub_phase = {testing_stage.sub_phase!r}  （已清空）")

    sep("Step 5: 运行 Phase 2（安装依赖 + 执行测试）")
    print("  ⏳ 安装依赖 + 执行测试，请稍候...\n")
    await service._run_testing_phase2(pipeline)

    # 重新加载
    pipeline = await service.state_store.load(pipeline.id)
    assert pipeline is not None
    testing_stage = pipeline.stages[3]

    sep("Phase 2 结果")
    print_stage(testing_stage, 3, "测试验证")

    out = testing_stage.agent_output or {}
    test_results = out.get("test_results", {})
    install_result = out.get("install_result", {})
    report = out.get("report", "")

    print(f"\n  安装结果: errors={install_result.get('errors', [])}")
    print(f"  测试结果: passed={test_results.get('passed')}/{test_results.get('total')}  ran={test_results.get('ran')}")

    if report:
        sep("测试报告")
        print(report[:1500])

    sep("Pipeline 最终日志")
    for log in pipeline.logs[-15:]:
        print(f"  {log}")

    sep("✅ Stage 4 测试完成", "═")


if __name__ == "__main__":
    asyncio.run(main())
