from __future__ import annotations

"""Pipeline 状态持久化存储"""

import json
import os
from typing import Optional, List
from src.models.pipeline import Pipeline


class StateStore:
    """Pipeline 状态持久化存储（当前使用本地 JSON 文件）"""

    def __init__(self, storage_dir: str | None = None):
        from src.config import get_config
        self.storage_dir = storage_dir or get_config().pipeline.storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    async def save(self, pipeline: Pipeline) -> None:
        filepath = self._get_path(pipeline.id)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(pipeline.model_dump_json(indent=2))

    async def load(self, pipeline_id: str) -> Optional[Pipeline]:
        filepath = self._get_path(pipeline_id)
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return Pipeline.model_validate_json(f.read())

    async def list_pipelines(self) -> List[Pipeline]:
        pipelines = []
        for fname in os.listdir(self.storage_dir):
            if fname.endswith(".json"):
                with open(
                    os.path.join(self.storage_dir, fname), "r", encoding="utf-8"
                ) as f:
                    pipelines.append(Pipeline.model_validate_json(f.read()))
        return sorted(pipelines, key=lambda p: p.created_at, reverse=True)

    async def delete(self, pipeline_id: str) -> None:
        filepath = self._get_path(pipeline_id)
        if os.path.exists(filepath):
            os.remove(filepath)

    def _get_path(self, pipeline_id: str) -> str:
        return os.path.join(self.storage_dir, f"{pipeline_id}.json")
