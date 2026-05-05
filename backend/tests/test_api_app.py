from fastapi.testclient import TestClient

from src.api.app import create_app
from src.bootstrap import create_engine
from src.models.pipeline import PipelineStatus
from src.store.state_store import StateStore


def create_test_client(tmp_path):
    engine = create_engine(StateStore(storage_dir=str(tmp_path)))
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
