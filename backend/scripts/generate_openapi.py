from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
DOCS_ROOT = BACKEND_ROOT / "docs"
JSON_PATH = DOCS_ROOT / "openapi.json"
YAML_PATH = DOCS_ROOT / "openapi.yaml"


def build_spec() -> dict:
    sys.path.insert(0, str(BACKEND_ROOT))

    from src.api.app import app

    spec = app.openapi()
    spec["servers"] = [
        {
            "url": "http://127.0.0.1:8000",
            "description": "Local development server",
        },
        {
            "url": "http://localhost:8000",
            "description": "Alternate local development server",
        },
    ]
    spec["tags"] = [
        {"name": "meta", "description": "API root metadata endpoints."},
        {"name": "health", "description": "Health and readiness checks."},
        {
            "name": "pipelines-ui",
            "description": "Frontend-facing pipeline endpoints used by the Electron/Vite app.",
        },
        {
            "name": "pipelines",
            "description": "Canonical v1 pipeline CRUD and lifecycle endpoints.",
        },
        {"name": "checkpoints", "description": "Human approval and rejection workflow endpoints."},
        {"name": "agents", "description": "Agent status, model, and usage summary endpoints."},
        {"name": "analytics", "description": "Dashboard and observability aggregation endpoints."},
        {"name": "activities", "description": "Recent activity feed endpoints."},
        {"name": "git", "description": "Pipeline-scoped Git status, diff, and cleanup endpoints."},
        {"name": "settings", "description": "Application and per-agent configuration endpoints."},
    ]
    return spec


def write_spec(spec: dict) -> None:
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    YAML_PATH.write_text(
        yaml.safe_dump(spec, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def main() -> None:
    spec = build_spec()
    write_spec(spec)
    print(f"Wrote {JSON_PATH}")
    print(f"Wrote {YAML_PATH}")


if __name__ == "__main__":
    main()
