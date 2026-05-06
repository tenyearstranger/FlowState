from __future__ import annotations

"""Service layer for application settings."""

from copy import deepcopy
from typing import Any

from src.config import LLMProvider, get_config
from src.store.settings_store import SettingsStore


DEFAULT_PROVIDER_META: list[dict[str, Any]] = [
    {
        "id": "openai",
        "name": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "color": "#74AA9C",
    },
    {
        "id": "anthropic",
        "name": "Anthropic",
        "models": ["claude-3-7-sonnet", "claude-3-5-haiku", "claude-3-opus"],
        "color": "#D4A96A",
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "models": ["deepseek-chat", "deepseek-coder"],
        "color": "#6B9FFF",
    },
    {
        "id": "qwen",
        "name": "通义千问 (Qwen)",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo"],
        "color": "#FF7A5C",
    },
]


def _mask_api_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "•" * len(value)
    return f"{value[:6]}{'•' * max(4, len(value) - 10)}{value[-4:]}"


class SettingsService:
    def __init__(self, store: SettingsStore | None = None):
        self.store = store or SettingsStore()

    async def get_settings(self) -> dict[str, Any]:
        raw = await self.store.load()
        return self._build_response(raw)

    async def save_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        current = await self.store.load()
        merged = deepcopy(current)

        providers = payload.get("providers", [])
        if isinstance(providers, list):
            provider_map = {item["id"]: deepcopy(item) for item in merged.get("providers", []) if isinstance(item, dict) and item.get("id")}
            for provider in providers:
                if not isinstance(provider, dict) or not provider.get("id"):
                    continue
                existing = provider_map.get(provider["id"], {"id": provider["id"]})
                existing["active"] = bool(provider.get("active", existing.get("active", False)))
                if "apiKey" in provider:
                    existing["api_key"] = str(provider.get("apiKey") or "").strip()
                provider_map[provider["id"]] = existing
            merged["providers"] = list(provider_map.values())

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
        return self._build_response(merged)

    def _build_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        cfg = get_config()
        persisted_providers = {
            item.get("id"): item
            for item in raw.get("providers", [])
            if isinstance(item, dict) and item.get("id")
        }

        providers: list[dict[str, Any]] = []
        for meta in DEFAULT_PROVIDER_META:
            persisted = persisted_providers.get(meta["id"], {})
            api_key = str(persisted.get("api_key") or "")
            is_current = cfg.llm.provider.value == meta["id"]
            providers.append(
                {
                    **meta,
                    "active": bool(persisted.get("active", is_current)),
                    "hasKey": bool(api_key),
                    "maskedKey": _mask_api_key(api_key),
                }
            )

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
            "providers": providers,
            "pipeline": pipeline,
            "general": general,
        }

    def _apply_runtime_config(self, raw: dict[str, Any]) -> None:
        cfg = get_config()
        pipeline = raw.get("pipeline") or {}
        default_provider = str(pipeline.get("defaultProvider") or cfg.llm.provider.value).lower()
        try:
            cfg.llm.provider = LLMProvider(default_provider)
        except ValueError:
            pass

        max_retries = pipeline.get("maxAgentRetries")
        if isinstance(max_retries, int) and max_retries > 0:
            cfg.pipeline.max_retries_per_stage = max_retries

