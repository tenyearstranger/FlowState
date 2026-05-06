from __future__ import annotations

"""Application settings persistence."""

import json
import os
from typing import Any


class SettingsStore:
    """Persist app settings in a local JSON file."""

    def __init__(self, filepath: str | None = None):
        self.filepath = filepath or os.getenv("FS_SETTINGS_PATH", ".flowstate_settings.json")

    async def load(self) -> dict[str, Any]:
        if not os.path.exists(self.filepath):
            return {}
        with open(self.filepath, "r", encoding="utf-8") as handle:
            return json.load(handle)

    async def save(self, payload: dict[str, Any]) -> None:
        parent = os.path.dirname(self.filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
