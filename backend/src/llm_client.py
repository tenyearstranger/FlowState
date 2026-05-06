"""
FlowState LLM 客户端

支持所有 OpenAI 兼容的 API（DeepSeek、OpenRouter、vLLM 等）。
底层使用 openai.OpenAI SDK，而非原生 httpx。
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from openai import OpenAI

from src.config import get_config, LLMProvider

logger = logging.getLogger(__name__)

# ============================================================================
# 常量
# ============================================================================

# 各提供商的默认 API 端点（与 OpenAI SDK 配合使用）
DEFAULT_BASE_URLS: Dict[LLMProvider, str] = {
    LLMProvider.OPENAI: "https://api.openai.com/v1",
    LLMProvider.DEEPSEEK: "https://api.deepseek.com",
    LLMProvider.KIMI: "https://api.moonshot.cn/v1",
    LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
    LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
    LLMProvider.LOCAL: "http://localhost:11434/v1",  # Ollama
}

# 各提供商的默认模型
DEFAULT_MODELS: Dict[LLMProvider, str] = {
    LLMProvider.OPENAI: "gpt-4",
    LLMProvider.DEEPSEEK: "deepseek-chat",
    LLMProvider.KIMI: "kimi-k2.5",
    LLMProvider.ANTHROPIC: "claude-3-opus-20240229",
    LLMProvider.OPENROUTER: "openai/gpt-4",
    LLMProvider.LOCAL: "llama3",
}

# 停止词策略，避免截断过早（参考 generator_api.py）
EOS: List[str] = [
    "<|endoftext|>",
    "<|endofmask|>",
    "</s>",
    "\nif __name__",
    "\ndef main(",
]


# ============================================================================
# 消息模型
# ============================================================================

@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    finish_reason: str = "stop"
    usage: Optional[Dict[str, int]] = None
    model: str = ""


def trim_by_eos(text: str, eos_list: List[str]) -> str:
    """在首个停止词处截断生成文本。"""
    cut = len(text)
    for stop in eos_list:
        idx = text.find(stop)
        if idx != -1:
            cut = min(cut, idx)
    return text[:cut]


def sanitize_code_output(text: str) -> str:
    """剥离 ```python ... ``` 等 Markdown 代码围栏，避免语法错误。"""
    import re
    fenced = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
    if fenced:
        return fenced.groups()[-1].strip()
    unfenced = text.replace("```", "").strip()
    unfenced = re.sub(r"^\s*(python|py)\s*\n", "", unfenced, flags=re.IGNORECASE)
    return unfenced


# ============================================================================
# LLM 客户端
# ============================================================================

class LLMClient:
    """
    统一 LLM 调用客户端（基于 openai.OpenAI SDK）

    支持任何 OpenAI 兼容的 API，包括：
    - OpenAI
    - DeepSeek
    - OpenRouter
    - Azure OpenAI
    - 本地部署（Ollama、vLLM、LocalAI 等）

    用法：
        client = LLMClient()
        resp = await client.chat([
            LLMMessage(role="system", content="..."),
            LLMMessage(role="user", content="..."),
        ])
        print(resp.content)
    """

    def __init__(self, config_override: Optional[Dict] = None):
        """
        Args:
            config_override: 可选，临时覆盖配置
                例如: {"provider": "deepseek", "model": "deepseek-chat"}
        """
        self.cfg = get_config()
        self._override = config_override or {}
        self._client: Optional[OpenAI] = None

        # 解析配置
        provider_str = self._override.get("provider") or self.cfg.llm.provider.value
        self.provider = LLMProvider(provider_str) if isinstance(provider_str, str) else provider_str
        self.model = self._override.get("model") or self.cfg.llm.model or DEFAULT_MODELS.get(self.provider, "gpt-4")
        self.temperature = float(self._override.get("temperature", self.cfg.llm.temperature))
        self.max_tokens = int(self._override.get("max_tokens", self.cfg.llm.max_tokens))
        self.top_p = float(self._override.get("top_p", 0.95))

        # API Key
        self.api_key = (
            self._override.get("api_key")
            or self.cfg.llm.api_key
            or self.cfg.llm.resolve_api_key()
        )

        # Base URL
        self.base_url = (
            self._override.get("base_url")
            or self.cfg.llm.base_url
            or DEFAULT_BASE_URLS.get(self.provider, "")
        )

    def _get_client(self) -> OpenAI:
        """获取（或创建） OpenAI 客户端"""
        if self._client is None:
            kwargs: Dict[str, Any] = {
                "api_key": self.api_key,
                "base_url": self.base_url,
            }
            if self.provider == LLMProvider.OPENROUTER:
                kwargs["default_headers"] = {
                    "HTTP-Referer": "https://flowstate.dev",
                    "X-Title": "FlowState",
                }
            self._client = OpenAI(**kwargs)
        return self._client

    def _build_extra_body(self) -> Optional[Dict[str, Any]]:
        """
        构建 extra_body 参数。
        对于 DeepSeek 推理模型，需要传入 thinking 控制参数。
        """
        if self.provider == LLMProvider.DEEPSEEK and "reasoner" in self.model:
            return {"thinking": {"type": "enabled"}}
        return None

    def _resolve_temperature(self) -> float:
        """
        Kimi 的 kimi-k2.6 当前只接受 temperature=1。
        """
        if self.provider == LLMProvider.KIMI and self.model.startswith("kimi-k2.6"):
            return 1.0
        return self.temperature

    def _resolve_stop_tokens(self) -> Optional[List[str]]:
        """
        Kimi 的 kimi-k2.6 当前与 stop 参数组合时会返回空 content。
        """
        if self.provider == LLMProvider.KIMI and self.model.startswith("kimi-k2.6"):
            return None
        return EOS

    async def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict] = None,
    ) -> LLMResponse:
        """
        调用 LLM Chat API

        Args:
            messages: 对话消息列表
            system_prompt: 可选的系统提示词（会作为首个 system 消息插入）
            response_format: 响应格式，如 {"type": "json_object"}

        Returns:
            LLMResponse 包含响应内容
        """
        # 构建消息列表
        api_messages: List[Dict[str, str]] = []

        # 插入系统提示词
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})

        # 添加用户/助手消息
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        # 构建 OpenAI SDK 参数
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
            "temperature": self._resolve_temperature(),
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }
        stop_tokens = self._resolve_stop_tokens()
        if stop_tokens:
            kwargs["stop"] = stop_tokens
        if response_format:
            kwargs["response_format"] = response_format

        # 仅推理模型需要传入 extra_body
        extra_body = self._build_extra_body()
        if extra_body is not None:
            kwargs["extra_body"] = extra_body

        # 调用 API
        client = self._get_client()
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                **kwargs,
            )
        except Exception as e:
            logger.error(f"LLM API 调用失败 (model={self.model}): {e}")
            raise

        choice = response.choices[0]
        usage = response.usage

        raw_content = choice.message.content or ""

        # 截断和清洗
        trimmed = trim_by_eos(raw_content, EOS)
        content = sanitize_code_output(trimmed.strip())

        return LLMResponse(
            content=content,
            finish_reason=choice.finish_reason or "stop",
            usage={
                "prompt_tokens": usage.prompt_tokens or 0,
                "completion_tokens": usage.completion_tokens or 0,
                "total_tokens": usage.total_tokens or 0,
            } if usage else None,
            model=response.model or self.model,
        )

    async def chat_json(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
    ) -> dict:
        """
        调用 LLM 并期望返回 JSON

        会自动设置 response_format 为 json_object
        """
        resp = await self.chat(
            messages=messages,
            system_prompt=system_prompt,
            response_format={"type": "json_object"},
        )
        parsed = self._parse_json_with_fallbacks(resp.content)
        if parsed is not None:
            return parsed

        # 最后尝试让模型修复 JSON（仅返回对象）
        repaired = await self.chat(
            messages=[
                LLMMessage(
                    role="user",
                    content=(
                        "将下面文本修复为一个严格合法的 JSON 对象。"
                        "只输出 JSON 对象本身，不要解释。\n\n"
                        f"{resp.content}"
                    ),
                )
            ],
            system_prompt="你是 JSON 修复器。输出必须是合法 JSON 对象。",
            response_format={"type": "json_object"},
        )
        parsed = self._parse_json_with_fallbacks(repaired.content)
        if parsed is not None:
            return parsed

        preview = resp.content.strip().replace("\n", "\\n")[:400]
        raise ValueError(f"LLM 返回内容无法解析为 JSON 对象，预览: {preview}")

    async def close(self):
        """关闭客户端（openai SDK 无需手动关闭）"""
        self._client = None

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _parse_json_with_fallbacks(self, text: str) -> Optional[dict]:
        candidates: list[str] = []
        raw = text.strip()
        if raw:
            candidates.append(raw)

        extracted = self._extract_json(raw)
        if extracted and extracted not in candidates:
            candidates.append(extracted)

        fenced = self._extract_json_from_fence(raw)
        if fenced and fenced not in candidates:
            candidates.append(fenced)

        for candidate in candidates:
            parsed = self._try_load_json_object(candidate)
            if parsed is not None:
                return parsed
        return None

    @staticmethod
    def _try_load_json_object(text: str) -> Optional[dict]:
        variants = [text]
        sanitized = LLMClient._sanitize_json_text(text)
        if sanitized != text:
            variants.append(sanitized)

        for variant in variants:
            try:
                parsed = json.loads(variant)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    @staticmethod
    def _sanitize_json_text(text: str) -> str:
        cleaned = text.strip().lstrip("\ufeff")
        # 去掉对象/数组中的尾逗号
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
        return cleaned

    @staticmethod
    def _extract_json_from_fence(text: str) -> Optional[str]:
        fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            return fenced.group(1).strip()
        return None

    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """从文本中提取 JSON 对象"""
        stack = []
        start = -1
        in_string = False
        escape_next = False
        for i, ch in enumerate(text):
            if escape_next:
                escape_next = False
                continue

            if ch == "\\":
                escape_next = True
                continue

            if ch == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if ch in ("{", "["):
                if not stack:
                    start = i
                stack.append(ch)
            elif ch in ("}", "]"):
                if stack:
                    expected = "{" if ch == "}" else "["
                    if stack[-1] == expected:
                        stack.pop()
                        if not stack:
                            return text[start: i + 1]
        return None


# ============================================================================
# 便捷工厂方法
# ============================================================================

def create_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> LLMClient:
    """
    快速创建 LLM 客户端

    Usage:
        client = create_llm_client("deepseek", "deepseek-chat")
        client = create_llm_client("openai", "gpt-4", "sk-xxx")
    """
    overrides = {}
    if provider:
        overrides["provider"] = provider
    if model:
        overrides["model"] = model
    if api_key:
        overrides["api_key"] = api_key
    overrides.update(kwargs)
    return LLMClient(config_override=overrides if overrides else None)
