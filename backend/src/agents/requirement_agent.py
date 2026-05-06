"""需求分析 Agent"""

from __future__ import annotations

import json
from typing import Any

from .base_agent import BaseAgent, AgentInput, AgentOutput


class RequirementAgent(BaseAgent):
    """
    需求分析 Agent
    职责：解析用户输入的原始需求，输出结构化 PRD 文档
    """

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        raw = input_data.context.get("requirement_raw", "")
        project_path = input_data.context.get("project_path", "")
        project_summary = input_data.context.get("project_summary", "")
        feedback = input_data.human_feedback

        structured_payload, token_usage, model = await self._generate_structured_payload(
            raw=raw,
            project_path=project_path,
            project_summary=project_summary,
            feedback=feedback,
        )
        modules = self._normalize_modules(structured_payload.get("modules"))
        structured_payload["modules"] = modules
        structured_doc = self._render_markdown(
            payload=structured_payload,
            raw_requirement=raw,
            project_path=project_path,
            project_summary=project_summary,
        )

        return AgentOutput(
            success=True,
            result={
                "document": structured_doc,
                "raw_requirement": raw,
                "modules": modules,
                "structured_requirement": structured_payload,
            },
            summary=f"需求分析完成，识别出 {len(modules)} 个功能模块",
            details=structured_doc,
            needs_human_review=True,
            token_usage=token_usage,
            model=model,
        )

    async def _generate_structured_payload(
        self,
        *,
        raw: str,
        project_path: str,
        project_summary: str,
        feedback: str | None,
    ) -> tuple[dict[str, Any], dict[str, int] | None, str]:
        user_message = f"""请结合项目上下文分析以下原始需求，并返回结构化 JSON 对象。

原始需求：
{raw}

项目目录：
{project_path or "未提供"}

项目扫描摘要：
{project_summary or "未提供项目扫描摘要"}

请返回一个 JSON 对象，字段要求如下：
- "title": 需求标题，字符串
- "business_goals": 字符串数组
- "functional_requirements": 字符串数组
- "user_stories": 字符串数组
- "acceptance_criteria": 字符串数组
- "non_functional_requirements": 字符串数组
- "open_questions": 字符串数组
- "modules": 对象数组，每项包含：
  - "module_name": 字符串
  - "priority": "P0" | "P1" | "P2"
  - "description": 字符串

输出约束：
- 只返回 JSON 对象，不要返回 Markdown，不要解释
- 字段缺失时请返回空数组或空字符串，不要省略字段
- 请先在内部完成单 Agent 的逐步推理与需求拆解，但最终不要暴露推理过程
"""

        if feedback:
            user_message += f"\n\n根据以下反馈修改：\n{feedback}"

        parsed, response = await self.call_llm_json_response(
            user_message,
            temperature=0.1,
        )
        if not isinstance(parsed, dict):
            raise ValueError("需求分析模型返回的结构不是 JSON 对象")
        return parsed, response.usage, response.model

    # -------- 辅助方法 --------

    def _normalize_modules(self, modules: Any) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        if not isinstance(modules, list):
            return normalized

        for item in modules:
            if not isinstance(item, dict):
                continue
            module_name = str(
                item.get("module_name")
                or item.get("name")
                or item.get("title")
                or ""
            ).strip()
            priority = str(item.get("priority") or "P1").strip().upper()
            description = str(item.get("description") or "").strip()
            if not module_name:
                continue
            if priority not in {"P0", "P1", "P2"}:
                priority = "P1"
            normalized.append(
                {
                    "module_name": module_name,
                    "priority": priority,
                    "description": description,
                }
            )
        return normalized

    def _render_markdown(
        self,
        *,
        payload: dict[str, Any],
        raw_requirement: str,
        project_path: str,
        project_summary: str,
    ) -> str:
        title = str(payload.get("title") or "需求分析文档").strip() or "需求分析文档"
        business_goals = self._normalize_string_list(payload.get("business_goals"))
        functional_requirements = self._normalize_string_list(payload.get("functional_requirements"))
        user_stories = self._normalize_string_list(payload.get("user_stories"))
        acceptance_criteria = self._normalize_string_list(payload.get("acceptance_criteria"))
        non_functional_requirements = self._normalize_string_list(
            payload.get("non_functional_requirements")
        )
        open_questions = self._normalize_string_list(payload.get("open_questions"))
        modules = self._normalize_modules(payload.get("modules"))

        sections = [
            "# 需求文档",
            "",
            f"## 标题\n{title}",
            "",
            "## 原始需求",
            raw_requirement or "未提供原始需求。",
            "",
            "## 项目上下文",
            f"- 项目目录：{project_path or '未提供'}",
            "",
            project_summary or "未提供项目扫描摘要。",
            "",
            "## 业务目标",
            *self._render_bullets(business_goals, "待补充业务目标"),
            "",
            "## 功能清单",
            *self._render_bullets(functional_requirements, "待补充功能清单"),
            "",
            "## 用户故事",
            *self._render_bullets(user_stories, "待补充用户故事"),
            "",
            "## 验收标准",
            *self._render_bullets(acceptance_criteria, "待补充验收标准"),
            "",
            "## 非功能需求",
            *self._render_bullets(non_functional_requirements, "暂无额外非功能要求"),
            "",
            "## 开放问题",
            *self._render_bullets(open_questions, "暂无开放问题"),
            "",
            "## 模块划分",
        ]

        if modules:
            for module in modules:
                sections.extend(
                    [
                        f"### {module['module_name']}（{module['priority']}）",
                        module["description"] or "待补充模块描述。",
                        "",
                    ]
                )
        else:
            sections.extend(["- 暂无模块划分", ""])

        sections.extend(
            [
                "```json",
                json.dumps({"modules": modules}, ensure_ascii=False, indent=2),
                "```",
            ]
        )

        return "\n".join(sections).strip()

    def _normalize_string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        normalized: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized

    def _render_bullets(self, items: list[str], fallback: str) -> list[str]:
        if not items:
            return [f"- {fallback}"]
        return [f"- {item}" for item in items]
