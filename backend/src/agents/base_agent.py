from __future__ import annotations

"""Agent 基类定义"""

import json
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List
from pydantic import BaseModel
from src.config import get_config, get_stage_config
from src.llm_client import LLMClient, LLMMessage


class AgentInput(BaseModel):
    """Agent 输入"""
    task_description: str
    context: Dict[str, Any]
    human_feedback: Optional[str] = None


class AgentOutput(BaseModel):
    """Agent 输出"""
    success: bool
    result: Dict[str, Any]
    summary: str
    details: Optional[str] = None
    needs_human_review: bool = False


class BaseAgent(ABC):
    """所有 Agent 的基类"""

    def __init__(self, model_name: str | None = None, stage_type: str | None = None):
        """
        Args:
            model_name: 模型名称，不传则从全局配置读取
            stage_type: 阶段类型标识，如 "requirement_analysis"，
                        用于读取该阶段的专用配置
        """
        self.stage_type = stage_type or self._guess_stage_type()
        self.stage_config = get_stage_config(self.stage_type)
        cfg = get_config()

        # 模型名称优先级：构造参数 > 阶段配置 > 全局配置
        if model_name:
            self.model_name = model_name
        elif self.stage_config.model_override:
            self.model_name = self.stage_config.model_override
        else:
            self.model_name = cfg.llm.model

        self.temperature = (
            self.stage_config.temperature_override
            or cfg.llm.temperature
        )
        self.system_prompt = self.stage_config.system_prompt

        # LLM 客户端（惰性初始化）
        self._llm_client: Optional[LLMClient] = None

    def _guess_stage_type(self) -> str:
        """从类名推断阶段类型"""
        name = type(self).__name__.replace("Agent", "").lower()
        mapping = {
            "requirement": "requirement_analysis",
            "solution": "solution_design",
            "code": "coding",
            "test": "testing",
            "review": "code_review",
            "delivery": "delivery",
        }
        for key, val in mapping.items():
            if key in name:
                return val
        return name

    # ========================================================================
    # LLM 调用封装
    # ========================================================================

    def _get_llm_client(self) -> LLMClient:
        """获取 LLM 客户端（按需创建）"""
        if self._llm_client is None:
            overrides = {}
            if self.stage_config.model_override:
                overrides["model"] = self.stage_config.model_override
            if self.stage_config.temperature_override:
                overrides["temperature"] = self.stage_config.temperature_override

            self._llm_client = LLMClient(
                config_override=overrides if overrides else None
            )
        return self._llm_client

    async def call_llm(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        expect_json: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        """
        调用 LLM 的统一入口

        Args:
            user_message: 用户消息（当前阶段的任务描述 + 上下文）
            system_prompt: 系统提示词，默认使用 stage_config 中的
            expect_json: 是否期望 JSON 格式响应
            temperature: 温度参数，覆盖默认值

        Returns:
            LLM 响应的文本内容
        """
        client = self._get_llm_client()
        messages = [
            LLMMessage(role="user", content=user_message),
        ]

        actual_system_prompt = system_prompt or self.system_prompt
        temp = temperature if temperature is not None else self.temperature

        # 设置临时 temperature
        if temp != client.temperature:
            client.temperature = temp

        if expect_json:
            result = await client.chat_json(
                messages=messages,
                system_prompt=actual_system_prompt,
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            resp = await client.chat(
                messages=messages,
                system_prompt=actual_system_prompt,
            )
            return resp.content

    # ========================================================================
    # 抽象方法
    # ========================================================================

    @abstractmethod
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """执行 Agent 任务"""
        pass

    def can_auto_approve(self, output: AgentOutput) -> bool:
        """是否可自动通过（无需人类确认）"""
        return not output.needs_human_review
