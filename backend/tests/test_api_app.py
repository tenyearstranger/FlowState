import asyncio
import base64

from fastapi.testclient import TestClient

from src.agents.base_agent import AgentInput, AgentOutput
from src.agents.requirement_agent import RequirementAgent
from src.api.app import create_app
from src.bootstrap import create_engine
from src.models.pipeline import PipelineStatus, StageType
from src.store.state_store import StateStore


class FakeRequirementAgent:
    async def execute(self, input_data):
        project_path = input_data.context.get("project_path", "")
        project_summary = input_data.context.get("project_summary", "")
        requirement_raw = input_data.context.get("requirement_raw", "")
        document = f"""# 需求文档

## 原始需求
{requirement_raw}

## 项目目录
{project_path}

## 项目摘要
{project_summary}

```json
{{
  "modules": [
    {{"name": "收藏功能", "priority": "P0"}},
    {{"name": "列表展示", "priority": "P1"}}
  ]
}}
```"""
        return AgentOutput(
            success=True,
            result={
                "document": document,
                "raw_requirement": requirement_raw,
                "modules": [
                    {"name": "收藏功能", "priority": "P0"},
                    {"name": "列表展示", "priority": "P1"},
                ],
            },
            summary="需求分析完成，识别出 2 个功能模块",
            details=document,
            needs_human_review=True,
        )


class FakeSolutionAgent:
    async def execute(self, input_data):
        requirement_doc = input_data.context.get("requirement_doc", "")
        document = f"""# 技术方案文档

## 整体架构
采用前后端分离架构，后端使用 FastAPI，前端使用 React。

## 核心 API 设计
### 创建计划
- 方法：POST
- 路径：`/plans`

## 需求背景
{requirement_doc}

```json
{{
  "resolved_stack": {{
    "frontend": "React Native",
    "backend": "FastAPI",
    "database": "SQLite",
    "state_management": "Zustand",
    "notifications": "Expo Notifications",
    "testing": "pytest + vitest"
  }},
  "file_plan": [
    {{
      "path": "app/main.py",
      "layer": "backend",
      "purpose": "FastAPI 入口",
      "must_generate": true
    }},
    {{
      "path": "requirements.txt",
      "layer": "config",
      "purpose": "Python 依赖定义",
      "must_generate": true
    }}
  ],
  "api_design": [
    {{
      "name": "创建计划",
      "method": "POST",
      "path": "/plans",
      "description": "创建每日计划",
      "request": "标题、日期、优先级",
      "response": "计划详情"
    }}
  ]
}}
```"""
        return AgentOutput(
            success=True,
            result={
                "design": document,
                "architecture": "前后端分离架构",
                "tech_stack": ["FastAPI", "React", "SQLite"],
                "resolved_stack": {
                    "frontend": "React Native",
                    "backend": "FastAPI",
                    "database": "SQLite",
                    "state_management": "Zustand",
                    "notifications": "Expo Notifications",
                    "testing": "pytest + vitest",
                },
                "file_plan": [
                    {
                        "path": "app/main.py",
                        "layer": "backend",
                        "purpose": "FastAPI 入口",
                        "must_generate": True,
                    },
                    {
                        "path": "requirements.txt",
                        "layer": "config",
                        "purpose": "Python 依赖定义",
                        "must_generate": True,
                    },
                ],
                "structured_solution": {
                    "resolved_stack": {
                        "frontend": "React Native",
                        "backend": "FastAPI",
                        "database": "SQLite",
                        "state_management": "Zustand",
                        "notifications": "Expo Notifications",
                        "testing": "pytest + vitest",
                    },
                    "file_plan": [
                        {
                            "path": "app/main.py",
                            "layer": "backend",
                            "purpose": "FastAPI 入口",
                            "must_generate": True,
                        },
                        {
                            "path": "requirements.txt",
                            "layer": "config",
                            "purpose": "Python 依赖定义",
                            "must_generate": True,
                        },
                    ],
                },
                "api_design": [
                    {
                        "name": "创建计划",
                        "method": "POST",
                        "path": "/plans",
                        "description": "创建每日计划",
                        "request": "标题、日期、优先级",
                        "response": "计划详情",
                    }
                ],
            },
            summary="技术方案已生成：1 个核心接口，3 项技术选型",
            details=document,
            needs_human_review=True,
        )


class FakeCodeAgent:
    async def execute(self, input_data):
        structured_solution = input_data.context.get("solution_structured", {})
        file_plan = structured_solution.get("file_plan", [])
        assert any(item.get("path") == "app/main.py" for item in file_plan)
        assert structured_solution.get("resolved_stack", {}).get("backend") == "FastAPI"
        return AgentOutput(
            success=True,
            result={
                "files": {
                    "app/main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n",
                    "requirements.txt": "fastapi\nuvicorn\n",
                },
                "structure": ["app/main.py", "requirements.txt"],
                "language": "python",
                "framework": "fastapi",
            },
            summary="代码生成完成，共 2 个文件",
            details="  ✅ app/main.py\n  ✅ requirements.txt",
            needs_human_review=False,
        )


class FakeTestAgent:
    async def execute(self, input_data):
        generated_code = input_data.context.get("generated_code", {})
        assert "app/main.py" in generated_code
        return AgentOutput(
            success=True,
            result={
                "test_files": {
                    "tests/test_app.py": (
                        "from fastapi.testclient import TestClient\n"
                        "from app.main import app\n\n"
                        "def test_health():\n"
                        "    client = TestClient(app)\n"
                        "    response = client.get('/')\n"
                        "    assert response.status_code in {200, 404}\n"
                    )
                },
                "test_results": {"total": 1, "passed": 1, "failed": 0, "coverage": 85},
                "report": "## 测试报告\n\n- 总计: 1 项测试\n- 通过: 1 ✅\n- 失败: 0 ❌\n- 代码覆盖率: 85%",
                "pass_rate": "1/1",
            },
            summary="测试完成：1/1 通过",
            details="## 测试报告\n\n- 总计: 1 项测试\n- 通过: 1 ✅\n- 失败: 0 ❌\n- 代码覆盖率: 85%",
            needs_human_review=False,
        )


class FakeFailingTestAgent:
    async def execute(self, input_data):
        generated_code = input_data.context.get("generated_code", {})
        assert "app/main.py" in generated_code
        return AgentOutput(
            success=False,
            result={
                "test_files": {
                    "tests/test_app.py": (
                        "def test_health():\n"
                        "    assert False, 'health endpoint missing'\n"
                    )
                },
                "test_results": {
                    "total": 1,
                    "passed": 0,
                    "failed": 1,
                    "coverage": 40,
                    "errors": ["health endpoint missing"],
                },
                "report": "## 测试报告\n\n- 总计: 1 项测试\n- 通过: 0 ✅\n- 失败: 1 ❌\n- 代码覆盖率: 40%\n\n### 错误详情\n- health endpoint missing",
                "pass_rate": "0/1",
            },
            summary="测试完成：0/1 通过",
            details="## 测试报告\n\n- 总计: 1 项测试\n- 通过: 0 ✅\n- 失败: 1 ❌\n- 代码覆盖率: 40%",
            needs_human_review=True,
        )


class FakeReviewAgent:
    async def execute(self, input_data):
        test_report = input_data.context.get("test_report", "")
        assert "测试报告" in test_report
        return AgentOutput(
            success=True,
            result={
                "review": {
                    "score": 92,
                    "summary": "整体实现清晰，建议补充边界测试。",
                    "strengths": ["结构清晰", "接口定义明确"],
                    "issues": [],
                    "suggestions": ["补充异常路径断言"],
                },
                "report": "## 代码评审报告\n\n**评分: 92/100**\n\n- 建议补充异常路径断言",
                "issues": [],
                "score": 92,
            },
            summary="评审完成：评分 92/100，发现 0 个问题",
            details="## 代码评审报告\n\n**评分: 92/100**\n\n- 建议补充异常路径断言",
            needs_human_review=True,
        )


class FakeDeliveryAgent:
    async def execute(self, input_data):
        review_report = input_data.context.get("review_report", "")
        assert "代码评审报告" in review_report
        return AgentOutput(
            success=True,
            result={
                "pr_title": "feat: 完成自律应用核心链路",
                "pr_description": "包含需求、方案、代码、测试与评审结果。",
                "branch": "feature/self-discipline-app",
                "commit_message": "feat: deliver self-discipline app pipeline output",
                "deployment_command": "docker compose up -d",
                "changes": 3,
                "files_changed": ["app/main.py", "requirements.txt", "tests/test_app.py"],
                "pr_number": 88,
                "result": "## 📦 交付汇总\n\n**PR 编号:** #88\n**标题:** feat: 完成自律应用核心链路",
            },
            summary="交付就绪：生成 PR #88，变更 3 个文件",
            details="## 📦 交付汇总\n\n**PR 编号:** #88\n**标题:** feat: 完成自律应用核心链路",
            needs_human_review=True,
        )


def create_test_client(tmp_path):
    engine = create_engine(StateStore(storage_dir=str(tmp_path)))
    engine.agents[StageType.REQUIREMENT] = FakeRequirementAgent()
    engine.agents[StageType.SOLUTION] = FakeSolutionAgent()
    engine.agents[StageType.CODING] = FakeCodeAgent()
    engine.agents[StageType.TESTING] = FakeTestAgent()
    engine.agents[StageType.REVIEW] = FakeReviewAgent()
    engine.agents[StageType.DELIVERY] = FakeDeliveryAgent()
    app = create_app(engine=engine)
    return TestClient(app), engine


def test_healthcheck(tmp_path):
    client, _ = create_test_client(tmp_path)

    with client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_pipeline(tmp_path):
    client, _ = create_test_client(tmp_path)

    with client:
        create_response = client.post(
            "/api/v1/pipelines",
            json={
                "title": "Todo API",
                "requirement": "Build a todo app backend.",
            },
        )

        assert create_response.status_code == 201
        created_pipeline = create_response.json()["pipeline"]
        assert created_pipeline["title"] == "Todo API"
        assert created_pipeline["status"] == PipelineStatus.PENDING.value
        assert len(created_pipeline["stages"]) == 6

        get_response = client.get(f"/api/v1/pipelines/{created_pipeline['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == created_pipeline["id"]


def test_run_pipeline_endpoint_schedules_background_work(tmp_path):
    client, engine = create_test_client(tmp_path)
    called = {"value": False}

    async def fake_run_pipeline(pipeline):
        called["value"] = True
        pipeline.status = PipelineStatus.RUNNING
        await engine.state_store.save(pipeline)

    engine.run_pipeline = fake_run_pipeline

    with client:
        create_response = client.post(
            "/api/v1/pipelines",
            json={
                "title": "Async run",
                "requirement": "Run the pipeline asynchronously.",
            },
        )
        pipeline_id = create_response.json()["pipeline"]["id"]

        run_response = client.post(f"/api/v1/pipelines/{pipeline_id}/run")
        assert run_response.status_code == 200

    assert called["value"] is True


def test_frontend_mock_dashboard_endpoints(tmp_path):
    client, _ = create_test_client(tmp_path)

    with client:
        pipelines_response = client.get("/api/pipelines")
        agents_response = client.get("/api/agents")
        checkpoints_response = client.get("/api/checkpoints", params={"status": "all"})
        analytics_response = client.get("/api/analytics")
        activities_response = client.get("/api/activities/recent")
        detail_response = client.get("/api/pipelines/pl-001")
        logs_response = client.get("/api/pipelines/pl-001/logs")

    assert pipelines_response.status_code == 200
    assert len(pipelines_response.json()) == 5
    assert pipelines_response.json()[0]["status"] == "running"

    assert agents_response.status_code == 200
    assert len(agents_response.json()) == 6
    assert sum(1 for item in agents_response.json() if item["status"] == "running") == 3

    assert checkpoints_response.status_code == 200
    assert len(checkpoints_response.json()) == 2

    assert analytics_response.status_code == 200
    assert analytics_response.json()["summary"]["mergedChanges"] == 18

    assert activities_response.status_code == 200
    assert len(activities_response.json()) == 4

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == "pl-001"

    assert logs_response.status_code == 200
    assert len(logs_response.json()) >= 1


def test_frontend_mock_create_pipeline(tmp_path):
    client, _ = create_test_client(tmp_path)
    project_dir = tmp_path / "example-project"
    project_dir.mkdir()
    (project_dir / "package.json").write_text('{"name":"example-project"}', encoding="utf-8")
    (project_dir / "README.md").write_text("# Example Project", encoding="utf-8")
    (project_dir / "src").mkdir()
    (project_dir / "src" / "index.ts").write_text("console.log('hello')", encoding="utf-8")

    with client:
        create_response = client.post(
            "/api/pipelines",
            json={
                "projectPath": str(project_dir),
                "requirement": "在现有项目中实现用户收藏功能，并补充列表页。",
            },
        )

        assert create_response.status_code == 201
        created_pipeline = create_response.json()
        assert created_pipeline["status"] == "paused"
        assert created_pipeline["template"] == "新功能开发"
        assert created_pipeline["stages"][0]["status"] == "awaiting_review"
        assert created_pipeline["stages"][0]["isCheckpoint"] is True
        assert "需求文档" in created_pipeline["stages"][0]["output"]
        assert "项目目录扫描" in created_pipeline["stages"][0]["output"]
        assert "package.json" in created_pipeline["stages"][0]["output"]
        assert created_pipeline["projectPath"] == str(project_dir.resolve())
        assert "关键文件" in created_pipeline["projectSummary"]
        assert created_pipeline["requirementDocPath"] == str((project_dir / "main" / "requirements.md").resolve())

        detail_response = client.get(f"/api/pipelines/{created_pipeline['id']}")
        logs_response = client.get(f"/api/pipelines/{created_pipeline['id']}/logs")
        checkpoints_response = client.get("/api/checkpoints", params={"status": "pending"})

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == created_pipeline["id"]
    assert detail_response.json()["status"] == "paused"
    assert (project_dir / "main" / "requirements.md").exists()
    assert "收藏功能" in (project_dir / "main" / "requirements.md").read_text(encoding="utf-8")

    assert logs_response.status_code == 200
    assert any("工作目录" in log for log in logs_response.json())
    assert any("项目目录扫描完成" in log for log in logs_response.json())
    assert any("需求分析完成" in log for log in logs_response.json())
    assert any("需求文档已写入" in log for log in logs_response.json())
    assert any("等待审批" in log for log in logs_response.json())

    assert checkpoints_response.status_code == 200
    assert any(item["pipelineId"] == created_pipeline["id"] for item in checkpoints_response.json())


def test_frontend_mock_create_pipeline_rejects_invalid_project_path(tmp_path):
    client, _ = create_test_client(tmp_path)
    invalid_path = tmp_path / "missing-project"

    with client:
        create_response = client.post(
            "/api/pipelines",
            json={
                "projectPath": str(invalid_path),
                "requirement": "实现一个新的通知中心。",
            },
        )

    assert create_response.status_code == 400
    assert "项目目录不存在" in create_response.json()["detail"]


def test_approve_requirement_checkpoint_advances_pipeline(tmp_path):
    client, _ = create_test_client(tmp_path)
    project_dir = tmp_path / "approve-project"
    project_dir.mkdir()

    with client:
        create_response = client.post(
            "/api/pipelines",
            json={
                "projectPath": str(project_dir),
                "requirement": "实现一个自律应用的需求分析。",
            },
        )
        created_pipeline = create_response.json()
        checkpoint_id = f"cp-{created_pipeline['id']}-requirement_analysis"

        approve_response = client.post(f"/api/checkpoints/{checkpoint_id}/approve")
        detail_response = client.get(f"/api/pipelines/{created_pipeline['id']}")
        pending_checkpoints_response = client.get("/api/checkpoints", params={"status": "pending"})

    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    assert detail_response.status_code == 200
    updated_pipeline = detail_response.json()
    assert updated_pipeline["status"] == "paused"
    assert updated_pipeline["stages"][0]["status"] == "completed"
    assert updated_pipeline["stages"][1]["status"] == "awaiting_review"
    assert "技术方案文档" in updated_pipeline["stages"][1]["output"]
    assert (project_dir / "main" / "solution.md").exists()
    assert "创建计划" in (project_dir / "main" / "solution.md").read_text(encoding="utf-8")

    assert pending_checkpoints_response.status_code == 200
    assert all(item["id"] != checkpoint_id for item in pending_checkpoints_response.json())
    assert any(item["pipelineId"] == created_pipeline["id"] and item["stage"] == "方案设计" for item in pending_checkpoints_response.json())


def test_reject_requirement_checkpoint_marks_feedback(tmp_path):
    client, _ = create_test_client(tmp_path)
    project_dir = tmp_path / "reject-project"
    project_dir.mkdir()

    with client:
        create_response = client.post(
            "/api/pipelines",
            json={
                "projectPath": str(project_dir),
                "requirement": "实现一个自律应用的需求分析。",
            },
        )
        created_pipeline = create_response.json()
        checkpoint_id = f"cp-{created_pipeline['id']}-requirement_analysis"

        reject_response = client.post(
            f"/api/checkpoints/{checkpoint_id}/reject",
            json={"reason": "请补充更明确的提醒策略和数据指标定义。"},
        )
        detail_response = client.get(f"/api/pipelines/{created_pipeline['id']}")

    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"
    assert "提醒策略" in (reject_response.json()["rejectReason"] or "")

    assert detail_response.status_code == 200
    updated_pipeline = detail_response.json()
    assert updated_pipeline["status"] == "paused"
    assert updated_pipeline["stages"][0]["status"] == "rejected"


def test_approve_solution_checkpoint_generates_code(tmp_path):
    client, _ = create_test_client(tmp_path)
    project_dir = tmp_path / "coding-project"
    project_dir.mkdir()

    with client:
        create_response = client.post(
            "/api/pipelines",
            json={
                "projectPath": str(project_dir),
                "requirement": "实现一个自律应用的需求分析。",
            },
        )
        created_pipeline = create_response.json()

        requirement_checkpoint_id = f"cp-{created_pipeline['id']}-requirement_analysis"
        client.post(f"/api/checkpoints/{requirement_checkpoint_id}/approve")

        solution_checkpoint_id = f"cp-{created_pipeline['id']}-solution_design"
        approve_solution_response = client.post(f"/api/checkpoints/{solution_checkpoint_id}/approve")
        detail_response = client.get(f"/api/pipelines/{created_pipeline['id']}")
        checkpoints_response = client.get("/api/checkpoints", params={"status": "pending"})

    assert approve_solution_response.status_code == 200
    assert approve_solution_response.json()["status"] == "approved"

    assert detail_response.status_code == 200
    updated_pipeline = detail_response.json()
    assert updated_pipeline["status"] == "paused"
    assert updated_pipeline["stages"][1]["status"] == "completed"
    assert updated_pipeline["stages"][2]["status"] == "completed"
    assert updated_pipeline["stages"][3]["status"] == "completed"
    assert updated_pipeline["stages"][4]["status"] == "awaiting_review"
    assert "FastAPI()" in (updated_pipeline["stages"][2]["output"] or "")
    assert "测试报告" in (updated_pipeline["stages"][3]["output"] or "")
    assert "代码评审报告" in (updated_pipeline["stages"][4]["output"] or "")
    assert (project_dir / "app" / "main.py").exists()
    assert (project_dir / "requirements.txt").exists()
    assert (project_dir / "tests" / "test_app.py").exists()
    assert (project_dir / "main" / "test_report.md").exists()
    assert (project_dir / "main" / "review_report.md").exists()
    assert any(
        item["pipelineId"] == created_pipeline["id"] and item["stage"] == "代码评审"
        for item in checkpoints_response.json()
    )


def test_failing_test_stage_waits_for_approval_and_blocks_review(tmp_path):
    client, engine = create_test_client(tmp_path)
    engine.agents[StageType.TESTING] = FakeFailingTestAgent()
    project_dir = tmp_path / "failing-test-project"
    project_dir.mkdir()

    with client:
        create_response = client.post(
            "/api/pipelines",
            json={
                "projectPath": str(project_dir),
                "requirement": "实现一个自律应用并补齐测试。",
            },
        )
        created_pipeline = create_response.json()

        requirement_checkpoint_id = f"cp-{created_pipeline['id']}-requirement_analysis"
        client.post(f"/api/checkpoints/{requirement_checkpoint_id}/approve")

        solution_checkpoint_id = f"cp-{created_pipeline['id']}-solution_design"
        client.post(f"/api/checkpoints/{solution_checkpoint_id}/approve")

        detail_response = client.get(f"/api/pipelines/{created_pipeline['id']}")
        checkpoints_response = client.get("/api/checkpoints", params={"status": "pending"})

    assert detail_response.status_code == 200
    updated_pipeline = detail_response.json()
    assert updated_pipeline["status"] == "paused"
    assert updated_pipeline["stages"][2]["status"] == "completed"
    assert updated_pipeline["stages"][3]["status"] == "awaiting_review"
    assert updated_pipeline["stages"][4]["status"] == "idle"
    assert "测试报告" in (updated_pipeline["stages"][3]["output"] or "")
    assert (project_dir / "tests" / "test_app.py").exists()
    assert (project_dir / "main" / "test_report.md").exists()
    assert any(
        item["pipelineId"] == created_pipeline["id"] and item["stage"] == "测试生成"
        for item in checkpoints_response.json()
    )


def test_approve_review_checkpoint_moves_delivery_to_waiting_review(tmp_path):
    client, _ = create_test_client(tmp_path)
    project_dir = tmp_path / "delivery-project"
    project_dir.mkdir()

    with client:
        create_response = client.post(
            "/api/pipelines",
            json={
                "projectPath": str(project_dir),
                "requirement": "实现一个自律应用并完成交付。",
            },
        )
        created_pipeline = create_response.json()

        requirement_checkpoint_id = f"cp-{created_pipeline['id']}-requirement_analysis"
        client.post(f"/api/checkpoints/{requirement_checkpoint_id}/approve")

        solution_checkpoint_id = f"cp-{created_pipeline['id']}-solution_design"
        client.post(f"/api/checkpoints/{solution_checkpoint_id}/approve")

        review_checkpoint_id = f"cp-{created_pipeline['id']}-code_review"
        approve_review_response = client.post(f"/api/checkpoints/{review_checkpoint_id}/approve")
        detail_response = client.get(f"/api/pipelines/{created_pipeline['id']}")
        checkpoints_response = client.get("/api/checkpoints", params={"status": "pending"})

    assert approve_review_response.status_code == 200
    assert approve_review_response.json()["status"] == "approved"

    assert detail_response.status_code == 200
    updated_pipeline = detail_response.json()
    assert updated_pipeline["status"] == "paused"
    assert updated_pipeline["stages"][4]["status"] == "completed"
    assert updated_pipeline["stages"][5]["status"] == "awaiting_review"
    assert "交付汇总" in (updated_pipeline["stages"][5]["output"] or "")
    assert (project_dir / "main" / "delivery.md").exists()
    assert any(
        item["pipelineId"] == created_pipeline["id"] and item["stage"] == "交付集成"
        for item in checkpoints_response.json()
    )


def test_approve_delivery_checkpoint_completes_pipeline(tmp_path):
    client, _ = create_test_client(tmp_path)
    project_dir = tmp_path / "delivery-approve-project"
    project_dir.mkdir()

    with client:
        create_response = client.post(
            "/api/pipelines",
            json={
                "projectPath": str(project_dir),
                "requirement": "实现一个自律应用并完成交付。",
            },
        )
        created_pipeline = create_response.json()

        requirement_checkpoint_id = f"cp-{created_pipeline['id']}-requirement_analysis"
        client.post(f"/api/checkpoints/{requirement_checkpoint_id}/approve")

        solution_checkpoint_id = f"cp-{created_pipeline['id']}-solution_design"
        client.post(f"/api/checkpoints/{solution_checkpoint_id}/approve")

        review_checkpoint_id = f"cp-{created_pipeline['id']}-code_review"
        client.post(f"/api/checkpoints/{review_checkpoint_id}/approve")

        delivery_checkpoint_id = f"cp-{created_pipeline['id']}-delivery"
        approve_delivery_response = client.post(f"/api/checkpoints/{delivery_checkpoint_id}/approve")
        detail_response = client.get(f"/api/pipelines/{created_pipeline['id']}")

    assert approve_delivery_response.status_code == 200
    assert approve_delivery_response.json()["status"] == "approved"

    assert detail_response.status_code == 200
    updated_pipeline = detail_response.json()
    assert updated_pipeline["status"] == "completed"
    assert updated_pipeline["stages"][5]["status"] == "completed"


def test_requirement_agent_renders_markdown_document_from_structured_json():
    agent = RequirementAgent()

    async def fake_call_llm(*args, **kwargs):
        return """{
  "title": "收藏功能需求分析",
  "business_goals": ["提升用户留存", "支持用户管理感兴趣内容"],
  "functional_requirements": ["列表页展示收藏状态", "支持收藏与取消收藏"],
  "user_stories": ["作为用户，我希望在列表页快速收藏内容"],
  "acceptance_criteria": ["用户可以成功收藏和取消收藏目标内容"],
  "non_functional_requirements": ["接口响应时间应控制在 300ms 内"],
  "open_questions": ["是否需要支持批量收藏"],
  "modules": [
    {
      "module_name": "收藏状态展示",
      "priority": "P0",
      "description": "在列表页展示已收藏和未收藏两种状态。"
    }
  ]
}"""

    agent.call_llm = fake_call_llm
    output = asyncio.run(
        agent.execute(
            AgentInput(
                task_description="执行阶段: requirement_analysis",
                context={
                    "requirement_raw": "实现收藏与取消收藏能力",
                    "project_path": "/tmp/demo-project",
                    "project_summary": "## 项目目录扫描\n\n- 关键文件：package.json",
                },
            )
        )
    )

    assert output.success is True
    assert output.result["modules"][0]["module_name"] == "收藏状态展示"
    assert "# 需求文档" in output.result["document"]
    assert "## 功能清单" in output.result["document"]
    assert "package.json" in output.result["document"]
    assert "```json" in output.result["document"]


def test_solution_agent_renders_concise_solution_document():
    from src.agents.solution_agent import SolutionAgent

    agent = SolutionAgent()

    async def fake_call_llm(*args, **kwargs):
        return """{
  "title": "自律 App 技术方案",
  "architecture_overview": "前后端分离，移动端配合后端 API 提供能力。",
  "tech_stack": ["React Native", "FastAPI", "PostgreSQL"],
  "directory_structure": [
    {"path": "mobile/", "purpose": "移动端应用"},
    {"path": "backend/", "purpose": "服务端接口"}
  ],
  "api_design": [
    {
      "name": "创建计划",
      "method": "POST",
      "path": "/plans",
      "description": "创建每日计划",
      "request": "标题、日期、优先级",
      "response": "计划详情"
    }
  ],
  "data_models": [
    {
      "name": "Plan",
      "description": "每日计划实体",
      "fields": [
        {"name": "id", "type": "uuid", "required": true, "description": "计划 ID"}
      ]
    }
  ],
  "technical_rationale": ["React Native 适合跨平台快速交付"],
  "risks": ["提醒功能依赖系统通知权限"],
  "open_questions": ["是否支持 Apple Watch 通知"]
}"""

    requirement_doc = """# 需求文档

## 标题
自律 App

## 原始需求
写一个自律 app

## 业务目标
- 提升计划执行率

## 功能清单
- 每日计划
- 专注计时

## 验收标准
- 能创建计划

## 模块划分
### 每日计划（P0）
计划管理
"""

    agent.call_llm = fake_call_llm
    output = asyncio.run(
        agent.execute(
            AgentInput(
                task_description="执行阶段: solution_design",
                context={
                    "requirement_doc": requirement_doc,
                    "project_path": "/tmp/demo-project",
                    "project_summary": "## 项目目录扫描\n\n- 关键文件：package.json",
                },
            )
        )
    )

    assert output.success is True
    assert "# 技术方案文档" in output.result["design"]
    assert "## 需求摘要" in output.result["design"]
    assert "## 原始需求" not in output.result["design"]
    assert "## Stage3 使用的技术栈约束" in output.result["design"]
    assert "## Stage3 文件清单" in output.result["design"]
    assert "创建计划" in output.result["design"]


def test_code_agent_requires_file_plan_and_returns_multiple_files():
    from src.agents.code_agent import CodeAgent

    agent = CodeAgent()

    async def fake_call_llm(*args, **kwargs):
        main_py = base64.b64encode(
            b"from fastapi import FastAPI\n\napp = FastAPI()\n"
        ).decode("utf-8")
        requirements_txt = base64.b64encode(
            b"fastapi\nuvicorn\n"
        ).decode("utf-8")
        return """<file path="app/main.py">
<summary>FastAPI 入口</summary>
<content_base64>
__MAIN_PY__
</content_base64>
</file>
<file path="requirements.txt">
<summary>依赖定义</summary>
<content_base64>
__REQ_TXT__
</content_base64>
</file>""".replace("__MAIN_PY__", main_py).replace("__REQ_TXT__", requirements_txt)

    agent.call_llm = fake_call_llm
    output = asyncio.run(
        agent.execute(
            AgentInput(
                task_description="执行阶段: coding",
                context={
                    "requirement_doc": "# 需求文档",
                    "solution_doc": "# 技术方案文档",
                    "solution_structured": {
                        "resolved_stack": {
                            "frontend": "React Native",
                            "backend": "FastAPI",
                            "database": "SQLite",
                            "state_management": "Zustand",
                            "notifications": "Expo Notifications",
                            "testing": "pytest + vitest",
                        },
                        "file_plan": [
                            {
                                "path": "app/main.py",
                                "layer": "backend",
                                "purpose": "FastAPI 入口",
                                "must_generate": True,
                            },
                            {
                                "path": "requirements.txt",
                                "layer": "config",
                                "purpose": "依赖定义",
                                "must_generate": True,
                            },
                        ],
                    },
                },
            )
        )
    )

    assert output.success is True
    assert set(output.result["files"].keys()) == {"app/main.py", "requirements.txt"}


def test_code_agent_generates_required_files_in_batches():
    from src.agents.code_agent import CodeAgent

    agent = CodeAgent()
    agent.BATCH_SIZE = 2
    call_count = {"value": 0}

    async def fake_call_llm(message: str, **kwargs):
        call_count["value"] += 1
        if call_count["value"] == 1:
            main_py = base64.b64encode(
                b"from fastapi import FastAPI\n\napp = FastAPI()\n"
            ).decode("utf-8")
            return f"""<file path="app/main.py">
<summary>入口</summary>
<content_base64>
{main_py}
</content_base64>
</file>
"""

        if call_count["value"] == 2:
            router_py = base64.b64encode(
                b"from fastapi import APIRouter\n\nrouter = APIRouter()\n"
            ).decode("utf-8")
            return f"""<file path="app/router.py">
<summary>路由</summary>
<content_base64>
{router_py}
</content_base64>
</file>"""

        requirements_txt = base64.b64encode(
            b"fastapi\nuvicorn\n"
        ).decode("utf-8")
        return f"""<file path="requirements.txt">
<summary>依赖</summary>
<content_base64>
{requirements_txt}
</content_base64>
</file>"""

    agent.call_llm = fake_call_llm
    output = asyncio.run(
        agent.execute(
            AgentInput(
                task_description="执行阶段: coding",
                context={
                    "requirement_doc": "# 需求文档",
                    "solution_doc": "# 技术方案文档",
                    "solution_structured": {
                        "resolved_stack": {
                            "frontend": "React Native",
                            "backend": "FastAPI",
                            "database": "SQLite",
                            "state_management": "Zustand",
                            "notifications": "Expo Notifications",
                            "testing": "pytest + vitest",
                        },
                        "file_plan": [
                            {"path": "app/main.py", "layer": "backend", "purpose": "入口", "must_generate": True},
                            {"path": "app/router.py", "layer": "backend", "purpose": "路由", "must_generate": True},
                            {"path": "requirements.txt", "layer": "config", "purpose": "依赖", "must_generate": True},
                        ],
                    },
                },
            )
        )
    )

    assert output.success is True
    assert call_count["value"] == 3
    assert set(output.result["files"].keys()) == {"app/main.py", "app/router.py", "requirements.txt"}
