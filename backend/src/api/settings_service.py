from __future__ import annotations

"""Service layer for application settings."""

from copy import deepcopy
from pathlib import Path
from typing import Any

from src.config import LLMProvider, get_config
from src.store.settings_store import SettingsStore


class SettingsService:
    def __init__(self, store: SettingsStore | None = None):
        self.store = store or SettingsStore()

    async def get_settings(self) -> dict[str, Any]:
        raw = await self.store.load()
        return self._build_response(raw)

    async def save_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        current = await self.store.load()
        merged = deepcopy(current)

        llm_value = payload.get("llm")
        if isinstance(llm_value, dict):
            existing_llm = merged.get("llm", {})
            if not isinstance(existing_llm, dict):
                existing_llm = {}
            existing_llm.update(
                {
                    "provider": str(llm_value.get("provider") or existing_llm.get("provider") or "deepseek").strip(),
                    "model": str(llm_value.get("model") or existing_llm.get("model") or "").strip(),
                    "base_url": str(llm_value.get("baseUrl") or existing_llm.get("base_url") or "").strip(),
                    "api_key": str(llm_value.get("apiKey") or existing_llm.get("api_key") or "").strip(),
                }
            )
            merged["llm"] = existing_llm

        for section in ("pipeline", "general"):
            section_value = payload.get(section)
            if isinstance(section_value, dict):
                existing = merged.get(section, {})
                if not isinstance(existing, dict):
                    existing = {}
                existing.update(section_value)
                merged[section] = existing

        await self.store.save(merged)
        self._apply_runtime_config(merged)
        self._sync_local_env_file(merged)
        return self._build_response(merged)

    def _build_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        cfg = get_config()
        llm_raw = raw.get("llm") if isinstance(raw.get("llm"), dict) else {}

        pipeline_defaults = {
            "defaultProvider": cfg.llm.provider.value,
            "maxAgentRetries": cfg.pipeline.max_retries_per_stage,
            "checkpointTimeoutMinutes": 60,
            "autoCreateBranch": True,
            "autoCommitCode": True,
            "autoCreateMR": True,
            "branchNamePattern": "devflow/{pipeline-id}-{slug}",
            "repositoryPath": "./src",
            "semanticIndex": False,
        }
        general_defaults = {
            "checkpointNotifications": True,
            "pipelineCompleteNotifications": True,
            "agentFailureAlerts": True,
            "logRetentionDays": "7",
            "anonymousUsageStats": False,
            "appVersion": "v0.1.0-alpha",
            "engineVersion": "v0.1.0",
            "apiVersion": "v1",
        }

        pipeline = pipeline_defaults | {
            key: value for key, value in (raw.get("pipeline") or {}).items() if value is not None
        }
        general = general_defaults | {
            key: value for key, value in (raw.get("general") or {}).items() if value is not None
        }

        return {
            "llm": {
                "provider": str(llm_raw.get("provider") or cfg.llm.provider.value),
                "model": str(llm_raw.get("model") or cfg.llm.model),
                "baseUrl": str(llm_raw.get("base_url") or cfg.llm.base_url),
                "apiKey": str(llm_raw.get("api_key") or cfg.llm.api_key),
            },
            "pipeline": pipeline,
            "general": general,
        }

    def _apply_runtime_config(self, raw: dict[str, Any]) -> None:
        cfg = get_config()
        llm = raw.get("llm") or {}
        provider = str(llm.get("provider") or cfg.llm.provider.value).lower()
        try:
            cfg.llm.provider = LLMProvider(provider)
        except ValueError:
            pass
        cfg.llm.model = str(llm.get("model") or cfg.llm.model).strip() or cfg.llm.model
        cfg.llm.base_url = str(llm.get("base_url") or cfg.llm.base_url).strip()
        cfg.llm.api_key = str(llm.get("api_key") or cfg.llm.api_key).strip()

        pipeline = raw.get("pipeline") or {}
        max_retries = pipeline.get("maxAgentRetries")
        if isinstance(max_retries, int) and max_retries > 0:
            cfg.pipeline.max_retries_per_stage = max_retries

    def _sync_local_env_file(self, raw: dict[str, Any]) -> None:
        llm = raw.get("llm") or {}
        env_values = {
            "FS_LLM_PROVIDER": str(llm.get("provider") or "").strip(),
            "FS_LLM_MODEL": str(llm.get("model") or "").strip(),
            "FS_LLM_BASE_URL": str(llm.get("base_url") or "").strip(),
            "FS_LLM_API_KEY": str(llm.get("api_key") or "").strip(),
        }

        env_path = Path(__file__).resolve().parents[2] / ".env.local"
        existing_lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
        updated_lines: list[str] = []
        seen_keys: set[str] = set()

        for line in existing_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in line:
                updated_lines.append(line)
                continue

            key, _ = line.split("=", 1)
            key = key.strip()
            if key in env_values:
                updated_lines.append(f"{key}={env_values[key]}")
                seen_keys.add(key)
            else:
                updated_lines.append(line)

        for key, value in env_values.items():
            if key not in seen_keys:
                updated_lines.append(f"{key}={value}")

        env_path.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")
