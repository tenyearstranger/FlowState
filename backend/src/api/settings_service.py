from __future__ import annotations

"""Service layer for application settings."""

import os
from urllib.parse import urlparse
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.config import LLMProvider, get_config
from src.llm_client import LLMClient, LLMMessage
from src.store.settings_store import SettingsStore


AGENT_STAGE_MAP = {
    "requirements-agent": "requirement_analysis",
    "architect-agent": "solution_design",
    "codegen-agent": "coding",
    "test-agent": "testing",
    "review-agent": "code_review",
    "delivery-agent": "delivery",
}

AGENT_ENV_PREFIX_MAP = {
    "requirements-agent": "FS_AGENT_REQUIREMENTS",
    "architect-agent": "FS_AGENT_ARCHITECT",
    "codegen-agent": "FS_AGENT_CODEGEN",
    "test-agent": "FS_AGENT_TEST",
    "review-agent": "FS_AGENT_REVIEW",
    "delivery-agent": "FS_AGENT_DELIVERY",
}


class SettingsService:
    def __init__(self, store: SettingsStore | None = None):
        self.store = store or SettingsStore()

    async def get_settings(self) -> dict[str, Any]:
        raw = await self.store.load()
        return self._build_response(raw)

    async def validate_llm_settings(self, agent_id: str | None, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_llm_payload(payload)
        self._validate_llm_payload_format(normalized)
        await self._test_llm_connectivity(normalized)

        return {
            "ok": True,
            "message": f"{agent_id or 'llm'} 连接测试成功",
            "provider": normalized["provider"],
            "model": normalized["model"],
        }

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

        agent_configs = payload.get("agentConfigs")
        if isinstance(agent_configs, dict):
            existing_agents = merged.get("agents", {})
            if not isinstance(existing_agents, dict):
                existing_agents = {}

            for agent_id, agent_value in agent_configs.items():
                if agent_id not in AGENT_STAGE_MAP or not isinstance(agent_value, dict):
                    continue
                current_agent = existing_agents.get(agent_id, {})
                if not isinstance(current_agent, dict):
                    current_agent = {}
                current_agent.update(
                    {
                        "provider": str(agent_value.get("provider") or current_agent.get("provider") or "").strip(),
                        "model": str(agent_value.get("model") or current_agent.get("model") or "").strip(),
                        "base_url": str(agent_value.get("baseUrl") or current_agent.get("base_url") or "").strip(),
                        "api_key": str(agent_value.get("apiKey") or current_agent.get("api_key") or "").strip(),
                    }
                )
                existing_agents[agent_id] = current_agent

            merged["agents"] = existing_agents

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
        self._sync_agent_env_file(merged)
        return self._build_response(merged)

    def _build_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        cfg = get_config()
        llm_raw = raw.get("llm") if isinstance(raw.get("llm"), dict) else {}
        agents_raw = raw.get("agents") if isinstance(raw.get("agents"), dict) else {}

        llm = {
            "provider": str(llm_raw.get("provider") or cfg.llm.provider.value),
            "model": str(llm_raw.get("model") or cfg.llm.model),
            "baseUrl": str(llm_raw.get("base_url") or cfg.llm.base_url),
            "apiKey": str(llm_raw.get("api_key") or cfg.llm.api_key),
        }

        agent_configs: dict[str, dict[str, str]] = {}
        for agent_id, stage_name in AGENT_STAGE_MAP.items():
            stage_cfg = cfg.stages.get(stage_name)
            stored_agent = agents_raw.get(agent_id, {}) if isinstance(agents_raw.get(agent_id), dict) else {}
            agent_configs[agent_id] = {
                "provider": str(
                    stored_agent.get("provider")
                    or getattr(stage_cfg, "provider_override", None)
                    or llm["provider"]
                ),
                "model": str(
                    stored_agent.get("model")
                    or getattr(stage_cfg, "model_override", None)
                    or llm["model"]
                ),
                "baseUrl": str(
                    stored_agent.get("base_url")
                    or getattr(stage_cfg, "base_url_override", None)
                    or llm["baseUrl"]
                ),
                "apiKey": str(
                    stored_agent.get("api_key")
                    or getattr(stage_cfg, "api_key_override", None)
                    or llm["apiKey"]
                ),
            }

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
            "llm": llm,
            "agentConfigs": agent_configs,
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

        agents = raw.get("agents") or {}
        for agent_id, stage_name in AGENT_STAGE_MAP.items():
            agent_cfg = agents.get(agent_id) if isinstance(agents, dict) else None
            if not isinstance(agent_cfg, dict):
                continue
            stage_cfg = cfg.stages.get(stage_name)
            if stage_cfg is None:
                continue
            stage_cfg.provider_override = str(agent_cfg.get("provider") or "").strip() or None
            stage_cfg.model_override = str(agent_cfg.get("model") or "").strip() or None
            stage_cfg.base_url_override = str(agent_cfg.get("base_url") or "").strip() or None
            stage_cfg.api_key_override = str(agent_cfg.get("api_key") or "").strip() or None

        pipeline = raw.get("pipeline") or {}
        max_retries = pipeline.get("maxAgentRetries")
        if isinstance(max_retries, int) and max_retries > 0:
            cfg.pipeline.max_retries_per_stage = max_retries

    def _normalize_llm_payload(self, payload: dict[str, Any]) -> dict[str, str]:
        return {
            "provider": str(payload.get("provider") or "").strip().lower(),
            "model": str(payload.get("model") or "").strip(),
            "base_url": str(payload.get("baseUrl") or payload.get("base_url") or "").strip(),
            "api_key": str(payload.get("apiKey") or payload.get("api_key") or "").strip(),
        }

    def _validate_llm_payload_format(self, payload: dict[str, str]) -> None:
        provider = payload["provider"]
        model = payload["model"]
        base_url = payload["base_url"]
        api_key = payload["api_key"]

        if not provider:
            raise ValueError("Provider 不能为空")
        try:
            LLMProvider(provider)
        except ValueError as exc:
            raise ValueError(f"不支持的 Provider: {provider}") from exc

        if not model:
            raise ValueError("Model 不能为空")

        if not base_url:
            raise ValueError("Base URL 不能为空")
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Base URL 格式无效，请填写完整的 http(s) 地址")

        if provider == LLMProvider.LOCAL.value:
            return

        if not api_key:
            raise ValueError("API Key 不能为空")
        if any(ch.isspace() for ch in api_key):
            raise ValueError("API Key 不能包含空白字符")

    async def _test_llm_connectivity(self, payload: dict[str, str]) -> None:
        client = LLMClient(
            {
                "provider": payload["provider"],
                "model": payload["model"],
                "base_url": payload["base_url"],
                "api_key": payload["api_key"],
                "max_tokens": 32,
                "temperature": 0.2,
            }
        )
        try:
            response = await client.chat(
                [
                    LLMMessage(
                        role="user",
                        content="请只回复 TEST_OK",
                    )
                ],
                system_prompt="你是一个连接测试助手。请只输出 TEST_OK。",
            )
        except Exception as exc:
            raise ValueError(f"连通性测试失败: {exc}") from exc

        if not response.content or "TEST_OK" not in response.content.upper():
            raise ValueError("连通性测试失败: 模型返回结果异常")

    def _sync_agent_env_file(self, raw: dict[str, Any]) -> None:
        resolved = self._build_response(raw)
        llm = resolved.get("llm") or {}
        env_values = {
            "FS_LLM_PROVIDER": str(llm.get("provider") or "").strip(),
            "FS_LLM_MODEL": str(llm.get("model") or "").strip(),
            "FS_LLM_BASE_URL": str(llm.get("baseUrl") or "").strip(),
            "FS_LLM_API_KEY": str(llm.get("apiKey") or "").strip(),
        }

        agent_configs = resolved.get("agentConfigs") or {}
        for agent_id, env_prefix in AGENT_ENV_PREFIX_MAP.items():
            agent_cfg = agent_configs.get(agent_id) or {}
            env_values[f"{env_prefix}_PROVIDER"] = str(agent_cfg.get("provider") or "").strip()
            env_values[f"{env_prefix}_MODEL"] = str(agent_cfg.get("model") or "").strip()
            env_values[f"{env_prefix}_BASE_URL"] = str(agent_cfg.get("baseUrl") or "").strip()
            env_values[f"{env_prefix}_API_KEY"] = str(agent_cfg.get("apiKey") or "").strip()

        configured_env_path = os.getenv("FS_ENV_FILE_PATH", "").strip()
        env_path = (
            Path(configured_env_path)
            if configured_env_path
            else Path(__file__).resolve().parents[2] / ".env"
        )
        legacy_env_path = env_path.with_name(".env.local")
        env_path.parent.mkdir(parents=True, exist_ok=True)
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
        if legacy_env_path.exists() and legacy_env_path != env_path:
            legacy_env_path.unlink()
